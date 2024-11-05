from datetime import date

import pytest

from property_models.aus.old_listings.constants import (
    OldListingURL,
    RawListing,
    RawPriceRecord,
    RawPropertyInfo,
)
from property_models.aus.old_listings.parse import parse_date, parse_price, parse_record_type
from property_models.constants import PropertyType, RecordType
from property_models.dev_utils.fixtures import (
    TEST_ADDRESSES,
    TEST_ADDRESSES_STRING,
    TEST_POSTCODE,
    TEST_STATE,
    TEST_SUBURB,
)
from property_models.models import Address, PriceRecord, PropertyInfo


def test_parse_date():
    """Test the parsing function for old listings."""
    assert parse_date("March 2000") == date(2000, 3, 1)
    assert parse_date("July 2019") == date(2019, 7, 1)
    assert parse_date("December 2025") == date(2025, 12, 1)


def test_parse_price():
    """Test the price parsing."""
    assert parse_price("Auction") is None
    assert parse_price("Contact") is None
    assert parse_price("$415,000") == 415000
    assert parse_price("$350 Week") == 350
    assert parse_price("$410,000 Price Guide") == 410000
    assert parse_price("$480,000 - $520,000") == 500000
    assert parse_price("$480,000 - $520,000 Auction") == 500000


def test_parse_record_type():
    """Test the price record type."""
    assert parse_record_type("Auction") == RecordType.AUCTION
    assert parse_record_type("Contact") == RecordType.ENQUIRY
    assert parse_record_type("By Negotiation") == RecordType.PRIVATE_SALE
    assert parse_record_type("$495,000") is None
    assert parse_record_type("$440 Private Sale") == RecordType.PRIVATE_SALE
    assert parse_record_type("$430,000 Private Sale") == RecordType.PRIVATE_SALE
    assert parse_record_type("$440,000 - $480,000") is None
    assert parse_record_type("$320,000 - $350,000 Auction") == RecordType.AUCTION


def test_old_listing_url(mock_postcodes):
    """Test `OldListingURL` works."""
    old_listing_url = OldListingURL(
        state=TEST_STATE,
        suburb=TEST_SUBURB,
        postcode=TEST_POSTCODE,
        page=1,
        beds=1,
        baths=1,
        cars=1,
    )

    with pytest.raises(ValueError):
        OldListingURL(
            state=TEST_STATE,
            suburb=TEST_SUBURB,
            postcode=TEST_POSTCODE + 1,
            page=1,
            beds=1,
            baths=1,
            cars=1,
        )

    old_listing_url.format()

    old_listing_url_2 = old_listing_url.next_page()
    assert old_listing_url_2.page == old_listing_url.page + 1

    different_page = 10
    old_listing_url_2 = old_listing_url.to_page(different_page)
    assert old_listing_url_2.page == different_page


def test_parsing_integration():
    """Test generating old listing data and parsing it."""
    raw_listing = RawListing(
        general_info=RawPropertyInfo(
            address=TEST_ADDRESSES_STRING[0],
            beds="1",
            cars="1",
            baths="1",
            property_type="Unit/apmt",
            land_size_m2=None,
        ),
        recent_price=RawPriceRecord(date=" March 2019", market_info="$380,000"),
        historical_prices=[
            RawPriceRecord(date="March 2019", market_info="$380,000 - $420,000"),
            RawPriceRecord(date="June 2013", market_info="Auction"),
            RawPriceRecord(date="June 2013", market_info="$320,000 - $340,000"),
            RawPriceRecord(date="June 2013", market_info="$320,000 - $340,000 Auction"),
            RawPriceRecord(date="August 2011", market_info="Private Sale"),
        ],
    )

    correct_address = Address(**TEST_ADDRESSES[0])

    correct_property_info = PropertyInfo(
        address=correct_address,
        baths=1,
        beds=1,
        cars=1,
        property_size_m2=None,
        land_size_m2=None,
        condition=None,
        property_type=PropertyType.APARTMENT.GENERAL.value,
        construction_date=None,
        floors=None,
    )

    assert str(raw_listing.to_property_info()) == str(correct_property_info)
    assert raw_listing.to_property_info() == correct_property_info

    correct_price_records = [
        PriceRecord(address=correct_address, date=date(2019, 3, 1), record_type=None, price=380000),
        PriceRecord(address=correct_address, date=date(2019, 3, 1), record_type=None, price=400000),
        PriceRecord(address=correct_address, date=date(2013, 6, 1), record_type=RecordType.AUCTION, price=None),
        PriceRecord(address=correct_address, date=date(2013, 6, 1), record_type=None, price=330000),
        PriceRecord(address=correct_address, date=date(2013, 6, 1), record_type=RecordType.AUCTION, price=330000),
        PriceRecord(address=correct_address, date=date(2011, 8, 1), record_type=RecordType.PRIVATE_SALE, price=None),
    ]

    assert raw_listing.to_price_records() == correct_price_records
