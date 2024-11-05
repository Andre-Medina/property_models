import polars as pl
import selenium.webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm

from property_models.aus.old_listings.constants import OldListingURL, RawListing
from property_models.aus.old_listings.extract import extract_listing_data, get_page_counts
from property_models.models import Postcode, PriceRecord, PropertyInfo


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
        max_pages: int | None = None,
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
        property_infos_list: list[pl.DataFrame] = []

        for page_number in range(1, page_count + 1):
            if max_pages is not None and page_number > max_pages:
                break

            next_page_url = old_listing_url.to_page(page_number)
            driver.get(next_page_url.format())

            property_infos, price_records = cls.extract_data_from_page(driver, page_url=next_page_url)
            price_records_list.append(price_records)
            property_infos_list.append(property_infos)

        property_infos = pl.concat(property_infos_list)
        price_records = pl.concat(price_records_list)

        return property_infos, price_records

    @classmethod
    def extract_data_from_page(cls, driver: WebDriver, *, page_url: OldListingURL) -> tuple[pl.DataFrame, pl.DataFrame]:
        """Extract data from a single page."""
        table = driver.find_elements(By.CLASS_NAME, "content-col")[0]

        listings = table.find_elements(By.TAG_NAME, "div")

        raw_listings: list[RawListing] = []
        for listing in tqdm(listings, desc="extracting raw listings"):
            raw_listings.append(extract_listing_data(listing, state=page_url.state, postcode=page_url.postcode))

        property_infos: list[PropertyInfo] = []
        price_records: list[PriceRecord] = []
        for raw_listing in tqdm(raw_listings, desc="converting to data"):
            property_info = raw_listing.to_property_info()
            property_infos.append(property_info)

            price_record = raw_listing.to_price_records()
            price_records.extend(price_record)

        print("Converting to frames.")
        property_info_df = PropertyInfo.to_dataframe(property_infos)
        price_records_df = PriceRecord.to_dataframe(price_records)

        return property_info_df, price_records_df
