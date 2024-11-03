import json
from datetime import date

import polars as pl
import polars.testing
import pytest

from property_models.constants import PropertyCondition, PropertyType, RecordType
from property_models.dev_utils.fixtures import CORRECT_PROPERTY_INFO_JSON, CORRECT_RECORDS_JSON
from property_models.models import (
    Address,
    Postcode,  # Import the Postcode class from your module
    PriceRecord,
    PropertyInfo,
)

#### POSTCODES ##########


def test_find_suburb(mock_postcodes):
    """Test the find_suburb method for a known postcode."""
    suburb = Postcode.find_suburb(postcode=200, country="aus")
    assert suburb == "australian_national_university"

    suburb = Postcode.find_suburb(postcode=2540, country="aus")
    assert suburb == "jervis_bay"

    suburb = Postcode.find_suburb(postcode=2600, country="aus")
    assert suburb == "deakin_west"


def test_find_postcode(mock_postcodes):
    """Test the find_postcode method for a known suburb."""
    postcode = Postcode.find_postcode(suburb="australian_national_university", country="aus")
    assert postcode == 200

    postcode = Postcode.find_postcode(suburb="jervis_bay", country="aus")
    assert postcode == 2540
    postcode = Postcode.find_postcode(suburb="duntroon", country="aus")
    assert postcode == 2600
    postcode = Postcode.find_postcode(suburb="deakin_west", country="aus")
    assert postcode == 2600


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
                "postcode": 2048,
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
                "postcode": 3032,
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
                "postcode": 3032,
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
    PriceRecord(
        record_type=RecordType.parse(record_type) if isinstance(record_type, str) else record_type,
        address=Address.parse(address[0], country=address[1]),
        price=price,
        date=date,
    )


def test_historical_price_read_csv(mock_price_records):
    """Create csv contents and make sure the read function works."""
    data_csv = PriceRecord._read_csv(mock_price_records)
    data_json = pl.DataFrame(CORRECT_RECORDS_JSON)
    pl.testing.assert_frame_equal(data_csv, data_json, check_dtypes=False)


def test_historical_price_to_records():
    """Takes a list of historical prices and converts them to a df."""
    historical_prices = [
        PriceRecord(
            date=date(2020, 1, 1),
            record_type=RecordType.parse(RecordType.AUCTION),
            address=Address.parse("80 FIFTH STREET, ASCOT VALE, VIC 3032", country="australia"),
            price=100000,
        ),
        PriceRecord(
            date=date(2020, 1, 1),
            record_type=RecordType.parse(RecordType.ENQUIRY),
            address=Address.parse("80 SAMPLE STREET, ASCOT VALE, VIC 3032", country="australia"),
            price=None,
        ),
        PriceRecord(
            date=date(2020, 1, 1),
            record_type=RecordType.parse(" NO Sale"),
            address=Address.parse("80 ROSEBERRY STREET, NORTH MELBOURNE, VIC 3032", country="australia"),
            price=200000,
        ),
    ]
    historical_records = PriceRecord.to_records(historical_prices)
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


####### PROPERTY INFO ############


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


def test_properties_info_read_csv(mock_property_info):
    """Create csv contents and make sure the read function works."""
    data_read = PropertyInfo.read_json(mock_property_info)
    data_json = pl.DataFrame(CORRECT_PROPERTY_INFO_JSON)

    pl.testing.assert_frame_equal(data_read.sort("floors"), data_json.sort("floors"), check_dtypes=False)
