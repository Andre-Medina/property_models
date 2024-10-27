from property_models.models import Address, HistoricalPrice, PropertyInfo
from property_models.constants import RecordType, PropertyType, PropertyCondition
from datetime import date
import pytest

##### ADDRESSES ###############

@pytest.mark.parametrize(
    "_name, address, country, correct_json",
    [
        (
            "Basic AUS unit 1, ",
            'U2 42-44 Example St, STANMORE, NSW 2048',
            "australia",
            {
                'unit_number': 2,
                'street_number': 42,
                'street_name': 'EXAMPLE STREET',
                'suburb': 'STANMORE',
                'post_code': 2048,
                'state': 'NSW',
                'country': 'australia',
            },
        ),
        (
            "Basic AUS unit 2, ",
            '7/67 ROSEBERRY STREET, ASCOT VALE'+ ", VIC 3032",
            "australia",
            {
                'unit_number': 7,
                'street_number': 67,
                'street_name': 'ROSEBERRY STREET',
                'suburb': 'ASCOT VALE',
                'post_code': 3032,
                'state': 'VIC',
                'country': 'australia'
            },
        ),
        (
            "Basic AUS unit 2, ",
            '80 ROSEBERRY STREET, ASCOT VALE'+ ", VIC 3032",
            "australia",
            {
                'unit_number': None,
                'street_number': 80,
                'street_name': 'ROSEBERRY STREET',
                'suburb': 'ASCOT VALE',
                'post_code': 3032,
                'state': 'VIC',
                'country': 'australia'
            },
        ),
    ]
)
def test_address_parsing(_name, address, country, correct_json):

    address_model = Address.parse(address, country=country)

    for field, value in address_model.model_dump().items():
        assert correct_json[field] == value
        
###### HISTORICAL PRICES ##############

@pytest.mark.parametrize(
    "_name, record_type, address, price",
    [
        ("Basic construction, ", RecordType.AUCTION, ('80 FIFTH STREET, ASCOT VALE, VIC 3032', "australia"), 100000),
        ("Null price, ", RecordType.ENQUIRY, ('80 SAMPLE STREET, ASCOT VALE, VIC 3032', "australia"), None),
        ("string record, ", " NO Sale", ('80 ROSEBERRY STREET, NORTH MELBOURNE, VIC 3032', "australia"), 200000),
    ]
)
def test_historical_price_init(_name, record_type, address, price):

    HistoricalPrice(
        record_type = RecordType.parse(record_type) if isinstance(record_type, str) else record_type,
        address = Address.parse(address[0], country = address[1]),
        price = price,
    )

##### PROPERTY INFO ############

@pytest.mark.parametrize(
    "_name, property_type, address, condition, count, date, size",
    [
        ("Basic construction, ", PropertyType.LAND.NEW_BUILD, ('80 FIFTH ST, ASCOT, VIC 3032', "australia"), None, 2, date(2020, 1, 1), 100),
        ("Null values, ", PropertyType.APARTMENT.SIXTIES_BRICK, ('80 FIFTH ST, ASCOT, VIC 3032', "australia"), None, 4, None, None),
        ("string record, ", PropertyType.TOWN_HOUSE.GENERAL, ('80 ROSEBERRY STREET, NORTH MELBOURNE, VIC 3032', "australia"),  None, None, date(2020, 1, 30), None),
    ]
)
def test_property_type_init(_name, property_type, address, condition, count, date, size):

    PropertyInfo(
    property_type = PropertyType.parse(property_type) if isinstance(property_type, str) else property_type,
    address = Address.parse(address[0], country = address[1]),
    condition = PropertyCondition.parse(condition) if condition is not None and isinstance(condition, str) else condition,
    bed = count,
    car = count,
    bath = count,
    floor_count = count,
    land_size_m2 = size,
    property_size_m2 = size,
    date_of_construction = date,
    )