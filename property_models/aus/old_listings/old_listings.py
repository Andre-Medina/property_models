import polars as pl
import selenium.webdriver

# from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from property_models.aus.old_listings.constants import OldListingURL  # , RawListing, RawPriceRecord, RawPropertyInfo
from property_models.aus.old_listings.extract import get_page_counts  # extract_listing_data
from property_models.models import Postcode  # , PriceRecord, PropertyInfo


class OldListing:
    """Class to interact with the old listing site."""

    def start() -> WebDriver:
        """Starts sever."""
        driver = selenium.webdriver.Chrome()
        return driver

    @classmethod
    def extract(
        cls,
        *,
        driver: WebDriver,
        state: str,
        suburb: str,
        beds: int,
        baths: int,
        cars: int,
    ) -> tuple[pl.DataFrame, pl.DataFrame]:
        """Extract data from old listings by looping through all related pages."""
        postcode = Postcode.find_postcode(suburb=suburb, country="AUS")

        old_listing_url = OldListingURL(
            state=state,
            suburb=suburb,
            postcode=postcode,
            beds=beds,
            baths=baths,
            cars=cars,
            page=1,
        )

        page_count = get_page_counts(driver=driver, old_listing_url=old_listing_url)

        price_records_list: list[pl.DataFrame] = []
        properties_info_list: list[pl.DataFrame] = []

        for page_number in enumerate(page_count):
            next_page_url = old_listing_url.to_page(page_number)
            driver.get(next_page_url.format())
            properties_info_list, price_records_list = cls.extract_data_from_page(driver, page_url=next_page_url)

    # @classmethod
    # def extract_data_from_page(cls, driver: WebDriver, *, page_url: OldListingURL
    # ) -> tuple[pl.DataFrame, pl.DataFrame]:
    #     """"""

    #     table = driver.find_elements(By.CLASS_NAME, "content-col")[0]

    #     listings = table.find_elements(By.TAG_NAME, "div")

    #     listings_raw: list[RawListing] = []
    #     for listing in listings:
    #         listings_raw.append(extract_listing_data(listing, state=page_url.state, postcode=page_url.postcode))

    #     properties_info: list[PropertyInfo] = []
    #     price_records: list[PriceRecord] = []
    #     for listing_raw in listings_raw:
    #         property_info = listing_raw.extract_property_info()
    #         properties_info.append()
