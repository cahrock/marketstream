"""
MarketStream — SEC EDGAR Financial Statement Dataset ingestion.

Downloads a quarter's Financial Statement Dataset ZIP from SEC EDGAR and
uploads the raw file to S3 under a Hive-style partitioned path.

Usage:
    python jobs/ingest_edgar.py --year 2024 --quarter 1
    python jobs/ingest_edgar.py --year 2024 --quarter 1 --no-upload   # local test only

Requires env var:
    SEC_USER_AGENT  e.g. "MarketStream/0.1 multidevops@gmail.com"
Optional env var:
    MARKETSTREAM_BUCKET  (defaults to marketstream-data-302542863862)
"""

import argparse
import os
import sys
import time
from pathlib import Path

import boto3
import requests

SEC_BASE = "https://www.sec.gov/files/dera/data/financial-statement-data-sets"
DEFAULT_BUCKET = "marketstream-data-302542863862"
LOCAL_DIR = Path("sample_data")


def build_url(year: int, quarter: int) -> str:
    return f"{SEC_BASE}/{year}q{quarter}.zip"


def s3_key(year: int, quarter: int) -> str:
    # Hive-style partitioning so Athena/Spark auto-detect partitions later.
    return (
        f"raw/financial-statements/year={year}/quarter=Q{quarter}/"
        f"{year}q{quarter}.zip"
    )


def download(year: int, quarter: int, user_agent: str) -> Path:
    url = build_url(year, quarter)
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    dest = LOCAL_DIR / f"{year}q{quarter}.zip"

    print(f"Downloading {url}")
    # SEC requires a descriptive User-Agent with contact info, and rate-limits
    # to ~10 req/s. One request here, but we set the header correctly regardless.
    headers = {"User-Agent": user_agent}
    with requests.get(url, headers=headers, stream=True, timeout=60) as r:
        if r.status_code == 403:
            sys.exit(
                "403 Forbidden from SEC. Check your SEC_USER_AGENT header "
                "(must include contact info)."
            )
        if r.status_code == 404:
            sys.exit(
                f"404 Not Found: {url}\n"
                "That quarter may not be published yet, or the year/quarter is wrong."
            )
        r.raise_for_status()
        total = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):  # 1 MB chunks
                f.write(chunk)
                total += len(chunk)
        # be polite to SEC servers
        time.sleep(0.2)

    size_mb = dest.stat().st_size / (1024 * 1024)
    print(f"Downloaded {dest} ({size_mb:.1f} MB)")
    return dest


def upload(local_path: Path, year: int, quarter: int, bucket: str) -> None:
    key = s3_key(year, quarter)
    print(f"Uploading to s3://{bucket}/{key}")
    s3 = boto3.client("s3")
    s3.upload_file(str(local_path), bucket, key)
    print("Upload complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest SEC EDGAR financial statement datasets.")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--quarter", type=int, required=True, choices=[1, 2, 3, 4])
    parser.add_argument("--no-upload", action="store_true", help="Download only; skip S3 upload.")
    parser.add_argument("--bucket", default=os.environ.get("MARKETSTREAM_BUCKET", DEFAULT_BUCKET))
    args = parser.parse_args()

    user_agent = os.environ.get("SEC_USER_AGENT")
    if not user_agent:
        sys.exit("SEC_USER_AGENT env var is not set. See script docstring.")

    local_path = download(args.year, args.quarter, user_agent)

    if args.no_upload:
        print("--no-upload set; skipping S3. Local file retained for inspection.")
        return

    upload(local_path, args.year, args.quarter, args.bucket)


if __name__ == "__main__":
    main()