from abc import abstractmethod
from contextlib import suppress
from enum import Enum
from typing import Literal

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


class MetaPropertyType(str, Enum):
    """MetaClothes class."""

    _name: str

    @property
    def value(self) -> tuple[str, str | None]:
        """Redefine `enum.value` to add parent type."""
        parent_value = self.__class__._name()
        child_value = getattr(self, "_value_", None)
        child_value = None if child_value == "None" else child_value
        return parent_value, child_value

    @classmethod
    @abstractmethod
    def _name(_cls) -> str:
        """Custom name."""
        pass


class PropertyTypeLand(MetaPropertyType):
    """Sub Enum for empty lots of land."""

    GENERAL = None
    NEW_BUILD = "new_build"
    OLD_LAND = "old_land"
    DEMOLITION = "demolition"

    @classmethod
    def _name(_cls) -> str:
        """Custom name."""
        return "land"


class PropertyTypeHouse(MetaPropertyType):
    """Sub enum for free standing houses."""

    GENERAL = None
    VICTORIAN = "victorian"
    WEATHER_BOARD = "weather_board"
    MODERN = "modern"
    NEW_BUILD = "new_build"

    @classmethod
    def _name(_cls) -> str:
        """Custom name."""
        return "free_standing_house"


class PropertyTypeTownHouse(MetaPropertyType):
    """Sub Enum for different town house sub classes."""

    GENERAL = None
    VICTORIAN = "victorian"
    MODERN = "modern"

    @classmethod
    def _name(_cls) -> str:
        """Custom name."""
        return "town_house"


class PropertyTypeApartment(MetaPropertyType):
    """Sub enum for different apartment sub classes."""

    GENERAL = None

    SIXTIES_BRICK = "sixties_brick"
    MODERN = "modern"
    SKY_SCRAPPER = "sky_scrapper"

    @classmethod
    def _name(_cls) -> str:
        """Custom name."""
        return "apartment"


class PropertyType(tuple[str, str | None]):
    """Enum to hold different property types."""

    LAND = PropertyTypeLand
    FREE_STANDING_HOUSE = PropertyTypeHouse
    TOWN_HOUSE = PropertyTypeTownHouse
    APARTMENT = PropertyTypeApartment

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
        try:
            parsed = cls(property_type)
            return parsed
        except Exception:  # noqa: B904
            raise NotImplementedError  # noqa: B904


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
