from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


def extract_info(listing):
    address = ""
    try:
        information_list = listing.find_element(By.TAG_NAME, "section").find_elements(By.TAG_NAME, "section")

        general_info = extract_general(information_list[0])
        recent_price = extract_recent(information_list[1])
        historical_prices = extract_historical(information_list[2])

        extracted_data = {
            "general_info": general_info,
            "recent_price": recent_price,
            "historical_prices": historical_prices,
        }

        return extracted_data

    except:
        print(address, "FAILED")


def extract_recent(information: WebElement) -> dict[str, str | float | int]:
    """Extract recent prices."""
    date = information.find_element(By.TAG_NAME, "span").text.split(":")[-1]
    price = information.find_element(By.TAG_NAME, "h3").text.split(" ")[0]

    recent_price = {
        "date": date,
        "price": 0,
        "type": price,
    }

    return recent_price


def extract_general(information: WebElement) -> dict[str, str | float | int]:
    """Extract general information."""
    address = information.find_element(By.TAG_NAME, "h2").text
    bed = information.find_element(By.CLASS_NAME, "bed").text
    bath = information.find_element(By.CLASS_NAME, "bath").text
    car = information.find_element(By.CLASS_NAME, "car").text
    type = information.find_element(By.CLASS_NAME, "type").text

    general_info = {
        "address": address,
        "bed": bed,
        "bath": bath,
        "car": car,
        "type": type,
    }

    return general_info


def extract_historical(information: WebElement) -> list[dict[str, str | float | int]]:
    """Extract historical prices."""
    information_soup = BeautifulSoup(information.get_attribute("outerHTML"), "html.parser")
    historical_prices = information_soup.find_all("li")

    extracted_data = []
    for historical_price in historical_prices:
        date = historical_price.find("span").text
        market_info = historical_price.text.split(date)[1]
        extracted_data.append(
            {
                "date": date,
                "price": 0,
                "type": market_info,
            }
        )

    return extracted_data