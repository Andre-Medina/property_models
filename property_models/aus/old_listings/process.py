import datetime
import re

from property_models.aus.old_listings.constants import RawListing
from property_models.constants import RecordType
from property_models.models import Address, PriceRecord, PropertyInfo


##### PROCESS RAW LISTING #####
def process_property_info(raw_listing: RawListing) -> PropertyInfo:
    """Extract the property info from the listing."""
    property_info = PropertyInfo(
        address=Address.parse(raw_listing.general_info.address, country="AUS"),
        beds=int(raw_listing.general_info.beds),
        baths=int(raw_listing.general_info.baths),
        cars=int(raw_listing.general_info.cars),
        property_size_m2=None,
        land_size_m2=None,
        condition=None,
        property_type=None,
        construction_date=None,
        floors=None,
    )

    return property_info


def process_price_records(raw_listing: RawListing) -> list[PriceRecord]:
    """Extract the price records from the listing."""
    address = Address.parse(raw_listing.general_info.address, country="AUS")

    recent_price = PriceRecord(
        address=address,
        date=parse_date(raw_listing.recent_price.date),
        record_type=parse_record_type(raw_listing.recent_price.market_info),
        price=parse_price(raw_listing.recent_price.market_info),
    )

    price_records = [recent_price]

    for historical_price in raw_listing.historical_prices:
        price_record = PriceRecord(
            address=address,
            date=parse_date(historical_price.date),
            record_type=parse_record_type(historical_price.market_info),
            price=parse_price(historical_price.market_info),
        )
        price_records.append(price_record)

    return price_records


###### PARSE PRICES AND RECORD TYPES ##########


def parse_date(date_raw: str) -> datetime.date:
    """Parse a date."""
    date_clean = datetime.datetime.strptime(date_raw.strip(), "%B %Y").date()
    return date_clean


PRICE_PATTERN_SINGLE = r"^\$([\,\.\d]+)(\s[^\-]+|$)"
PRICE_EXTRACTION_SINGLE = r"\1"
PRICE_PATTERN_RANGE = r"^\$([\,\.\d]+)(\s*-\s*)\$([\,\.\d]+)"
PRICE_EXTRACTION_RANGE_LOWER = r"\1"
price_extraction_range_upper = r"\3"


def parse_price(price_info: str) -> int | None:
    """Takes a price as a string in and outputs a float.

    E.g.
    ```
    Auction => None
    Contact => None
    $415,000 => 415000.0
    $350 Week => 350.0
    $410,000 Price Guide => 410000.0
    $480,000 - $520,000 => 500000.0
    $480,000 - $520,000 Auction => 500000.0
    ```
    """
    if (match := re.match(PRICE_PATTERN_SINGLE, price_info)) is not None:
        price = int(match.expand(PRICE_EXTRACTION_SINGLE).replace(",", ""))

    elif (match := re.match(PRICE_PATTERN_RANGE, price_info)) is not None:
        lower_price = int(match.expand(PRICE_EXTRACTION_RANGE_LOWER).replace(",", ""))
        upper_price = int(match.expand(price_extraction_range_upper).replace(",", ""))
        price = int((lower_price + upper_price) * 0.5)
    else:
        price = None

    return price


RECORD_TYPE_PATTERN = r"([\$\d\,\.\-\s]*)([a-zA-Z\s]+)"
RECORD_TYPE_EXTRACTION = r"\2"


def parse_record_type(price_info: str) -> RecordType | None:
    """Takes the price information and extracts the type of the record.

    E.g.
    ```
    Auction  :  RecordType.AUCTION
    Contact  :  RecordType.ENQUIRY
    By Negotiation  :  RecordType.PRIVATE_SALE
    $495,000  :  None
    $440 Private Sale  :  RecordType.PRIVATE_SALE
    $430,000 Private Sale  :  RecordType.PRIVATE_SALE
    $440,000 - $480,000  :  None
    $320,000 - $350,000 Auction  :  RecordType.AUCTION
    ```
    """
    if (match := re.match(RECORD_TYPE_PATTERN, price_info)) is not None:
        words = match.expand(RECORD_TYPE_EXTRACTION)
        type = RecordType.parse(words, errors="null")
    else:
        type = None

    return type
