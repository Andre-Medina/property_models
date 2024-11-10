import os
import tempfile
from datetime import date

import pytest

from property_models import constants

TEST_SUBURB = "MY_SUBURB"
TEST_POSTCODE = 3000
TEST_COUNTRY = "AUS"
TEST_STATE = "VIC"

TEST_STREET_NAMES = ["MY STREET", "YOUR ROAD", "THEIR BOULEVARD"]
TEST_UNIT_NUMBERS = ["10", None, "300"]
TEST_STREET_NUMBERS = ["10", "300", "1"]

TEST_ADDRESSES_STRING = [
    f"{TEST_UNIT_NUMBERS[0]}/{TEST_STREET_NUMBERS[0]} {TEST_STREET_NAMES[0]}, "
    f"{TEST_SUBURB}, {TEST_STATE} {TEST_POSTCODE}",
    f"{TEST_UNIT_NUMBERS[1]}/{TEST_STREET_NUMBERS[1]} {TEST_STREET_NAMES[1]}, "
    f"{TEST_SUBURB}, {TEST_STATE} {TEST_POSTCODE}",
    f"{TEST_UNIT_NUMBERS[2]}/{TEST_STREET_NUMBERS[2]} {TEST_STREET_NAMES[2]}, "
    f"{TEST_SUBURB}, {TEST_STATE} {TEST_POSTCODE}",
]
TEST_ADDRESSES = [
    {
        "unit_number": TEST_UNIT_NUMBERS[0],
        "street_number": TEST_STREET_NUMBERS[0],
        "street_name": TEST_STREET_NAMES[0],
        "suburb": TEST_SUBURB,
        "postcode": TEST_POSTCODE,
        "state": TEST_STATE,
        "country": TEST_COUNTRY,
    },
    {
        "unit_number": TEST_UNIT_NUMBERS[1],
        "street_number": TEST_STREET_NUMBERS[1],
        "street_name": TEST_STREET_NAMES[1],
        "suburb": TEST_SUBURB,
        "postcode": TEST_POSTCODE,
        "state": TEST_STATE,
        "country": TEST_COUNTRY,
    },
    {
        "unit_number": TEST_UNIT_NUMBERS[2],
        "street_number": TEST_STREET_NUMBERS[2],
        "street_name": TEST_STREET_NAMES[2],
        "suburb": TEST_SUBURB,
        "postcode": TEST_POSTCODE,
        "state": TEST_STATE,
        "country": TEST_COUNTRY,
    },
]

####### POST CODE MOCKING

MOCK_POSTCODE_CSV_DATA = f"""postcode,suburb
200,australian_national_university
2540,jervis_bay
2600,deakin_west
2600,duntroon
{TEST_POSTCODE},{TEST_SUBURB}
"""


@pytest.fixture(scope="function")
def mock_postcodes():
    """Create a temporary file with the mock CSV data."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=f"_{TEST_COUNTRY}.csv") as temp_file:
        temp_file.write(MOCK_POSTCODE_CSV_DATA)
        temp_file_path = temp_file.name
        temp_file_format = temp_file_path.split(f"_{TEST_COUNTRY}")[0] + "_{country}.csv"

    original_template = constants.POSTCODE_CSV_FILE
    constants.POSTCODE_CSV_FILE = temp_file_format

    yield temp_file_path

    constants.POSTCODE_CSV_FILE = original_template
    os.remove(temp_file_path)


###### PRICE RECORDS MOCKING ########

MOCK_RECORDS_CSV_DATA = f"""
unit_number,street_number,street_name,date,record_type,price
{TEST_UNIT_NUMBERS[0] or ""},{TEST_STREET_NUMBERS[0] or ""},{TEST_STREET_NAMES[0] or ""},2020-01-01,auction,1000000
{TEST_UNIT_NUMBERS[1] or ""},{TEST_STREET_NUMBERS[1] or ""},{TEST_STREET_NAMES[1] or ""},2020-10-01,no_sale,500000
{TEST_UNIT_NUMBERS[2] or ""},{TEST_STREET_NUMBERS[2] or ""},{TEST_STREET_NAMES[2] or ""},2025-12-01,private_sale,5000000
"""

CORRECT_RECORDS_JSON = {
    "address": TEST_ADDRESSES,
    "date": [date(2020, 1, 1), date(2020, 10, 1), date(2025, 12, 1)],
    "record_type": ["auction", "no_sale", "private_sale"],
    "price": [1000000, 500000, 5000000],
}

CORRECT_RECORDS_COMPRESSED_JSON = {
    "unit_number": [TEST_UNIT_NUMBERS[0], TEST_UNIT_NUMBERS[1], TEST_UNIT_NUMBERS[2]],
    "street_number": [TEST_STREET_NUMBERS[0], TEST_STREET_NUMBERS[1], TEST_STREET_NUMBERS[2]],
    "street_name": [TEST_STREET_NAMES[0], TEST_STREET_NAMES[1], TEST_STREET_NAMES[2]],
    "date": CORRECT_RECORDS_JSON["date"],
    "record_type": CORRECT_RECORDS_JSON["record_type"],
    "price": CORRECT_RECORDS_JSON["price"],
}


@pytest.fixture(scope="function")
def mock_price_records(mock_postcodes):  # noqa: ARG001
    """Create a temporary file with the mock CSV data."""
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=f"_{TEST_COUNTRY}_{TEST_STATE}_{TEST_SUBURB}.csv"
    ) as temp_file:
        temp_file.write(MOCK_RECORDS_CSV_DATA)
        temp_file_path = temp_file.name
        temp_file_format = temp_file_path.split(f"_{TEST_COUNTRY}")[0] + "_{country}_{state}_{suburb}.csv"

    original_template = constants.PRICE_RECORDS_CSV_FILE
    constants.PRICE_RECORDS_CSV_FILE = temp_file_format

    yield temp_file_path

    constants.PRICE_RECORDS_CSV_FILE = original_template
    os.remove(temp_file_path)


######## PROPERTY INFO MOCKING ###########

MOCK_PROPERTY_INFO_JSON_DATA = f"""[
{{"address": {{"unit_number": {TEST_UNIT_NUMBERS[0] or "null"}, "street_number": {TEST_STREET_NUMBERS[0] or "null"},
"street_name": "{TEST_STREET_NAMES[0]}",
"suburb": "{TEST_SUBURB}", "postcode": {TEST_POSTCODE}, "state": "{TEST_STATE}", "country": "{TEST_COUNTRY}"}},
"beds": 10, "baths": 10, "cars": 10, "property_size_m2": 304.4, "land_size_m2": 100.3,
"condition": null, "property_type": ["apartment", "sixties_brick"],
"construction_date": "2000-01-01", "floors": 10}},
{{"address": {{"unit_number": {TEST_UNIT_NUMBERS[1] or "null"}, "street_number": {TEST_STREET_NUMBERS[1] or "null"},
"street_name": "{TEST_STREET_NAMES[1]}",
"suburb": "{TEST_SUBURB}", "postcode": {TEST_POSTCODE}, "state": "{TEST_STATE}", "country": "{TEST_COUNTRY}"}},
"beds": 10, "baths": 10, "cars": 10, "property_size_m2": 304.4, "land_size_m2": 100.3,
"condition": null, "property_type": ["apartment", "sixties_brick"],
"construction_date": "2000-01-01", "floors": 1000}},
{{"address": {{"unit_number": {TEST_UNIT_NUMBERS[2] or "null"}, "street_number": {TEST_STREET_NUMBERS[2] or "null"},
"street_name": "{TEST_STREET_NAMES[2]}",
"suburb": "{TEST_SUBURB}", "postcode": {TEST_POSTCODE}, "state": "{TEST_STATE}", "country": "{TEST_COUNTRY}"}},
"beds": 10, "baths": 10, "cars": 10, "property_size_m2": 304.4, "land_size_m2": 100.3,
"condition": null, "property_type": ["apartment", "None"],
"construction_date": null, "floors": 100}}
]"""
CORRECT_PROPERTY_INFO_JSON = {
    "address": TEST_ADDRESSES,
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


@pytest.fixture(scope="function")
def mock_property_info(mock_postcodes):  # noqa: ARG001
    """Create a temporary file with the mock CSV data."""
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=f"_{TEST_COUNTRY}_{TEST_STATE}_{TEST_SUBURB}.csv"
    ) as temp_file:
        temp_file.write(MOCK_PROPERTY_INFO_JSON_DATA)
        temp_file_path = temp_file.name
        temp_file_format = temp_file_path.split(f"_{TEST_COUNTRY}")[0] + "_{country}_{state}_{suburb}.csv"

    original_template = constants.PROPERTIES_INFO_JSON_FILE
    constants.PROPERTIES_INFO_JSON_FILE = temp_file_format
    yield temp_file_path
    constants.PROPERTIES_INFO_JSON_FILE = original_template
    os.remove(temp_file_path)
