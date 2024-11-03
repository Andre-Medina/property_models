from datetime import date
from functools import lru_cache
from typing import Literal

import polars as pl
from au_address_parser import AbAddressUtility
from pydantic import BaseModel, ConfigDict
from tqdm import tqdm

from property_models import constants
from property_models.constants import (
    POSTCODE_SCHEMA,
    PRICE_RECORDS_SCHEMA,
    PROPERTIES_INFO_SCHEMA,
    PropertyCondition,
    PropertyType,
    RecordType,
)

ALLOWED_COUNTRIES = Literal["australia"]


####### POSTCODES #####################


class Postcode:
    """Class to hold postcodes for different countries and convert between postcodes and suburbs."""

    @lru_cache
    @staticmethod
    def read_postcodes(*, country: str) -> pl.DataFrame:
        """Read postcode for given country."""
        postcode_file = constants.POSTCODE_CSV_FILE.format(country=country)

        postcodes_raw = pl.read_csv(postcode_file, schema=POSTCODE_SCHEMA)

        postcodes = postcodes_raw.select(
            pl.col("suburb").str.strip_chars().str.to_uppercase().str.replace(" ", "_"),
            pl.col("postcode"),
        )

        return postcodes

    @classmethod
    def find_suburb(cls, *, postcode: int, country: str) -> str:
        """Find suburb name for the given postcode."""
        postcodes = cls.read_postcodes(country=country)

        try:
            suburb = postcodes.filter(pl.col("postcode") == postcode).select("suburb").item(0, 0)
        except IndexError:
            raise ValueError(f"Could not find suburb: {suburb!r}") from None

        return suburb

    @classmethod
    def find_postcode(cls, *, suburb: str, country: str) -> int:
        """Find postcode name for the given suburb."""
        postcodes = cls.read_postcodes(country=country)

        suburb_clean = suburb.strip().upper().replace(" ", "_")

        try:
            clean = postcodes.filter(pl.col("suburb") == suburb_clean).select("postcode").item(0, 0)
        except IndexError:
            raise ValueError(f"Could not find suburb: {suburb!r}") from None

        return clean


####### ADDRESSES ########################
class Address(BaseModel):
    """Dataclass to hold information about a single physical address location."""

    unit_number: int | str | None = None
    street_number: int
    street_name: str
    suburb: str
    postcode: int
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
            postcode=int(parsed_address._post),
            state=parsed_address._state,
            country="australia",
        )

        return address_object


########## PRICE RECORDS ###############
class PriceRecord(BaseModel):
    """Model to organise price records."""

    address: Address
    date: date
    record_type: RecordType
    price: int | None

    @classmethod
    def read(cls, *, country: str, state: str, suburb: str) -> pl.DataFrame:
        """Read historical records for a specific physical location."""
        price_records_file = constants.PRICE_RECORDS_CSV_FILE.format(
            country=country,
            state=state,
            suburb=suburb,
        )
        price_records_raw = cls._read_csv(price_records_file)

        postcode = Postcode.find_postcode(suburb=suburb, country=country)

        price_records_formatted = price_records_raw.select(
            pl.struct(
                pl.col("unit_number"),
                pl.col("street_number"),
                pl.col("street_name"),
                pl.lit(suburb).alias("suburb"),
                pl.lit(postcode).alias("postcode"),
                pl.lit(state).alias("state"),
                pl.lit(country).alias("country"),
            ).alias("address"),
            pl.col("date"),
            pl.col("record_type"),
            pl.col("price"),
        )

        return price_records_formatted

    @classmethod
    def _read_csv(_cls, file: str, /) -> pl.DataFrame:
        """Read and validate contents of file containing several records."""
        price_records = pl.read_csv(
            file,
            schema_overrides=PRICE_RECORDS_SCHEMA,
        )

        (
            price_records.with_columns(
                pl.col("record_type").map_elements(
                    lambda record_type: RecordType.parse(record_type, errors="null"), return_dtype=pl.String
                )
            )
        )

        return price_records

    @classmethod
    def write(cls, price_records: pl.DataFrame, *, country: str, state: str, suburb: str) -> None:
        """Write records to a csv file."""
        price_records_file = constants.PRICE_RECORDS_CSV_FILE.format(
            country=country,
            state=state,
            suburb=suburb,
        )

        price_records.write_csv(price_records_file)

    @classmethod
    def to_records(cls, price_record_list: list["PriceRecord"], /) -> pl.DataFrame:
        """Convert list of price records to a dataframe."""
        price_records_frame = (
            pl.DataFrame(price_record_list)
            .select(
                pl.col("address").struct["unit_number"],
                pl.col("address").struct["street_number"],
                pl.col("address").struct["street_name"],
                pl.col("date"),
                pl.col("record_type"),
                pl.col("price"),
            )
            .cast(PRICE_RECORDS_SCHEMA)
        )

        return price_records_frame


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
    construction_date: date | None
    floors: int | None

    model_config = ConfigDict({"arbitrary_types_allowed": True})

    @classmethod
    def read(cls, *, country: str, state: str, suburb: str) -> pl.DataFrame:
        """Read historical records for a specific physical location."""
        properties_info_json = constants.PROPERTIES_INFO_JSON_FILE.format(
            country=country,
            state=state,
            suburb=suburb,
        )
        historical_records = cls.read_json(properties_info_json)
        return historical_records

    @classmethod
    def read_json(_cls, properties_info_json: str, /, full_validation: bool = True) -> pl.DataFrame:
        """Read and validate contents of file containing several records."""
        """Read local `.json` file containing properties info into a dataframe."""

        properties_info_raw = pl.read_json(
            properties_info_json, schema=PROPERTIES_INFO_SCHEMA | {"construction_date": pl.String}
        )
        properties_info = properties_info_raw.with_columns(pl.col("construction_date").str.to_date())

        if full_validation:
            for item in tqdm(pl.concat([properties_info_raw]).to_dicts(), desc="Validating properties"):
                PropertyInfo.from_stringified_dict(item)

        return properties_info

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
                'postcode': 3032,
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
            'construction_date': '2000-01-01',
            'floors': 10}
        )
        ```
        """
        construction_date = stringified_dict.pop("construction_date")

        property_info_reloaded = cls(
            address=Address(**stringified_dict.pop("address")),
            property_type=PropertyType(stringified_dict.pop("property_type")),
            construction_date=None
            if construction_date is None
            else construction_date
            if isinstance(construction_date, date)
            else date.fromisoformat(construction_date),
            **stringified_dict,
        )

        return property_info_reloaded
