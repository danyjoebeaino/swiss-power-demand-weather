"""Download MeteoSwiss daily station data (SwissMetNet) for the AnSeqDa project.

Run from the project root:
    python3 download_meteo.py

Files are saved to data/raw/meteo/. Source: MeteoSwiss (open data, must be cited).
"""
import json
import urllib.request
from pathlib import Path

STAC_ITEM = "https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn/items/{}"
META_PARAMS = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_parameters.csv"

# Zurich/Fluntern, Bern/Zollikofen, Geneve/Cointrin, Lugano
STATIONS = ["sma", "ber", "gve", "lug"]

OUT = Path("data/raw/meteo")
OUT.mkdir(parents=True, exist_ok=True)


def download(url: str, dest: Path) -> None:
    print(f"  -> {dest.name}")
    urllib.request.urlretrieve(url, dest)


for sta in STATIONS:
    print(f"Station {sta.upper()}")
    with urllib.request.urlopen(STAC_ITEM.format(sta)) as r:
        item = json.load(r)
    # keep only daily files ("_d_"): historical + recent
    for name, asset in item["assets"].items():
        if "_d_" in name and name.endswith(".csv") and "_now" not in name:
            download(asset["href"], OUT / name)

print("Parameter descriptions")
download(META_PARAMS, OUT / "ogd-smn_meta_parameters.csv")
print("Done.")