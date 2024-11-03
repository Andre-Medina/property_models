import pytest

from property_models.aus.old_listings.constants import OldListingURL
from property_models.dev_utils.fixtures import (
    TEST_POSTCODE,
    TEST_STATE,
    TEST_SUBURB,
)


def test_old_listing_url(mock_postcodes) -> str:
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
