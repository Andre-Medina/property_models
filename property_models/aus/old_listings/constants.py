from pydantic import BaseModel, model_validator
from typing_extensions import Self

from property_models.models import Postcode  # Address, Postcode, PriceRecord, PropertyInfo

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
    """Model to hold raw listing from Old Listing ."""

    general_info: RawPropertyInfo
    recent_price: RawPriceRecord
    historical_prices: list[RawPriceRecord]
