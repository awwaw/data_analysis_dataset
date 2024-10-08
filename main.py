import requests
from bs4 import BeautifulSoup
import datetime


URL = "https://simplewine.ru/catalog/vino/"
HREF_PREFIX = "https://simplewine.ru"
AMOUNT_OF_PAGES = 111
PAGES = range(1, AMOUNT_OF_PAGES + 1)


def get_page_url(page_number: int, url: str = URL) -> str:
    return url + f"page{page_number}"


def verify_href(href: str) -> bool:
    return href.startswith("/catalog/product") and not href.endswith("/reviews/")


def get_product_pages_links() -> list[str]:
    products_links = []

    for page_number in PAGES:
        response = requests.get(url=get_page_url(page_number=page_number))
        data = response.content
        parsed_html = BeautifulSoup(data)
        catalogue = parsed_html.body.find("div", attrs={"class": "catalog__right-side"})
        items = catalogue.find_all("div", attrs={"class": "catalog-grid__item"})

        for item in items:
            hrefs = list(map(lambda x: x["href"], item.find_all("a", href=True)))
            valid_hrefs = list(map(lambda x: HREF_PREFIX + x, filter(verify_href, hrefs)))
            products_links += valid_hrefs

    return list(set(products_links))


def write_to_plain_text(items: list[str], filename: str = "wines.txt") -> None:
    with open(filename, "w") as output_file:
        for item in items:
            output_file.write(item + "\n")


def main() -> None:
    start = datetime.datetime.now()
    wines = get_product_pages_links()
    write_to_plain_text(wines)
    end = datetime.datetime.now()
    print(f"Duration: {end - start}")


if __name__ == "__main__":
    main()
