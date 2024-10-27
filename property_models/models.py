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


class PropertyInfo(BaseModel):
    """Model to hold the general information about a property."""

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

    model_config = ConfigDict({"arbitrary_types_allowed": True})
