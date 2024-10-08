import json
import csv
import arff

from transliterate import translit


OUTPUT_FILE = "raw_dataset.tsv"
ARFF_FILE = "wines_dataset.arff"


def is_ascii(string: str) -> bool:
    return all(list(map(lambda x: ord(x) < 128, string)))


def to_tsv(filename: str = "parsed_wines.json"):
    with open(filename, "r") as file:
        objects = json.load(file)

    for obj in objects:
        for key in obj:
            try:
                if is_ascii(obj[key]):
                    continue
            except TypeError:
                continue

            obj[key] = translit(obj[key], "ru", reversed=True)

    with open(OUTPUT_FILE, "w") as file:
        dw = csv.DictWriter(file, objects[0].keys(), delimiter="\t")
        dw.writeheader()
        dw.writerows(objects)


def to_arff(filename: str = "raw_dataset.tsv"):
    with open(filename, "r") as file:
        reader = csv.reader(file, delimiter="\t", quotechar='"')
        header = None
        data = []
        for row in reader:
            if header is None:
                header = row
            elif len(row) > 0:
                data.append(row)

    content = {"relation": "Wines dataset", "attributes": []}
    attributes = []
    for h in header:
        if h in ["name", "country", "region", "grape", "manufacturer"]:
            attributes.append((h, "STRING"))
        elif h in ["price", "rating", "strength", "volume"]:
            attributes.append((h, "NUMERIC"))
        elif h == "sweetness":
            attributes.append((h, ["dry", "semi-dry", "semi-sweet", "sweet"]))

    content["data"] = data

    arff_dic = {
        "attributes": attributes,
        "data": data,
        "relation": "Wines dataset",
    }

    with open(ARFF_FILE, "w") as file:
        arff.dump(
            arff_dic,
            file
        )

OUTPUT_CSV_FILE = "raw_dataframe.csv"


def to_csv(filename: str = "wines_dataset.arff") -> None:
    content = arff.load(open(filename, "r"))
    with open(OUTPUT_CSV_FILE, "w") as csvfile:
        writer = csv.writer(csvfile)
        header = []
        for n, t in content["attributes"]:
            header.append(n)

        print(header)

        writer.writerow(header)
        writer.writerows(content["data"])


def main():
    to_tsv()
    to_arff()
    to_csv()


if __name__ == "__main__":
    main()