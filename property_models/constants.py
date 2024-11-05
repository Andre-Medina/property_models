import os
from abc import abstractmethod
from contextlib import suppress
from enum import Enum
from functools import lru_cache
from typing import Literal

import polars as pl

DATA_DIR: str = None

if (DATA_DIR := os.environ.get("DATA_DIR")) is None:
    current_dir = os.getcwd()
    root_dir = current_dir.rsplit("/property_models", maxsplit=1)[0]
    DATA_DIR = f"{root_dir}/property_models/data"

POSTCODE_CSV_FILE: str = DATA_DIR + "/processed/{country}/suburb_to_postcode.csv"
PRICE_RECORDS_CSV_FILE: str = DATA_DIR + "/processed/{country}/{state}/{suburb}/records.csv"
PROPERTIES_INFO_JSON_FILE: str = DATA_DIR + "/processed/{country}/{state}/{suburb}/properties.json"

ALLOWED_COUNTRIES = Literal["AUS"]

####### SCHEMAS #######

ADDRESS_SCHEMA = pl.Schema(
    {
        "unit_number": pl.UInt16,
        "street_number": pl.UInt16,
        "street_name": pl.String,
        "suburb": pl.String,
        "postcode": pl.UInt16,
        "state": pl.String,
        "country": pl.String,
    }
)

PRICE_RECORDS_COMPRESSED_SCHEMA = pl.Schema(
    {
        "unit_number": pl.UInt16,
        "street_number": pl.UInt16,
        "street_name": pl.String,
        "date": pl.Date,
        "record_type": str,
        "price": pl.UInt32,
    }
)

PRICE_RECORDS_SCHEMA = pl.Schema(
    {
        "address": pl.Struct(ADDRESS_SCHEMA),
        "date": pl.Date,
        "record_type": str,
        "price": pl.UInt32,
    }
)

PROPERTIES_INFO_SCHEMA = pl.Schema(
    {
        "address": pl.Struct(ADDRESS_SCHEMA),
        "beds": pl.UInt8,
        "baths": pl.UInt8,
        "cars": pl.UInt8,
        "property_size_m2": pl.Float32,
        "land_size_m2": pl.Float32,
        "condition": pl.String,
        "property_type": pl.List(pl.String),
        "construction_date": pl.Date(),
        "floors": pl.UInt8,
    }
)

POSTCODE_SCHEMA = pl.Schema(
    {
        "postcode": pl.UInt16,
        "suburb": pl.String,
    }
)

####### RECORD TYPE ################


class RecordType(str, Enum):
    """Different kinds of record types for property information."""

    AUCTION = "auction"
    PRIVATE_SALE = "private_sale"
    ENQUIRY = "enquiry"
    NO_SALE = "no_sale"
    RENT = "rent"

    @classmethod
    def parse(cls, record_type: str, *, errors: Literal["raise", "coerce", "null"] = "raise") -> "RecordType":
        """Takes a string and converts it into an enum.

        Parameters
        ----------
        record_type : str, string to be cleaned into an enum.
        errors : Literal["raise", "coerce", "null"], optional, How to handle errors when bad values are passed, by
            default "raise".

        Returns
        -------
        RecordType, enum relating to the passed string.

        Raises
        ------
        ValueError, If bad value is passed.
        NotImplementedError, If called with un implemented parameters.
        """
        record_clean = record_type.strip().replace("  ", " ").replace(" ", "_").lower()

        with suppress(ValueError):
            record_enum = cls(record_clean)
            return record_enum

        match record_clean:
            case "auction":
                record_enum = cls.AUCTION
            case "by_negotiation":
                record_enum = cls.PRIVATE_SALE
            case "price_guide" | "contact" | "in_excess_of":
                record_enum = cls.ENQUIRY
            case "week":
                record_enum = cls.RENT
            case _:  # " " | "_" | "":
                if errors == "raise":
                    raise ValueError(f"Cannot find type for {record_clean!r} ({record_type!r})")
                if errors == "null":
                    return None
                if errors == "coerce":
                    raise NotImplementedError("'coerce' is not implemented yet")

        return record_enum


####### PROPERTY TYPE ################


class SubPropertyType(str, Enum):
    """MetaClothes class."""

    _name: str

    @property
    def value(self) -> "PropertyType":
        """Redefine `enum.value` to add parent type."""
        parent_value = self.__class__._name()
        child_value = getattr(self, "_value_", None)
        child_value = None if child_value == "None" else child_value
        value_as_object = PropertyType((parent_value, child_value))
        return value_as_object

    @classmethod
    @abstractmethod
    def _name(_cls) -> str:
        """Custom name."""
        pass


class PropertyTypeLand(SubPropertyType):
    """Sub Enum for empty lots of land."""

    GENERAL = "None"
    NEW_BUILD = "new_build"
    OLD_LAND = "old_land"
    DEMOLITION = "demolition"

    @classmethod
    def _name(_cls) -> str:
        """Custom name."""
        return "land"


class PropertyTypeHouse(SubPropertyType):
    """Sub enum for free standing houses."""

    GENERAL = "None"
    VICTORIAN = "victorian"
    WEATHER_BOARD = "weather_board"
    MODERN = "modern"
    NEW_BUILD = "new_build"

    @classmethod
    def _name(_cls) -> str:
        """Custom name."""
        return "free_standing_house"


class PropertyTypeTownHouse(SubPropertyType):
    """Sub Enum for different town house sub classes."""

    GENERAL = "None"
    VICTORIAN = "victorian"
    MODERN = "modern"

    @classmethod
    def _name(_cls) -> str:
        """Custom name."""
        return "town_house"


class PropertyTypeApartment(SubPropertyType):
    """Sub enum for different apartment sub classes."""

    GENERAL = "None"

    SIXTIES_BRICK = "sixties_brick"
    MODERN = "modern"
    SKY_SCRAPPER = "sky_scrapper"

    @classmethod
    def _name(_cls) -> str:
        """Custom name."""
        return "apartment"


class PropertyType(tuple[str, str]):
    """Enum to hold different property types."""

    LAND = PropertyTypeLand
    FREE_STANDING_HOUSE = PropertyTypeHouse
    TOWN_HOUSE = PropertyTypeTownHouse
    APARTMENT = PropertyTypeApartment

    def __init__(self, values: tuple[str, str | None]):
        """Create a PropertyType enum."""
        self.tuple_to_enum(values)

    def tuple_to_enum(cls, values: tuple[str, str | None]) -> "SubPropertyType":
        """Take a tuple, validate it, and pass the corrected enum."""
        try:
            sub_enum = cls._sub_enum_lookup()[values[0]]
            chosen_enum = sub_enum(values[1] or "None")
            return chosen_enum
        except (KeyError, ValueError) as exc:
            exc.add_note(f"Unknown enum values {values!r}.")
            raise exc

    @classmethod
    @lru_cache
    def _sub_enum_lookup(cls) -> dict[str, SubPropertyType]:
        sub_enum_lookup = {
            sub_enum_class._name(): sub_enum_class
            for _sub_enum_name, sub_enum_class in cls.__dict__.items()
            if isinstance(sub_enum_class, Enum.__class__)
        }
        return sub_enum_lookup

    @classmethod
    def parse(cls, property_type: str, *, errors: Literal["raise", "coerce", "null"] = "raise") -> "PropertyType":  # noqa: ARG003
        """Takes a string and converts it into an enum.

        Parameters
        ----------
        property_type : str, string to be cleaned into an enum.
        errors : Literal["raise", "coerce", "null"], optional, How to handle errors when bad values are passed, by
            default "raise".

        Returns
        -------
        PropertyType, enum relating to the passed string.

        Raises
        ------
        ValueError, If bad value is passed.
        NotImplementedError, If called with un implemented parameters.
        """
        if property_type is None:
            return None

        with suppress(AttributeError):
            parsed = cls(property_type.value)
            return parsed
        property_type_clean = property_type.lower().strip().replace(" ", "_")

        # if ('unit' in property_type_clean) | ("apmt" in property_type):
        if property_type_clean == "unit/apmt":
            return cls.APARTMENT.GENERAL.value
        if property_type_clean == "townhouse":
            return cls.APARTMENT.GENERAL.value
        if property_type_clean == "house":
            return cls.APARTMENT.GENERAL.value
        if property_type_clean == "sales_residential":
            return None

        raise NotImplementedError(f"cannot process land type: {property_type_clean!r}")


#### Property condition #########


class PropertyCondition(Enum):  # noqa: ARG003
    """Enum to hold the different property conditions."""

    @classmethod
    def parse(
        cls, property_condition: str, *, errors: Literal["raise", "coerce", "null"] = "raise"
    ) -> "PropertyCondition":
        """Takes a string and converts it into an enum.

        Parameters
        ----------
        property_condition : str, string to be cleaned into an enum.
        errors : Literal["raise", "coerce", "null"], optional, How to handle errors when bad values are passed, by
            default "raise".

        Returns
        -------
        PropertyCondition, enum relating to the passed string.

        Raises
        ------
        ValueError, If bad value is passed.
        NotImplementedError, If called with un implemented parameters.
        """
        raise NotImplementedError
