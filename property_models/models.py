from datetime import date
from typing import Literal

import polars as pl
from au_address_parser import AbAddressUtility
from pydantic import BaseModel, ConfigDict
from tqdm import tqdm

from property_models.constants import (
    HISTORICAL_RECORDS_CSV_FILE,
    HISTORICAL_RECORDS_SCHEMA,
    PROPERTIES_INFO_JSON_FILE,
    PROPERTIES_INFO_SCHEMA,
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
    construction_date: date | None
    floors: int | None

    model_config = ConfigDict({"arbitrary_types_allowed": True})

    @classmethod
    def read(cls, *, country: str, state: str, suburb: str) -> pl.DataFrame:
        """Read historical records for a specific physical location."""
        properties_info_json = PROPERTIES_INFO_JSON_FILE.format(
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
