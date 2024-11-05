from pydantic import BaseModel, model_validator
from typing_extensions import Self

from property_models.aus.old_listings.parse import parse_date, parse_price, parse_record_type
from property_models.constants import PropertyType
from property_models.models import (
    Address,
    Postcode,  # Address, Postcode, PriceRecord, PropertyInfo
    PriceRecord,
    PropertyInfo,
)

OLD_LISTINGS_BASE_URL = "https://www.oldlistings.com.au/"
OLD_LISTINGS_URL = (
    OLD_LISTINGS_BASE_URL
    + "real-estate/{state}/{suburb}/{postcode}/buy/{page}/:bed:{beds}:bedmax:{beds}:bath:{baths}:car:{cars}"
)


##### OLD LISTING URL ########
class OldListingURL(BaseModel):
    """Model to hold inputs."""

    state: str
    suburb: str
    postcode: int
    page: int
    beds: int
    baths: int
    cars: int

    @model_validator(mode="after")
    def check_postcode(self) -> Self:
        """Check postcode matches suburb."""
        postcode = Postcode.find_postcode(suburb=self.suburb, country="AUS")
        if postcode != self.postcode:
            raise ValueError(f"Postcode: {self.postcode!r} doesn't match suburb: {self.suburb!r}")
        return self

    def format(self) -> str:
        """Convert inputs to url to correct page."""
        url_kwargs_raw = self.model_dump()

        url_kwargs = url_kwargs_raw | {"suburb": url_kwargs_raw["suburb"].replace(" ", "+").lower()}
        url = OLD_LISTINGS_URL.format(**url_kwargs)

        return url

    def next_page(self) -> "OldListingURL":
        """Move to the next page."""
        url_kwargs_raw = self.model_dump()
        url_kwargs_updated = url_kwargs_raw | {"page": url_kwargs_raw["page"] + 1}
        new_url = self.__class__(**url_kwargs_updated)
        return new_url

    def to_page(self, page_number) -> "OldListingURL":
        """Move to certain page."""
        url_kwargs_raw = self.model_dump()
        url_kwargs_updated = url_kwargs_raw | {"page": page_number}
        new_url = self.__class__(**url_kwargs_updated)
        return new_url


##### OLD LISTING DATA #####


class RawPropertyInfo(BaseModel):
    """Model for raw info for a property."""

    address: str
    beds: str
    cars: str
    baths: str
    property_type: str


class RawPriceRecord(BaseModel):
    """Model to hold a raw price record."""

    date: str
    market_info: str


class RawListing(BaseModel):
    """Model to hold raw listing from Old Listing."""

    general_info: RawPropertyInfo
    recent_price: RawPriceRecord
    historical_prices: list[RawPriceRecord]

    def to_property_info(self) -> PropertyInfo:
        """Extract the property info from the listing."""
        property_info = PropertyInfo(
            address=Address.parse(self.general_info.address, country="AUS"),
            beds=int(self.general_info.beds),
            baths=int(self.general_info.baths),
            cars=int(self.general_info.cars),
            property_size_m2=None,
            land_size_m2=None,
            condition=None,
            property_type=PropertyType.parse(self.general_info.property_type, errors="raise"),
            construction_date=None,
            floors=None,
        )

        return property_info

    def to_price_records(self) -> list[PriceRecord]:
        """Extract the price records from the listing."""
        address = Address.parse(self.general_info.address, country="AUS")

        recent_price = PriceRecord(
            address=address,
            date=parse_date(self.recent_price.date),
            record_type=parse_record_type(self.recent_price.market_info),
            price=parse_price(self.recent_price.market_info),
        )

        price_records = [recent_price]

        for historical_price in self.historical_prices:
            price_record = PriceRecord(
                address=address,
                date=parse_date(historical_price.date),
                record_type=parse_record_type(historical_price.market_info),
                price=parse_price(historical_price.market_info),
            )
            price_records.append(price_record)

        return price_records
