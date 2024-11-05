
from selenium.common.exceptions import NoSuchElementException
from typing import Any

def return_if_no_element(function, *, default_value: Any | None = None) -> Any | None:
    """Attempts to find element, if not found, returns default value."""
    try:
        return_value = function()
    except NoSuchElementException:
        return_value = default_value

    return return_value