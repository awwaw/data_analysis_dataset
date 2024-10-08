from enum import Enum
from typing import Optional

from bs4 import BeautifulSoup

from selenium import webdriver

import datetime

import json

sweetness = {
    "сухое": "dry",
    "полусухое": "semi-dry",
    "полусладкое": "semi-sweet",
    "сладкое": "sweet"
}


def set_country(wine: dict, country: str):
    if country[-1] == ',':
        country = country[:-1]
    wine["country"] = country


def set_region(wine: dict, region: str):
    wine["region"] = region


def set_grape(wine: dict, grape: str):
    wine["grape"] = grape


def set_strength(wine: dict, strength: float):
    wine["strength"] = float(strength[:-1])


def set_sugar(wine: dict, sugar: str):
    wine["sweetness"] = sweetness[sugar.lower()]


def set_manufacturer(wine: dict, manufacturer: str):
    wine["manufacturer"] = manufacturer


def set_volume(wine: dict, volume: str):
    wine["volume"] = float(volume.split()[0])


methods = {
    "country": set_country,
    "region": set_region,
    "sugar_type": set_sugar,
    "grape": set_grape,
    "manufacturer": set_manufacturer,
    "strength": set_strength,
    "volume": set_volume
}


# ----------------------------------------------


def get_plain_text(filename: str = "wines.txt") -> list[str]:
    with open(filename, "r") as input_file:
        return input_file.readlines()


def print_error(error: Exception, parsing_value: str):
    print(f"Error while parsing {parsing_value}. Error - {error}")


def parse_price(value: str) -> Optional[int]:
    try:
        return int(''.join(value[:value.index("₽")].split()).strip())
    except Exception as e:
        print_error(e, "price")
        return None


def parse_product_info_link(link: str) -> Optional[str]:
    correct_url_prefix = "/catalog/vino/filter/"
    if not link.startswith(correct_url_prefix):
        return None

    tags = ["country", "region", "sugar_type", "manufacturer", "strength", "volume", "grape"]
    for tag in tags:
        if tag in link:
            return tag
    return None


def parse_link(driver: webdriver, link: str) -> (dict[str, str], dict[str, int]):
    failure_stats = {
        "name": 0,
        "price": 0,
        "rating": 0,
        "country": 0,
        "region": 0,
        "sugar_type": 0,
        "grape": 0,
        "manufacturer": 0,
        "strength": 0,
        "volume": 0
    }

    driver.get(link)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    result = {}
    tag_main = soup.find("main", attrs={"class": "product-page"})

    try:
        name = tag_main.find("h1", attrs={"class": "product-page__header"}).text.strip()
        result["name"] = name
    except Exception as e:
        print_error(e, "name")
        result["name"] = None
        failure_stats["name"] += 1

    price = tag_main.find("div", attrs={"class": "product-buy__price"})
    if price is None:
        price = tag_main.find("div", attrs={"class": "product-buy__old-price"})

    if price is not None:
        price = parse_price(price.text)
    if price is None:
        failure_stats["price"] += 1
    result["price"] = price

    try:
        rating = float(tag_main.find("p", attrs={"class": "rating-stars__value"}).text)
        result["rating"] = rating
    except Exception as e:
        print_error(e, "rating")
        result["rating"] = None
        failure_stats["rating"] += 1

    product_info = tag_main.find_all("dd", attrs={"class": "product-brief__value"})
    hrefs = {}
    for info in product_info:
        info_hrefs = info.find_all("a", href=True)
        for a in info_hrefs:
            link = a['href']
            hrefs[link] = a

    for q in hrefs:
        href = q
        tag = hrefs[q]
        t = parse_product_info_link(href)

        if t is None:
            continue

        try:
            methods[t](result, tag.text.strip())
        except Exception as e:
            print_error(e, t)
            methods[t] = None
            if t not in failure_stats:
                failure_stats[t] = 0
            failure_stats[t] += 1

    return result, failure_stats


def parse(starting_index: int):
    failure_stats = {
        "name": 0,
        "price": 0,
        "rating": 0,
        "country": 0,
        "region": 0,
        "sugar_type": 0,
        "grape": 0,
        "manufacturer": 0,
        "strength": 0,
        "volume": 0
    }

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_experimental_option(
        "prefs", {
            # block image loading
            "profile.managed_default_content_settings.images": 2,
        }
    )
    driver = webdriver.Chrome(options=options)
    links = get_plain_text()
    start = datetime.datetime.now()
    print(start)
    with open("parsed_wines.json", "w") as file:
        file.write("[")
        parsed = 0
        for link in links:
            try:
                result, failures = parse_link(driver, link)
            except Exception as _:
                continue
            for key in failures:
                if key not in failure_stats:
                    failure_stats[key] = 0
                failure_stats[key] += failures[key]

            json.dump(result, file)
            file.write(",\n")
            parsed += 1
            if parsed % 100 == 0:
                print(f"Parsed links: {parsed}, time spent: {datetime.datetime.now() - start}")
        file.write("]")
    end = datetime.datetime.now()
    print(end)
    print(f"Duration - {end - start}")

    with open("failure_stats.json", "w") as file:
        json.dump(failure_stats, file)


def main() -> None:
    index = 0
    with open("parsed_wines.json", "r") as file:
        lines = file.readlines()
        index = len(lines)
    parse(starting_index=index)


if __name__ == "__main__":
    main()
