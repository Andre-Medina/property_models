import json
import tempfile
from datetime import date

import polars as pl
import polars.testing
import pytest

from property_models.constants import PropertyCondition, PropertyType, RecordType
from property_models.models import Address, HistoricalPrice, PropertyInfo

##### ADDRESSES ###############


@pytest.mark.parametrize(
    "_name, address, country, correct_json",
    [
        (
            "Basic AUS unit 1, ",
            "U2 42-44 Example St, STANMORE, NSW 2048",
            "australia",
            {
                "unit_number": 2,
                "street_number": 42,
                "street_name": "EXAMPLE STREET",
                "suburb": "STANMORE",
                "post_code": 2048,
                "state": "NSW",
                "country": "australia",
            },
        ),
        (
            "Basic AUS unit 2, ",
            "7/67 ROSEBERRY STREET, ASCOT VALE" + ", VIC 3032",
            "australia",
            {
                "unit_number": 7,
                "street_number": 67,
                "street_name": "ROSEBERRY STREET",
                "suburb": "ASCOT VALE",
                "post_code": 3032,
                "state": "VIC",
                "country": "australia",
            },
        ),
        (
            "Basic AUS unit 2, ",
            "80 ROSEBERRY STREET, ASCOT VALE" + ", VIC 3032",
            "australia",
            {
                "unit_number": None,
                "street_number": 80,
                "street_name": "ROSEBERRY STREET",
                "suburb": "ASCOT VALE",
                "post_code": 3032,
                "state": "VIC",
                "country": "australia",
            },
        ),
    ],
)
def test_address_parsing(_name, address, country, correct_json):
    """Test address parsing works and the correct output is generated."""
    address_model = Address.parse(address, country=country)

    for field, value in address_model.model_dump().items():
        assert correct_json[field] == value


###### HISTORICAL PRICES ##############


@pytest.mark.parametrize(
    "_name, record_type, address, price, date",
    [
        (
            "Basic construction, ",
            RecordType.AUCTION,
            ("80 FIFTH STREET, ASCOT VALE, VIC 3032", "australia"),
            100000,
            date(2020, 1, 1),
        ),
        (
            "Null price, ",
            RecordType.ENQUIRY,
            ("80 SAMPLE STREET, ASCOT VALE, VIC 3032", "australia"),
            None,
            date(2020, 1, 1),
        ),
        (
            "string record, ",
            " NO Sale",
            ("80 ROSEBERRY STREET, NORTH MELBOURNE, VIC 3032", "australia"),
            200000,
            date(2020, 1, 1),
        ),
    ],
)
def test_historical_price_init(_name, record_type, address, price, date):
    """Test HistoricalPrice class can be initialized."""
    HistoricalPrice(
        record_type=RecordType.parse(record_type) if isinstance(record_type, str) else record_type,
        address=Address.parse(address[0], country=address[1]),
        price=price,
        date=date,
    )


def test_historical_price_read_csv():
    """Create csv contents and make sure the read function works."""
    records_csv = b"""\
    unit_number,street_number,street_name,date,record_type,price
    ,1,STEELE STREET,2020-01-01,auction,1000000
    10,31,LONG ROAD,2020-10-01,no_sale,500000
    ,31,BROAD WAY,2025-12-01,private_sale,5000000
    """

    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        temp_file.write(records_csv)
        temp_file.seek(0)
        data_csv = HistoricalPrice.read_csv(records_csv)

    records_json = {
        "unit_number": [None, 10, None, None],
        "street_number": [1, 31, 31, None],
        "street_name": ["STEELE STREET", "LONG ROAD", "BROAD WAY", None],
        "date": [date(2020, 1, 1), date(2020, 10, 1), date(2025, 12, 1), None],
        "record_type": ["auction", "no_sale", "private_sale", None],
        "price": [1000000, 500000, 5000000, None],
    }
    data_json = pl.DataFrame(records_json)

    pl.testing.assert_frame_equal(data_csv, data_json, check_dtypes=False)


def test_historical_price_to_records():
    """Takes a list of historical prices and converts them to a df."""
    historical_prices = [
        HistoricalPrice(
            date=date(2020, 1, 1),
            record_type=RecordType.parse(RecordType.AUCTION),
            address=Address.parse("80 FIFTH STREET, ASCOT VALE, VIC 3032", country="australia"),
            price=100000,
        ),
        HistoricalPrice(
            date=date(2020, 1, 1),
            record_type=RecordType.parse(RecordType.ENQUIRY),
            address=Address.parse("80 SAMPLE STREET, ASCOT VALE, VIC 3032", country="australia"),
            price=None,
        ),
        HistoricalPrice(
            date=date(2020, 1, 1),
            record_type=RecordType.parse(" NO Sale"),
            address=Address.parse("80 ROSEBERRY STREET, NORTH MELBOURNE, VIC 3032", country="australia"),
            price=200000,
        ),
    ]
    historical_records = HistoricalPrice.to_records(historical_prices)
    records_json = {
        "unit_number": [None, None, None],
        "street_number": [80, 80, 80],
        "street_name": ["FIFTH STREET", "SAMPLE STREET", "ROSEBERRY STREET"],
        "date": [date(2020, 1, 1), date(2020, 1, 1), date(2020, 1, 1)],
        "record_type": ["auction", "enquiry", "no_sale"],
        "price": [100000, None, 200000],
    }

    data_json = pl.DataFrame(records_json)

    pl.testing.assert_frame_equal(historical_records, data_json, check_dtypes=False)


##### PROPERTY INFO ############


@pytest.mark.parametrize(
    "_name, property_type, address, condition, count, date, size",
    [
        (
            "Basic construction, ",
            PropertyType.LAND.NEW_BUILD,
            ("80 FIFTH ST, ASCOT, VIC 3032", "australia"),
            None,
            2,
            date(2020, 1, 1),
            100,
        ),
        (
            "Null values, ",
            PropertyType.APARTMENT.SIXTIES_BRICK,
            ("80 FIFTH ST, ASCOT, VIC 3032", "australia"),
            None,
            4,
            None,
            None,
        ),
        (
            "string record, ",
            PropertyType.TOWN_HOUSE.GENERAL,
            ("80 ROSEBERRY STREET, NORTH MELBOURNE, VIC 3032", "australia"),
            None,
            None,
            date(2020, 1, 30),
            None,
        ),
    ],
)
def test_property_type_init(_name, property_type, address, condition, count, date, size):
    """Test PropertyInfo class can be initialized."""
    PropertyInfo(
        property_type=PropertyType.parse(property_type) if isinstance(property_type, str) else property_type,
        address=Address.parse(address[0], country=address[1]),
        condition=PropertyCondition.parse(condition)
        if condition is not None and isinstance(condition, str)
        else condition,
        beds=count,
        cars=count,
        baths=count,
        floors=count,
        land_size_m2=size,
        property_size_m2=size,
        construction_date=date,
    )


def test_property_type_from_stringified_dict():
    """Test `from_stringified_dict` method."""
    property_info_original = PropertyInfo(
        property_type=PropertyType.parse(PropertyType.APARTMENT.SIXTIES_BRICK),
        address=Address.parse("80 ROSEBERRY STREET, NORTH MELBOURNE, VIC 3032", country="australia"),
        condition=None,
        beds=10,
        cars=10,
        baths=10,
        floors=10,
        land_size_m2=100.3,
        property_size_m2=304.4,
        construction_date=date(2000, 1, 1),
    )

    # Simulate dumping contents to text file
    data_json = property_info_original.model_dump()
    data_string = json.dumps(data_json, default=str)

    # Read data normally
    data_loaded = json.loads(data_string)
    property_info_reloaded = PropertyInfo.from_stringified_dict(data_loaded)
    assert property_info_original == property_info_reloaded

    # Read bad data
    data_loaded = json.loads(data_string)
    bad_property_info_reloaded = PropertyInfo.from_stringified_dict(data_loaded | {"beds": None})
    assert property_info_original != bad_property_info_reloaded


def test_properties_info_read_csv():
    """Create csv contents and make sure the read function works."""
    # noqa: E501
    properties_info_json_file = b"""[
    {"address": {"unit_number": null, "street_number": 80, "street_name": "ROSEBERRY STREET",
    "suburb": "NORTH MELBOURNE", "post_code": 3032, "state": "VIC", "country": "australia"},
    "beds": 10, "baths": 10, "cars": 10, "property_size_m2": 304.4, "land_size_m2": 100.3,
    "condition": null, "property_type": ["apartment", "sixties_brick"],
    "construction_date": "2000-01-01", "floors": 10},
    {"address": {"unit_number": 22, "street_number": 42, "street_name": "FDF STREET",
    "suburb": "WEST MELBOURNE", "post_code": 3032, "state": "VIC", "country": "australia"},
    "beds": 10, "baths": 10, "cars": 10, "property_size_m2": 304.4, "land_size_m2": 100.3,
    "condition": null, "property_type": ["apartment", "sixties_brick"],
    "construction_date": "2000-01-01", "floors": 1000},
    {"address": {"unit_number": null, "street_number": 80, "street_name": "ROSEBERRY STREET",
    "suburb": "NORTH MELBOURNE", "post_code": 3032, "state": "VIC", "country": "australia"},
    "beds": 10, "baths": 10, "cars": 10, "property_size_m2": 304.4, "land_size_m2": 100.3,
    "condition": null, "property_type": ["apartment", "None"],
    "construction_date": null, "floors": 100}
    ]"""

    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        temp_file.write(properties_info_json_file)
        temp_file.seek(0)
        data_read = PropertyInfo.read_json(temp_file)

    properties_info_json = {
        "address": [
            {
                "unit_number": None,
                "street_number": 80,
                "street_name": "ROSEBERRY STREET",
                "suburb": "NORTH MELBOURNE",
                "post_code": 3032,
                "state": "VIC",
                "country": "australia",
            },
            {
                "unit_number": 22,
                "street_number": 42,
                "street_name": "FDF STREET",
                "suburb": "WEST MELBOURNE",
                "post_code": 3032,
                "state": "VIC",
                "country": "australia",
            },
            {
                "unit_number": None,
                "street_number": 80,
                "street_name": "ROSEBERRY STREET",
                "suburb": "NORTH MELBOURNE",
                "post_code": 3032,
                "state": "VIC",
                "country": "australia",
            },
        ],
        "beds": [10, 10, 10],
        "baths": [10, 10, 10],
        "cars": [10, 10, 10],
        "property_size_m2": [304.3999938964844, 304.3999938964844, 304.3999938964844],
        "land_size_m2": [100.30000305175781, 100.30000305175781, 100.30000305175781],
        "condition": [None, None, None],
        "property_type": [["apartment", "sixties_brick"], ["apartment", "sixties_brick"], ["apartment", "None"]],
        "construction_date": [date(2000, 1, 1), date(2000, 1, 1), None],
        "floors": [10, None, 100],
    }
    data_json = pl.DataFrame(properties_info_json)

    pl.testing.assert_frame_equal(data_read.sort("floors"), data_json.sort("floors"), check_dtypes=False)
