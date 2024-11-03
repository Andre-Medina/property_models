import os
import tempfile
from datetime import date

import pytest

from property_models import constants

####### POST CODE MOCKING

MOCK_POSTCODE_CSV_DATA = """postcode,suburb
200,australian_national_university
2540,jervis_bay
2600,deakin_west
2600,duntroon
"""


@pytest.fixture(scope="function")
def mock_postcodes():
    """Create a temporary file with the mock CSV data."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="_aus.csv") as temp_file:
        temp_file.write(MOCK_POSTCODE_CSV_DATA)
        temp_file_path = temp_file.name
        temp_file_format = temp_file_path.split("_aus")[0] + "_{country}.csv"

    original_template = constants.POSTCODE_CSV_FILE
    constants.POSTCODE_CSV_FILE = temp_file_format

    yield temp_file_path

    constants.POSTCODE_CSV_FILE = original_template
    os.remove(temp_file_path)


###### PRICE RECORDS MOCKING ########

MOCK_RECORDS_CSV_DATA = """
unit_number,street_number,street_name,date,record_type,price
,1,STEELE STREET,2020-01-01,auction,1000000
10,31,LONG ROAD,2020-10-01,no_sale,500000
,31,BROAD WAY,2025-12-01,private_sale,5000000
,,,,,
"""
CORRECT_RECORDS_JSON = {
    "unit_number": [None, 10, None, None],
    "street_number": [1, 31, 31, None],
    "street_name": ["STEELE STREET", "LONG ROAD", "BROAD WAY", None],
    "date": [date(2020, 1, 1), date(2020, 10, 1), date(2025, 12, 1), None],
    "record_type": ["auction", "no_sale", "private_sale", None],
    "price": [1000000, 500000, 5000000, None],
}


@pytest.fixture(scope="function")
def mock_price_records():
    """Create a temporary file with the mock CSV data."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="_aus_vic_suburb.csv") as temp_file:
        temp_file.write(MOCK_RECORDS_CSV_DATA)
        temp_file_path = temp_file.name
        temp_file_format = temp_file_path.split("_aus")[0] + "_{country}_{state}_{suburb}.csv"

    original_template = constants.PRICE_RECORDS_CSV_FILE
    constants.PRICE_RECORDS_CSV_FILE = temp_file_format

    yield temp_file_path

    constants.PRICE_RECORDS_CSV_FILE = original_template
    os.remove(temp_file_path)


######## PROPERTY INFO MOCKING ###########

MOCK_PROPERTY_INFO_JSON_DATA = """[
{"address": {"unit_number": null, "street_number": 80, "street_name": "ROSEBERRY STREET",
"suburb": "NORTH MELBOURNE", "postcode": 3032, "state": "VIC", "country": "australia"},
"beds": 10, "baths": 10, "cars": 10, "property_size_m2": 304.4, "land_size_m2": 100.3,
"condition": null, "property_type": ["apartment", "sixties_brick"],
"construction_date": "2000-01-01", "floors": 10},
{"address": {"unit_number": 22, "street_number": 42, "street_name": "FDF STREET",
"suburb": "WEST MELBOURNE", "postcode": 3032, "state": "VIC", "country": "australia"},
"beds": 10, "baths": 10, "cars": 10, "property_size_m2": 304.4, "land_size_m2": 100.3,
"condition": null, "property_type": ["apartment", "sixties_brick"],
"construction_date": "2000-01-01", "floors": 1000},
{"address": {"unit_number": null, "street_number": 80, "street_name": "ROSEBERRY STREET",
"suburb": "NORTH MELBOURNE", "postcode": 3032, "state": "VIC", "country": "australia"},
"beds": 10, "baths": 10, "cars": 10, "property_size_m2": 304.4, "land_size_m2": 100.3,
"condition": null, "property_type": ["apartment", "None"],
"construction_date": null, "floors": 100}
]"""
CORRECT_PROPERTY_INFO_JSON = {
    "address": [
        {
            "unit_number": None,
            "street_number": 80,
            "street_name": "ROSEBERRY STREET",
            "suburb": "NORTH MELBOURNE",
            "postcode": 3032,
            "state": "VIC",
            "country": "australia",
        },
        {
            "unit_number": 22,
            "street_number": 42,
            "street_name": "FDF STREET",
            "suburb": "WEST MELBOURNE",
            "postcode": 3032,
            "state": "VIC",
            "country": "australia",
        },
        {
            "unit_number": None,
            "street_number": 80,
            "street_name": "ROSEBERRY STREET",
            "suburb": "NORTH MELBOURNE",
            "postcode": 3032,
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


@pytest.fixture(scope="function")
def mock_property_info():
    """Create a temporary file with the mock CSV data."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="_aus_vic_suburb.csv") as temp_file:
        temp_file.write(MOCK_PROPERTY_INFO_JSON_DATA)
        temp_file_path = temp_file.name
        temp_file_format = temp_file_path.split("_aus")[0] + "_{country}_{state}_{suburb}.csv"

    original_template = constants.PROPERTIES_INFO_JSON_FILE
    constants.PROPERTIES_INFO_JSON_FILE = temp_file_format
    yield temp_file_path
    constants.PROPERTIES_INFO_JSON_FILE = original_template
    os.remove(temp_file_path)
