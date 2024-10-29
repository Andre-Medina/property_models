from datetime import date
from typing import Literal

import polars as pl
from au_address_parser import AbAddressUtility
from pydantic import BaseModel, ConfigDict

from property_models.constants import (
    HISTORICAL_RECORDS_CSV_FILE,
    HISTORICAL_RECORDS_SCHEMA,
    # PROPERTIES_INFO_JSON_FILE,
    PropertyCondition,
    PropertyType,
    RecordType,
)

ALLOWED_COUNTRIES = Literal["australia"]


####### ADDRESSES ########################
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
            unit_number=int(parsed_address._flat) if parsed_address._flat else None,
            street_number=int(parsed_address._number_first),
            street_name=parsed_address._street,
            suburb=parsed_address._locality,
            post_code=int(parsed_address._post),
            state=parsed_address._state,
            country="australia",
        )

        return address_object


########## HISTORICAL PRICES ###############
class HistoricalPrice(BaseModel):
    """Model to organise historical prices."""

    record_type: RecordType
    address: Address
    date: date
    price: int | None

    @classmethod
    def read_location(cls, *, country: str, state: str, suburb: str) -> pl.DataFrame:
        """Read historical records for a specific physical location."""
        historical_records_file = HISTORICAL_RECORDS_CSV_FILE.format(
            country=country,
            state=state,
            suburb=suburb,
        )
        historical_records = cls.read_csv(historical_records_file)
        return historical_records

    @classmethod
    def read_csv(_cls, file: str, /) -> pl.DataFrame:
        """Read and validate contents of file containing several records."""
        historical_records = pl.read_csv(
            file,
            schema_overrides=HISTORICAL_RECORDS_SCHEMA,
        )

        (
            historical_records.with_columns(
                pl.col("record_type").map_elements(
                    lambda record_type: RecordType.parse(record_type, errors="null"), return_dtype=pl.String
                )
            )
        )

        return historical_records

    @classmethod
    def to_records(cls, historical_prices: list["HistoricalPrice"], /) -> pl.DataFrame:
        """Convert list of historical prices to a dataframe."""
        historical_records = (
            pl.DataFrame(historical_prices)
            .select(
                pl.col("address").struct["unit_number"],
                pl.col("address").struct["street_number"],
                pl.col("address").struct["street_name"],
                pl.col("date"),
                pl.col("record_type"),
                pl.col("price"),
            )
            .cast(HISTORICAL_RECORDS_SCHEMA)
        )

        return historical_records


##### PROPERTY INFO ################
class PropertyInfo(BaseModel):
    """Model to hold the general information about a property."""

    address: Address

    beds: int | None
    baths: int | None
    cars: int | None

    property_size_m2: float | None
    land_size_m2: float | None

    condition: PropertyCondition | None

    property_type: PropertyType | None
    date_of_construction: date | None
    floors: int | None

    model_config = ConfigDict({"arbitrary_types_allowed": True})

    @classmethod
    def from_stringified_dict(cls, stringified_dict: dict, /) -> "PropertyInfo":
        """Takes a dictionary of stringified parameters and returns a created object.

        e.g.
        ```
        PropertyInfo.from_stringified_dict({
            'address': {
                'unit_number': None,
                'street_number': 80,
                'street_name': 'ROSEBERRY STREET',
                'suburb': 'NORTH MELBOURNE',
                'post_code': 3032,
                'state': 'VIC',
                'country': 'australia',
            },
            'beds': 10,
            'baths': 10,
            'cars': 10,
            'property_size_m2': 304.4,
            'land_size_m2': 100.3,
            'condition': None,
            'property_type': ['apartment', 'sixties_brick'],
            'date_of_construction': '2000-01-01',
            'floors': 10}
        )
        ```
        """
        property_info_reloaded = cls(
            address=Address(**stringified_dict.pop("address")),
            property_type=PropertyType(stringified_dict.pop("property_type")),
            date_of_construction=date.fromisoformat(stringified_dict.pop("date_of_construction")),
            **stringified_dict,
        )

        return property_info_reloaded
