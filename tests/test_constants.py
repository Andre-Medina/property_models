import pytest
from property_models.constants import PropertyType, RecordType


def test_record_type_clean():
    """Testing `RecordType.clean`."""

    assert RecordType.parse("auction") == RecordType.AUCTION
    assert RecordType.parse("  auction") == RecordType.AUCTION
    assert RecordType.parse("  AuctION ") == RecordType.AUCTION
    assert RecordType.parse("  pRIVate SALE ") == RecordType.PRIVATE_SALE

    assert RecordType.parse("AUUUUUCTION", errors= "null")  == None
    
    with pytest.raises(ValueError):
        RecordType.parse("AUUUUUCTION", errors= "raise")

    with pytest.raises(NotImplementedError):
        RecordType.parse("AUUUUUCTION", errors= "coerce")



def test_property_type_meta():
    """Testing `MetaPropertyType` works as intended."""

    assert PropertyType.APARTMENT.SIXTIES_BRICK.value == ("apartment", "sixties_brick")
    assert PropertyType.APARTMENT.GENERAL.value == ("apartment", None)
    assert PropertyType.FREE_STANDING_HOUSE.MODERN.value == ("free_standing_house", "modern")
    assert PropertyType.LAND.NEW_BUILD.value == ("land", "new_build")
    assert PropertyType.TOWN_HOUSE.VICTORIAN.value == ("town_house", "victorian")