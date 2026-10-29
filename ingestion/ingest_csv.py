import argparse, hashlib, json, logging, os, shutil
from datetime import date, datetime

import pandas as pd
import yaml


def load_config(path="config/config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def ingest_source(name, cfg, run_date):
    src = os.path.join(cfg["source_dir"], cfg["sources"][name]["file"])
    if not os.path.exists(src):
        raise FileNotFoundError(f"Source file missing: {src}")

    dest_dir = os.path.join(cfg["bronze_dir"], name, f"ingestion_date={run_date}")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, os.path.basename(src))

    shutil.copy2(src, dest)  # raw copy, data is not modified

    # Row/column counts for the log only; the file itself is untouched
    df = pd.read_csv(dest)
    meta = {
        "source": name,
        "file": os.path.basename(src),
        "rows": len(df),
        "columns": list(df.columns),
        "md5": file_hash(dest),
        "ingested_at": datetime.now().isoformat(timespec="seconds"),
        "bronze_path": dest,
    }
    with open(os.path.join(dest_dir, "_metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    logging.info("OK %s | rows=%d | cols=%d | %s", name, meta["rows"], len(df.columns), dest)
    return meta


def main(run_date=None):
    cfg = load_config()
    run_date = run_date or date.today().isoformat()

    os.makedirs(os.path.dirname(cfg["log_file"]), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(cfg["log_file"]), logging.StreamHandler()],
    )

    logging.info("Ingestion started for run_date=%s", run_date)
    for name in cfg["sources"]:
        try:
            ingest_source(name, cfg, run_date)
        except Exception:
            logging.exception("FAILED %s", name)
            raise
    logging.info("Ingestion finished")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--run-date", default=None, help="YYYY-MM-DD (default: today)")
    main(p.parse_args().run_date)