
from enum import Enum
from contextlib import suppress
from typing import Literal

class RecordType(Enum):
    AUCTION = "auction"
    PRIVATE_SALE = "private_sale"
    ENQUIRY = "enquiry"
    NO_SALE = "no_sale"
    RENT = "rent"

    @classmethod
    def clean(cls, record_type: str, *, errors: Literal["raise", "coerce", "null"] = "raise") -> "RecordType":
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
            case _: #" " | "_" | "":
                if errors == "raise":
                    raise ValueError(f"Cannot find type for {record_clean!r} ({record_type!r})")
                if errors == "null":
                    return None
                if errors == "coerce":
                    raise NotImplementedError("'coerce' is not implemented yet")

        return record_enum