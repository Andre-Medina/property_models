import os

import pytest

from property_models.constants import (
    DATA_DIR,
    HISTORICAL_RECORDS_CSV_FILE,
    POSTCODE_CSV_FILE,
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
    file_path = HISTORICAL_RECORDS_CSV_FILE.format(
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


def test_property_type_meta():
    """Testing `MetaPropertyType` works as intended."""
    assert PropertyType.APARTMENT.SIXTIES_BRICK.value == ("apartment", "sixties_brick")
    assert PropertyType.APARTMENT.GENERAL.value == ("apartment", None)
    assert PropertyType.FREE_STANDING_HOUSE.MODERN.value == ("free_standing_house", "modern")
    assert PropertyType.LAND.NEW_BUILD.value == ("land", "new_build")
    assert PropertyType.TOWN_HOUSE.VICTORIAN.value == ("town_house", "victorian")
