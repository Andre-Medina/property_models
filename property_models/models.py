from pydantic import BaseModel
from typing import Literal
from au_address_parser import AbAddressUtility

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
            unit_number = parsed_address._flat,
            street_number = int(parsed_address._number_first),
            street_name = parsed_address._street,
            suburb = parsed_address._locality,
            post_code = int(parsed_address._post),
            state = parsed_address._state,
            country = "australia",
        )

        return address_object
    

