import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ.get("DB_NAME", "log_analyzer")


def upsert_patterns(collection, patterns, source_label: str, code_field: bool = False):
    inserted = 0
    updated = 0
    now = datetime.now(timezone.utc).isoformat()

    for pattern_data in patterns:
        pattern_value = pattern_data.get("pattern", "")
        code_value = pattern_data.get("code") if code_field else None
        if not pattern_value and not code_value:
            continue

        document = dict(pattern_data)
        document.setdefault("id", str(uuid.uuid4()))
        document.setdefault("source", source_label)
        document.setdefault("active", True)
        document["updated_at"] = now

        query = {"code": code_value} if code_value else {"pattern": pattern_value}
        existing = collection.find_one(query)

        if existing:
            collection.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": document,
                    "$setOnInsert": {"created_at": now},
                },
            )
            updated += 1
        else:
            document.setdefault("created_at", now)
            collection.insert_one(document)
            inserted += 1

    return inserted, updated


def main() -> None:
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]

    logix_file = ROOT_DIR / "logix_erros.json"
    totvs_file = ROOT_DIR / "totvs_errors.json"

    logix_patterns = json.loads(logix_file.read_text(encoding="utf-8")) if logix_file.exists() else []
    totvs_patterns = json.loads(totvs_file.read_text(encoding="utf-8")) if totvs_file.exists() else []

    logix_inserted, logix_updated = upsert_patterns(db.logix_patterns, logix_patterns, "LOGIX JSON")
    totvs_inserted, totvs_updated = upsert_patterns(db.totvs_errors, totvs_patterns, "TOTVS JSON", code_field=True)

    db.logix_patterns.create_index("pattern")
    db.logix_patterns.create_index("active")
    db.totvs_errors.create_index("pattern")
    db.totvs_errors.create_index("code")
    db.totvs_errors.create_index("active")

    print(
        {
            "logix": {
                "inserted": logix_inserted,
                "updated": logix_updated,
                "total_active": db.logix_patterns.count_documents({"active": True}),
            },
            "totvs": {
                "inserted": totvs_inserted,
                "updated": totvs_updated,
                "total_active": db.totvs_errors.count_documents({"active": {"$ne": False}}),
            },
        }
    )


if __name__ == "__main__":
    main()
