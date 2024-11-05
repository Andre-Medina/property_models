import datetime
import re

from property_models.constants import RecordType

###### PARSE PRICES AND RECORD TYPES ##########


def parse_date(date_raw: str) -> datetime.date:
    """Parse a date.

    E.g
    ```
    "March 2000" -> date(2000, 3, 1)
    "July 2019" -> date(2019, 7, 1)
    "December 2025" -> date(2025, 12, 1)
    ```

    """
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
