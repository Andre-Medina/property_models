import os

import pytest
from pydantic import BaseModel, ConfigDict, ValidationError

from property_models.constants import (
    DATA_DIR,
    POSTCODE_CSV_FILE,
    PRICE_RECORDS_CSV_FILE,
    PROPERTIES_INFO_JSON_FILE,
    PropertyType,
    RecordType,
)


def test_data_dir():
    """Assert data dir exists."""
    assert os.path.isdir(DATA_DIR)


def test_postcodes_template_format():
    """Asserts you can format the template correctly."""
    file_path = POSTCODE_CSV_FILE.format(
        country="test_country",
        # state = "test_state",
        # suburb = "test_suburb",
    )
    assert file_path


def test_historical_records_template_format():
    """Asserts you can format template correctly."""
    file_path = PRICE_RECORDS_CSV_FILE.format(
        country="test_country",
        state="test_state",
        suburb="test_suburb",
    )
    assert file_path


def test_properties_info_template_format():
    """Asserts you can format template correctly."""
    file_path = PROPERTIES_INFO_JSON_FILE.format(
        country="test_country",
        state="test_state",
        suburb="test_suburb",
    )
    assert file_path


def test_record_type_clean():
    """Testing `RecordType.clean`."""
    assert RecordType.parse("auction") == RecordType.AUCTION
    assert RecordType.parse("  auction") == RecordType.AUCTION
    assert RecordType.parse("  AuctION ") == RecordType.AUCTION
    assert RecordType.parse("  pRIVate SALE ") == RecordType.PRIVATE_SALE

    assert RecordType.parse("AUUUUUCTION", errors="null") is None

    with pytest.raises(ValueError):
        RecordType.parse("AUUUUUCTION", errors="raise")

    with pytest.raises(NotImplementedError):
        RecordType.parse("AUUUUUCTION", errors="coerce")


#### PROPERTY TYPE ######


def test_property_type_sub():
    """Testing `SubPropertyType` works as intended."""
    assert PropertyType.APARTMENT.SIXTIES_BRICK.value == ("apartment", "sixties_brick")
    assert PropertyType.APARTMENT.GENERAL.value == ("apartment", None)
    assert PropertyType.FREE_STANDING_HOUSE.MODERN.value == ("free_standing_house", "modern")
    assert PropertyType.LAND.NEW_BUILD.value == ("land", "new_build")
    assert PropertyType.TOWN_HOUSE.VICTORIAN.value == ("town_house", "victorian")


def test_property_type_validation():
    """Test the validation of PropertyType works."""
    PropertyType(("apartment", "sixties_brick"))
    PropertyType(("apartment", None))

    with pytest.raises(KeyError):
        PropertyType(("a", "sixties_brick"))
    with pytest.raises(ValueError):
        PropertyType(("apartment", "this is nothing"))


def test_property_type_sub_class_class():
    """Test the class of property type sub classes."""
    assert type(PropertyType.APARTMENT.SIXTIES_BRICK.value) is PropertyType


def test_property_type_pydantic():
    """Test PropertyType can be used as a pydantic model."""

    class TestModel(BaseModel):
        """Model to hold the general information about a property."""

        property_type: PropertyType

        model_config = ConfigDict({"arbitrary_types_allowed": True})

    TestModel(property_type=PropertyType.APARTMENT.SIXTIES_BRICK.value)
    TestModel(property_type=PropertyType.LAND.NEW_BUILD.value)
    TestModel(property_type=PropertyType.LAND.GENERAL.value)

    TestModel(property_type=PropertyType(("land", "new_build")))
    with pytest.raises(ValidationError):
        TestModel(property_type=("land", "new_build"))


def test_property_type_unique():
    """Test `PropertyType.unique` works as expected."""
    assert (
        PropertyType.unique([PropertyType.APARTMENT.SIXTIES_BRICK.value, PropertyType.APARTMENT.SIXTIES_BRICK.value])
        == PropertyType.APARTMENT.SIXTIES_BRICK.value
    )

    assert (
        PropertyType.unique([PropertyType.APARTMENT.SIXTIES_BRICK.value, None])
        == PropertyType.APARTMENT.SIXTIES_BRICK.value
    )

    assert PropertyType.unique([None, None]) is None


def test_property_type_pase_tuples():
    """Test `PropertyType.parse` works as expected on objects."""
    assert PropertyType.parse(PropertyType.APARTMENT.GENERAL) == PropertyType.APARTMENT.GENERAL.value
    assert PropertyType.parse(PropertyType.APARTMENT.GENERAL.value) == PropertyType.APARTMENT.GENERAL.value
    assert PropertyType.parse(("land", "new_build")) == PropertyType.LAND.NEW_BUILD.value
    assert PropertyType.parse(["land", "new_build"]) == PropertyType.LAND.NEW_BUILD.value
    # assert PropertyType.parse('["land", "new_build"]') == PropertyType.LAND.NEW_BUILD.value


def test_property_type_pase_strings():
    """Test `PropertyType.parse` works as expected on strings."""
    assert PropertyType.parse("unit/apmt") == PropertyType.APARTMENT.GENERAL.value
    assert PropertyType.parse("apartment") == PropertyType.APARTMENT.GENERAL.value
    assert PropertyType.parse("townhouse") == PropertyType.TOWN_HOUSE.GENERAL.value
    assert PropertyType.parse("TOWNHOUSE") == PropertyType.TOWN_HOUSE.GENERAL.value
    assert PropertyType.parse("LAND ") == PropertyType.LAND.GENERAL.value
    assert PropertyType.parse("house") == PropertyType.FREE_STANDING_HOUSE.GENERAL.value
    assert PropertyType.parse("   HouSE ") == PropertyType.FREE_STANDING_HOUSE.GENERAL.value
    assert PropertyType.parse("sales_residential") is None
    assert PropertyType.parse("Sales Residential") is None
    assert PropertyType.parse("residential_sale") is None
    assert PropertyType.parse(None) is None
