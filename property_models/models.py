import json
import re
from datetime import date
from functools import lru_cache

import fsspec
import polars as pl
from au_address_parser import AbAddressUtility
from pydantic import BaseModel, ConfigDict
from tqdm import tqdm

from property_models import constants
from property_models.constants import (
    ADDRESS_SCHEMA,
    ALLOWED_COUNTRIES,
    POSTCODE_SCHEMA,
    PRICE_RECORDS_COMPRESSED_SCHEMA,
    PRICE_RECORDS_SCHEMA,
    PROPERTIES_INFO_SCHEMA,
    PropertyCondition,
    PropertyType,
    RecordType,
)


####### POSTCODES #####################
class Postcode:
    """Class to hold postcodes for different countries and convert between postcodes and suburbs."""

    @lru_cache
    @staticmethod
    def read_postcodes(*, country: ALLOWED_COUNTRIES) -> pl.DataFrame:
        """Read postcode for given country."""
        postcode_file = constants.POSTCODE_CSV_FILE.format(country=country)

        postcodes_raw = pl.read_csv(postcode_file, schema=POSTCODE_SCHEMA)

        postcodes = postcodes_raw.select(
            pl.col("suburb").str.strip_chars().str.to_uppercase().str.replace(" ", "_"),
            pl.col("postcode"),
        )

        return postcodes

    @classmethod
    def find_suburb(cls, *, postcode: int, country: ALLOWED_COUNTRIES) -> str:
        """Find suburb name for the given postcode."""
        postcodes = cls.read_postcodes(country=country)

        try:
            suburb = postcodes.filter(pl.col("postcode") == postcode).select("suburb").item(0, 0)
        except IndexError:
            raise ValueError(f"Could not find suburb: {suburb!r}") from None

        return suburb

    @classmethod
    def find_postcode(cls, *, suburb: str, country: ALLOWED_COUNTRIES) -> int:
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
    street_number: int | str
    street_name: str
    suburb: str
    postcode: int
    state: str
    country: ALLOWED_COUNTRIES

    @classmethod
    def parse(cls, address, *, country: ALLOWED_COUNTRIES) -> "Address":
        """Takes an address and a country and parses to a common format."""
        address_cleaned = address.strip()
        match country:
            case "AUS":
                address_object = cls._parse_australian_address(address_cleaned)

            case _:
                raise NotImplementedError(f"Cannot parse address for {country!r}")

        return address_object

    @classmethod
    def _parse_australian_address(cls, address) -> "Address":
        """Parses Australia specific address."""
        try:
            address_ = address
            address_ = address_.split("&")[-1].strip()  # Split '1.02 & 1.10, 1 road...`  into just `1.10, 1 road...`
            address_ = address_.replace(".", "")  #  remove `1.02` -> `102`
            address_ = re.sub(r"^([a-zA-Z\d\.]+),\s*", r"\1/", address_)  #  `unit, number` into `unit/ number`
            address_ = address_.replace("_", " ")  # Fix "SUBURB_NAME" into "SUBURB NAME"
            address_ = address_.strip()
            parsed_address = AbAddressUtility(address_)
        except Exception as exc:
            exc.add_note(f"Issue with address: {address!r}")
            exc.add_note(f"Cleaned as: {address_!r}")
            raise exc

        address_object = cls(
            unit_number=parsed_address._flat if parsed_address._flat else None,
            street_number=parsed_address._number_first,
            street_name=parsed_address._street,
            suburb=parsed_address._locality.replace(" ", "_"),
            postcode=int(parsed_address._post),
            state=parsed_address._state,
            country="AUS",
        )

        return address_object

    @classmethod
    def join_on(cls, dataframe_1: pl.DataFrame, dataframe_2: pl.DataFrame, /) -> pl.DataFrame:
        """Join two dataframes with a `pl.Struct` `'address'` column on the addresses."""
        cls._check_address_column(dataframe_1)
        cls._check_address_column(dataframe_2)

        dataframe_joined = (
            dataframe_1.select(cls.expand_address_column())
            .join(
                dataframe_2.select(cls.expand_address_column()),
                on=cls.unnested_address_columns(),
                how="outer",
                suffix="_right",
                join_nulls=True,
            )
            .with_columns(cls.collapse_address_column())
            .drop(*cls.unnested_address_columns(), *cls.unnested_address_columns(suffix="_right"))
        )

        return dataframe_joined

    @classmethod
    def _check_address_column(_cls, df: pl.DataFrame) -> None:
        try:
            is_address_struct = isinstance(df["address"].dtype, pl.Struct)
            if not is_address_struct:
                raise pl.exceptions.ColumnNotFoundError()
        except pl.exceptions.ColumnNotFoundError:
            raise ValueError(f"Data found to not have a valid `'address'` column:\n{df}") from None

    @classmethod
    def expand_address_column(cls) -> pl.Expr:
        """Return polars expression for expand_address_column."""
        return (pl.exclude("address"), pl.col("address").struct.unnest())

    @classmethod
    def unnested_address_columns(cls, *, suffix: str = "") -> list[pl.Expr]:
        """Return polars expression for unnested_address_columns."""
        return [pl.col(f"{address_column}{suffix}") for address_column in ADDRESS_SCHEMA]

    @classmethod
    def collapse_address_column(cls) -> pl.Expr:
        """Return polars expression for collapse_address_column."""
        return pl.struct(cls.unnested_address_columns()).alias("address")


########## PRICE RECORDS ###############
class PriceRecord(BaseModel):
    """Model to organise price records."""

    address: Address
    date: date
    record_type: RecordType | None
    price: int | None

    @classmethod
    def read(cls, *, country: ALLOWED_COUNTRIES, state: str, suburb: str) -> pl.DataFrame:
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
                pl.col("unit_number").cast(ADDRESS_SCHEMA["unit_number"]),
                pl.col("street_number").cast(ADDRESS_SCHEMA["street_number"]),
                pl.col("street_name").cast(ADDRESS_SCHEMA["street_name"]),
                pl.lit(suburb).alias("suburb").cast(ADDRESS_SCHEMA["suburb"]),
                pl.lit(postcode).alias("postcode").cast(ADDRESS_SCHEMA["postcode"]),
                pl.lit(state).alias("state").cast(ADDRESS_SCHEMA["state"]),
                pl.lit(country).alias("country").cast(ADDRESS_SCHEMA["country"]),
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
            schema_overrides=PRICE_RECORDS_COMPRESSED_SCHEMA,
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
    def write(cls, price_records: pl.DataFrame, *, country: ALLOWED_COUNTRIES, state: str, suburb: str) -> None:
        """Write records to a csv file."""
        price_records_file = constants.PRICE_RECORDS_CSV_FILE.format(
            country=country,
            state=state,
            suburb=suburb,
        )

        price_records_compressed = price_records.select(
            pl.col("address").struct["unit_number"],
            pl.col("address").struct["street_number"],
            pl.col("address").struct["street_name"],
            pl.col("date"),
            pl.col("record_type"),
            pl.col("price"),
        )

        with fsspec.open(price_records_file, "w") as open_file:
            price_records_compressed.write_csv(open_file)

    @classmethod
    def to_dataframe(cls, price_record_list: list["PriceRecord"], /) -> pl.DataFrame:
        """Convert list of price records to a dataframe."""
        price_records_frame = pl.DataFrame(price_record_list).cast(PRICE_RECORDS_SCHEMA)

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
    def read(cls, *, country: ALLOWED_COUNTRIES, state: str, suburb: str) -> pl.DataFrame:
        """Read historical records for a specific physical location."""
        properties_info_file = constants.PROPERTIES_INFO_JSON_FILE.format(
            country=country,
            state=state,
            suburb=suburb,
        )
        properties_info = cls.read_json(properties_info_file)
        return properties_info

    @classmethod
    def read_json(_cls, properties_info_file: str, /, full_validation: bool = True) -> pl.DataFrame:
        """Read and validate contents of file containing several records."""
        """Read local `.json` file containing properties info into a dataframe."""

        properties_info_raw = pl.read_json(
            properties_info_file, schema=PROPERTIES_INFO_SCHEMA | {"construction_date": pl.String}
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

    @classmethod
    def write(cls, properties_info: pl.DataFrame, *, country: ALLOWED_COUNTRIES, state: str, suburb: str) -> None:
        """Write historical records to a json file."""
        properties_info_file = constants.PROPERTIES_INFO_JSON_FILE.format(
            country=country,
            state=state,
            suburb=suburb,
        )

        with fsspec.open(properties_info_file, "w") as open_file:
            json.dump(properties_info.rows(named=True), open_file, indent=4, default=str)

    @classmethod
    def to_dataframe(cls, property_info_list: list["PropertyInfo"], /) -> pl.DataFrame:
        """Convert list of price records to a dataframe."""
        property_info_frame = pl.DataFrame(property_info_list).cast(PROPERTIES_INFO_SCHEMA)
        return property_info_frame
