import glob, logging, os, re
from datetime import date

import pandas as pd
import yaml

STATE_FIXES = {"Maharastra": "Maharashtra"}
NAME_FIXES = {"Santuary": "Sanctuary"}


def load_config(path="config/config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def latest_bronze(cfg, source, pattern):
    files = sorted(glob.glob(os.path.join(cfg["bronze_dir"], source, "ingestion_date=*", pattern)))
    if not files:
        raise FileNotFoundError(f"No Bronze file found for {source}")
    return files[-1]


def to_snake(col):
    return re.sub(r"\W+", "_", col.strip().lower()).strip("_")


def extract_year(text):
    t = str(text).strip()
    if re.fullmatch(r"-?\d+", t):
        return int(t)
    m = re.fullmatch(r"(\d{3,4})s", t)
    if m:
        return int(m.group(1))
    return None


def main(run_date=None):
    cfg = load_config()
    os.makedirs("logs", exist_ok=True)
    os.makedirs(cfg["silver_dir"], exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler("logs/transformation.log"), logging.StreamHandler()],
    )

    df = pd.read_csv(latest_bronze(cfg, "places", "*.csv"))
    rows_in = len(df)

    df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")])
    df.columns = [to_snake(c) for c in df.columns]

    for col in ["zone", "state", "city", "name", "type"]:
        df[col] = df[col].str.strip()

    df["state"] = df["state"].replace(STATE_FIXES)
    for wrong, right in NAME_FIXES.items():
        df["name"] = df["name"].str.replace(wrong, right, regex=False)

    df["establishment_year_raw"] = df["establishment_year"]
    df["establishment_year"] = df["establishment_year_raw"].apply(extract_year).astype("Int64")
    not_parsed = df.loc[df["establishment_year"].isna(), "establishment_year_raw"].unique()
    logging.info("places: establishment_year could not be read for: %s", list(not_parsed))

    df["weekly_off"] = df["weekly_off"].fillna("Not specified")
    df["is_goa"] = df["state"].eq("Goa")

    dupes = int(df.duplicated().sum())
    df = df.drop_duplicates()

    df.to_parquet(os.path.join(cfg["silver_dir"], "places_clean.parquet"), index=False)
    df[df["is_goa"]].to_parquet(os.path.join(cfg["silver_dir"], "places_goa.parquet"), index=False)
    logging.info("places: rows in=%d out=%d duplicates removed=%d goa rows=%d states=%d",
                 rows_in, len(df), dupes, df["is_goa"].sum(), df["state"].nunique())


if __name__ == "__main__":
    main()
