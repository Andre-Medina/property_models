from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
from au_address_parser import AbAddressUtility
from property_models.constants import RecordType, PropertyType, PropertyCondition
from datetime import date

ALLOWED_COUNTRIES = Literal["australia"]


class Address(BaseModel):
    """Dataclass to hold information about a single physical address location."""

    unit_number: int | str | None = None
    street_number: int
    street_name: str
    suburb: str
    post_code: int
    state: str
    country: str

    @classmethod
    def parse(cls, address, *, country: ALLOWED_COUNTRIES) -> "Address":
        """Takes an address and a country and parses to a common format."""

        match country:
            case "australia":
                address_object = cls._parse_australian_address(address)

            case _:
                raise NotImplementedError(f"Cannot parse address for {country!r}")
            
        return address_object


    @classmethod
    def _parse_australian_address(cls, address) -> "Address":
        """Parses Australia specific address."""

        parsed_address = AbAddressUtility(address)

        address_object = cls(
            unit_number = int(parsed_address._flat) if parsed_address._flat else None,
            street_number = int(parsed_address._number_first),
            street_name = parsed_address._street,
            suburb = parsed_address._locality,
            post_code = int(parsed_address._post),
            state = parsed_address._state,
            country = "australia",
        )

        return address_object
    

class HistoricalPrice(BaseModel):

    record_type: RecordType
    address: Address
    price: int | None


class PropertyInfo(BaseModel):

    address: Address
    
    bed: int | None
    bath: int | None
    car: int | None

    property_size_m2: float | None
    land_size_m2: float | None

    condition: PropertyCondition | None 

    property_type: PropertyType | None
    date_of_construction: date | None
    floor_count: int | None


    model_config = ConfigDict({"arbitrary_types_allowed":True})
