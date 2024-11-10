import json
import os
from datetime import date

import polars as pl
import polars.testing
import pytest

from property_models.constants import PROPERTIES_INFO_SCHEMA, PropertyCondition, PropertyType, RecordType
from property_models.dev_utils.fixtures import (
    CORRECT_PROPERTY_INFO_JSON,
    CORRECT_RECORDS_COMPRESSED_JSON,
    CORRECT_RECORDS_JSON,
    TEST_ADDRESSES,
    TEST_ADDRESSES_STRING,
    TEST_COUNTRY,
    TEST_POSTCODE,
    TEST_STATE,
    TEST_SUBURB,
)
from property_models.dev_utils.fixtures import (
    TEST_STREET_NAMES as STREET_NAMES,
)
from property_models.dev_utils.fixtures import (
    TEST_STREET_NUMBERS as STREET_NUMS,
)
from property_models.dev_utils.fixtures import (
    TEST_UNIT_NUMBERS as UNIT_NUMS,
)
from property_models.models import (
    Address,
    Postcode,  # Import the Postcode class from your module
    PriceRecord,
    PropertyInfo,
)

#### POSTCODES ##########


def test_find_suburb(mock_postcodes):
    """Test the find_suburb method for a known postcode."""
    suburb = Postcode.find_suburb(postcode=200, country=TEST_COUNTRY)
    assert suburb == "australian_national_university".upper()

    suburb = Postcode.find_suburb(postcode=2540, country=TEST_COUNTRY)
    assert suburb == "jervis_bay".upper()

    suburb = Postcode.find_suburb(postcode=2600, country=TEST_COUNTRY)
    assert suburb == "deakin_west".upper()

    suburb = Postcode.find_suburb(postcode=TEST_POSTCODE, country=TEST_COUNTRY)
    assert suburb == TEST_SUBURB


def test_find_postcode(mock_postcodes):
    """Test the find_postcode method for a known suburb."""
    postcode = Postcode.find_postcode(suburb="australian_national_university", country=TEST_COUNTRY)
    assert postcode == 200

    postcode = Postcode.find_postcode(suburb="jervis_bay ", country=TEST_COUNTRY)
    assert postcode == 2540
    postcode = Postcode.find_postcode(suburb="duntroon", country=TEST_COUNTRY)
    assert postcode == 2600
    postcode = Postcode.find_postcode(suburb="DEAKIN WEST", country=TEST_COUNTRY)
    assert postcode == 2600
    postcode = Postcode.find_postcode(suburb=TEST_SUBURB, country=TEST_COUNTRY)
    assert postcode == TEST_POSTCODE


##### ADDRESSES ###############


@pytest.mark.parametrize(
    "_name, address, country, correct_json",
    [
        (
            "Basic AUS slash unit, ",
            f"{UNIT_NUMS[0]}/{STREET_NUMS[0]} {STREET_NAMES[0]}, {TEST_SUBURB}, {TEST_STATE} {TEST_POSTCODE}",
            TEST_COUNTRY,
            TEST_ADDRESSES[0],
        ),
        (
            "AUS comma unit number, ",
            f"{UNIT_NUMS[0]}, {STREET_NUMS[0]} {STREET_NAMES[0]}, {TEST_SUBURB}, {TEST_STATE} {TEST_POSTCODE}",
            TEST_COUNTRY,
            TEST_ADDRESSES[0],
        ),
        (
            "Basic AUS no unit, ",
            f"{STREET_NUMS[0]} {STREET_NAMES[0]}, {TEST_SUBURB}, {TEST_STATE} {TEST_POSTCODE}",
            TEST_COUNTRY,
            TEST_ADDRESSES[0] | {"unit_number": None},
        ),
        (
            "AUS needs stripping, ",
            f" {UNIT_NUMS[0]}, {STREET_NUMS[0]} {STREET_NAMES[0]}, {TEST_SUBURB}, {TEST_STATE} {TEST_POSTCODE}",
            TEST_COUNTRY,
            TEST_ADDRESSES[0],
        ),
        (
            "AUS Unit prefix, ",
            f"UNIT {UNIT_NUMS[0]}, {STREET_NUMS[0]} {STREET_NAMES[0]}, {TEST_SUBURB}, {TEST_STATE} {TEST_POSTCODE}",
            TEST_COUNTRY,
            TEST_ADDRESSES[0],
        ),
        (
            "AUS U prefix, ",
            f"U{UNIT_NUMS[0]} {STREET_NUMS[0]}-44 {STREET_NAMES[0]}, {TEST_SUBURB}, {TEST_STATE} {TEST_POSTCODE}",
            TEST_COUNTRY,
            TEST_ADDRESSES[0],
        ),
        (
            "AUS G2 unit, ",
            f"G2/{STREET_NUMS[0]}-44 {STREET_NAMES[0]}, {TEST_SUBURB}, {TEST_STATE} {TEST_POSTCODE}",
            TEST_COUNTRY,
            TEST_ADDRESSES[0] | {"unit_number": "G2"},
        ),
        # (
        #     "AUS space between unit and number, ",
        #     f"{UNIT_NUMS[0]} {STREET_NUMS[0]} {STREET_NAMES[0]}, {TEST_SUBURB}, {TEST_STATE} {TEST_POSTCODE}",
        #     TEST_COUNTRY,
        #     TEST_ADDRESSES[0],
        # ),
        (
            "AUS with two units with '&', ",
            f"6000 & {UNIT_NUMS[0]}/{STREET_NUMS[0]} {STREET_NAMES[0]}, {TEST_SUBURB}, {TEST_STATE} {TEST_POSTCODE}",
            TEST_COUNTRY,
            TEST_ADDRESSES[0],
        ),
        (
            "AUS full stop unit number, ",
            f"1.{UNIT_NUMS[0]}, {STREET_NUMS[0]} {STREET_NAMES[0]}, {TEST_SUBURB}, {TEST_STATE} {TEST_POSTCODE}",
            TEST_COUNTRY,
            TEST_ADDRESSES[0] | {"unit_number": f"1{UNIT_NUMS[0]}"},
        ),
    ],
)
def test_address_parsing(_name, address, country, correct_json):
    """Test address parsing works and the correct output is generated."""
    address_model = Address.parse(address, country=country)

    for field, value in address_model.model_dump().items():
        assert correct_json[field] == value


def test_address_parsing_from_dict():
    """Test creating address from string vs dict."""
    address_parsed = Address.parse(TEST_ADDRESSES_STRING[0], country=TEST_COUNTRY)
    address_kwargs = Address(**TEST_ADDRESSES[0])
    assert address_parsed == address_kwargs
    address_parsed = Address.parse(TEST_ADDRESSES_STRING[1], country=TEST_COUNTRY)
    address_kwargs = Address(**TEST_ADDRESSES[1])
    assert address_parsed == address_kwargs
    address_parsed = Address.parse(TEST_ADDRESSES_STRING[2], country=TEST_COUNTRY)
    address_kwargs = Address(**TEST_ADDRESSES[2])
    assert address_parsed == address_kwargs


###### HISTORICAL PRICES ##############


@pytest.mark.parametrize(
    "_name, record_type, address, price, date",
    [
        (
            "Basic construction, ",
            RecordType.AUCTION,
            ("80 FIFTH STREET, ASCOT VALE, VIC 3032", TEST_COUNTRY),
            100000,
            date(2020, 1, 1),
        ),
        (
            "Null price, ",
            RecordType.ENQUIRY,
            ("80 SAMPLE STREET, ASCOT VALE, VIC 3032", TEST_COUNTRY),
            None,
            date(2020, 1, 1),
        ),
        (
            "string record, ",
            " NO Sale",
            ("80 ROSEBERRY STREET, NORTH MELBOURNE, VIC 3032", TEST_COUNTRY),
            200000,
            date(2020, 1, 1),
        ),
    ],
)
def test_price_record_init(_name, record_type, address, price, date):
    """Test HistoricalPrice class can be initialized."""
    PriceRecord(
        record_type=RecordType.parse(record_type) if isinstance(record_type, str) else record_type,
        address=Address.parse(address[0], country=address[1]),
        price=price,
        date=date,
    )


def test_price_record_to_records():
    """Takes a list of historical prices and converts them to a df."""
    price_records = [
        PriceRecord(
            date=date(2020, 1, 1),
            record_type=RecordType.parse(RecordType.AUCTION),
            address=Address.parse("80 FIFTH STREET, ASCOT VALE, VIC 3032", country=TEST_COUNTRY),
            price=100000,
        ),
        PriceRecord(
            date=date(2020, 1, 1),
            record_type=RecordType.parse(RecordType.ENQUIRY),
            address=Address.parse("80 SAMPLE STREET, ASCOT VALE, VIC 3032", country=TEST_COUNTRY),
            price=None,
        ),
        PriceRecord(
            date=date(2020, 1, 1),
            record_type=RecordType.parse(" NO Sale"),
            address=Address.parse("80 ROSEBERRY STREET, NORTH MELBOURNE, VIC 3032", country=TEST_COUNTRY),
            price=200000,
        ),
    ]
    historical_records = PriceRecord.to_dataframe(price_records)
    records_json = {
        "address": {
            "unit_number": [None, None, None],
            "street_number": ["80", "80", "80"],
            "street_name": ["FIFTH STREET", "SAMPLE STREET", "ROSEBERRY STREET"],
            "suburb": ["ASCOT_VALE", "ASCOT_VALE", "NORTH_MELBOURNE"],
            "postcode": 3032,
            "state": "VIC",
            "country": TEST_COUNTRY,
        },
        "date": [date(2020, 1, 1), date(2020, 1, 1), date(2020, 1, 1)],
        "record_type": ["auction", "enquiry", "no_sale"],
        "price": [100000, None, 200000],
    }

    data_json = pl.DataFrame(records_json)

    pl.testing.assert_frame_equal(historical_records, data_json, check_dtypes=False)


def test_price_record_read_csv(mock_price_records):
    """Create csv contents and make sure the read function works."""
    data_csv = PriceRecord._read_csv(mock_price_records)
    data_json = pl.DataFrame(CORRECT_RECORDS_COMPRESSED_JSON)
    pl.testing.assert_frame_equal(data_csv, data_json, check_dtypes=False)


def test_price_record_read(mock_price_records):  # noqa: ARG001
    """Create csv contents and make sure the read function works."""
    data_csv = PriceRecord.read(country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)
    data_json = pl.DataFrame(CORRECT_RECORDS_JSON)
    pl.testing.assert_frame_equal(data_csv, data_json, check_dtypes=False)


def test_price_record_write(mock_price_records):
    """Test writing data writes the correct data."""
    data_csv = PriceRecord.read(country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)
    os.remove(mock_price_records)
    with pytest.raises(FileNotFoundError):
        PriceRecord.read(country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)

    data_csv.pipe(PriceRecord.write, country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)
    data_re_read = PriceRecord.read(country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)

    data_json = pl.DataFrame(CORRECT_RECORDS_JSON)
    pl.testing.assert_frame_equal(data_re_read, data_json, check_dtypes=False)


def test_price_records_to_frame(mock_price_records):  # noqa: ARG001
    """Test converting list of PriceRecord into a frame."""
    price_record_raw = PriceRecord.read(country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)

    price_record_list: list[PriceRecord] = []
    for item in price_record_raw.to_dicts():
        price_record_list.append(PriceRecord(**item))
    price_record_frame = PriceRecord.to_dataframe(price_record_list)

    pl.testing.assert_frame_equal(price_record_raw, price_record_frame)


####### PROPERTY INFO ############


@pytest.mark.parametrize(
    "_name, property_type, address, condition, count, date, size",
    [
        (
            "Basic construction, ",
            PropertyType.LAND.NEW_BUILD,
            ("80 FIFTH ST, ASCOT, VIC 3032", TEST_COUNTRY),
            None,
            2,
            date(2020, 1, 1),
            100,
        ),
        (
            "Null values, ",
            PropertyType.APARTMENT.SIXTIES_BRICK,
            ("80 FIFTH ST, ASCOT, VIC 3032", TEST_COUNTRY),
            None,
            4,
            None,
            None,
        ),
        (
            "string record, ",
            PropertyType.TOWN_HOUSE.GENERAL,
            ("80 ROSEBERRY STREET, NORTH MELBOURNE, VIC 3032", TEST_COUNTRY),
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
        address=Address.parse("80 ROSEBERRY STREET, NORTH MELBOURNE, VIC 3032", country=TEST_COUNTRY),
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
    properties_info_mocked = PropertyInfo.read_json(mock_property_info)
    properties_info_correct = pl.DataFrame(CORRECT_PROPERTY_INFO_JSON)

    pl.testing.assert_frame_equal(
        properties_info_mocked.sort("floors"), properties_info_correct.sort("floors"), check_dtypes=False
    )


def test_properties_info_read(mock_property_info):  # noqa: ARG001
    """Create csv contents and make sure the read function works."""
    properties_info_mocked = PropertyInfo.read(country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)
    properties_info_correct = pl.DataFrame(CORRECT_PROPERTY_INFO_JSON)

    pl.testing.assert_frame_equal(
        properties_info_mocked.sort("floors"), properties_info_correct.sort("floors"), check_dtypes=False
    )


def test_properties_info_write(mock_property_info):
    """Test writing data writes the correct data."""
    properties_info_mocked = PropertyInfo.read(country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)
    os.remove(mock_property_info)
    with pytest.raises(FileNotFoundError):
        PropertyInfo.read(country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)

    properties_info_mocked.pipe(PropertyInfo.write, country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)
    properties_info_re_read = PropertyInfo.read(country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)

    properties_info_correct = pl.DataFrame(CORRECT_PROPERTY_INFO_JSON)
    pl.testing.assert_frame_equal(
        properties_info_re_read.sort("floors"), properties_info_correct.sort("floors"), check_dtypes=False
    )


def test_property_info_to_frame(mock_property_info):  # noqa: ARG001
    """Test converting list of PropertyInfo into a frame."""
    property_info_raw = PropertyInfo.read(country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)

    property_info_list: list[PropertyInfo] = []
    for item in property_info_raw.to_dicts():
        property_info_list.append(PropertyInfo.from_stringified_dict(item))
    property_info_frame = PropertyInfo.to_dataframe(property_info_list)

    pl.testing.assert_frame_equal(property_info_raw, property_info_frame)


def test_property_info_unique(mock_property_info):  # noqa: ARG001
    """Test taking unique property_info works."""
    property_info_raw = PropertyInfo.read(country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)
    duped_address_1 = property_info_raw["address"].item(0)
    duped_address_2 = property_info_raw["address"].item(1)

    first_half_of_duplicated = property_info_raw.filter(pl.col("address") == duped_address_1).with_columns(
        pl.lit(None).alias("beds").cast(PROPERTIES_INFO_SCHEMA["beds"]),
        pl.lit(None).alias("construction_date").cast(PROPERTIES_INFO_SCHEMA["construction_date"]),
        pl.lit(None).alias("floors").cast(PROPERTIES_INFO_SCHEMA["floors"]),
    )
    second_half_of_duplicated = property_info_raw.filter(pl.col("address") == duped_address_1).with_columns(
        pl.lit(None).alias("cars").cast(PROPERTIES_INFO_SCHEMA["cars"]),
        pl.lit(None).alias("property_type").cast(PROPERTIES_INFO_SCHEMA["property_type"]),
        pl.lit(None).alias("condition").cast(PROPERTIES_INFO_SCHEMA["condition"]),
    )

    property_info_with_duplicates = pl.concat(
        [
            first_half_of_duplicated,
            second_half_of_duplicated,
            property_info_raw.filter(pl.col("address") != duped_address_1),
            property_info_raw.filter(pl.col("address") == duped_address_2),
        ]
    )

    property_info_de_dupe = PropertyInfo.unique(property_infos=property_info_with_duplicates)

    pl.testing.assert_frame_equal(property_info_raw.sort("address"), property_info_de_dupe.sort("address"))


##### INTEGRATION #############


def test_address_join_on(mock_property_info, mock_price_records):  # noqa: ARG001
    """Test joining two of the main dataframes together works."""
    properties_info_mocked = PropertyInfo.read(country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)
    price_records_mocked = PriceRecord.read(country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)

    combined_data = Address.join_on(properties_info_mocked, price_records_mocked)

    assert not combined_data.is_empty()
    assert set(combined_data.columns) == set(properties_info_mocked.columns) | set(price_records_mocked.columns)

    pl.testing.assert_frame_equal(
        combined_data.select(properties_info_mocked.columns).sort("floors"),
        properties_info_mocked.sort("floors"),
    )

    pl.testing.assert_frame_equal(
        combined_data.select(price_records_mocked.columns).sort("price"),
        price_records_mocked.sort("price"),
    )


def test_address_filter_on(mock_property_info):  # noqa: ARG001
    """Test you can filter by an address."""
    properties_info = PropertyInfo.read(country=TEST_COUNTRY, state=TEST_STATE, suburb=TEST_SUBURB)
    specific_address = properties_info["address"].item(0)

    properties_info.filter(pl.col("address") == specific_address)
    properties_info.filter(pl.col("address").is_in([specific_address]))
