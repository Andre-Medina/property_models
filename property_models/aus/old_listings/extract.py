# import polars as pl
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from property_models.aus.old_listings.constants import OldListingURL, RawListing, RawPriceRecord, RawPropertyInfo
from property_models.utils import return_if_no_element

#### GENERAL DATA ##########


def get_page_counts(
    *,
    driver: WebDriver,
    old_listing_url: OldListingURL,
) -> int:
    """Get total page count."""
    page_url_formatted = old_listing_url.format()
    driver.get(page_url_formatted)

    page_navigation = driver.find_element(By.CLASS_NAME, "pagination")
    last_navigation = page_navigation.find_elements(By.TAG_NAME, "li")[-2]
    page_count = int(last_navigation.text)

    return page_count


##### EXTRACT DATA #########


def extract_listing_data(listing: WebElement, state: str, postcode: int) -> RawListing:
    """Extracts raw information from a single listing for old_listings."""
    address = ""
    try:
        information_list = listing.find_element(By.TAG_NAME, "section").find_elements(By.TAG_NAME, "section")

        general_info = extract_listing_general(information_list[0], state=state, postcode=postcode)
        recent_price = extract_listing_prices(information_list[1])
        historical_prices = extract_listing_historical(information_list[2])

        extracted_data = RawListing(
            general_info=general_info,
            recent_price=recent_price,
            historical_prices=historical_prices,
        )
        return extracted_data

    except:  # noqa: E722
        # TODO: deal with exceptions
        print(address, "FAILED")
        general_info = extract_listing_general(information_list[0], state=state, postcode=postcode)
        recent_price = extract_listing_prices(information_list[1])
        historical_prices = extract_listing_historical(information_list[2])


def extract_listing_prices(information: WebElement) -> RawPriceRecord:
    """Extract recent prices."""
    date = information.find_element(By.TAG_NAME, "span").text.split(":")[-1]
    market_info = return_if_no_element(
        lambda: information.find_element(By.TAG_NAME, "h3").text.split(" ")[0], default_value="Expressions of Interest"
    )

    raw_price_record = RawPriceRecord(date=date, market_info=market_info)

    return raw_price_record


def extract_listing_general(information: WebElement, state: str, postcode: int) -> RawPropertyInfo:
    """Extract general information."""
    address = return_if_no_element(lambda: f"{information.find_element(By.TAG_NAME, "h2").text}, {state} {postcode}")
    beds = return_if_no_element(lambda: information.find_element(By.CLASS_NAME, "bed").text)
    baths = return_if_no_element(lambda: information.find_element(By.CLASS_NAME, "bath").text)
    cars = return_if_no_element(lambda: information.find_element(By.CLASS_NAME, "car").text)
    land_size_m2 = return_if_no_element(lambda: information.find_element(By.CLASS_NAME, "land").text)

    property_type = return_if_no_element(lambda: information.find_element(By.CLASS_NAME, "type").text)

    raw_property_info = RawPropertyInfo(
        address=address,
        beds=beds,
        baths=baths,
        cars=cars,
        property_type=property_type,
        land_size_m2=land_size_m2,
    )

    return raw_property_info


def extract_listing_historical(information: WebElement) -> list[RawPriceRecord]:
    """Extract historical prices."""
    information_soup = BeautifulSoup(information.get_attribute("outerHTML"), "html.parser")
    historical_prices = information_soup.find_all("li")

    extracted_data = []
    for historical_price in historical_prices:
        date = historical_price.find("span").text
        market_info = historical_price.text.split(date)[1]

        raw_price_record = RawPriceRecord(date=date, market_info=market_info)
        extracted_data.append(raw_price_record)

    return extracted_data
