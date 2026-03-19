import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

from datasul_hybrid_loader import DatasulHybridLoader

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ.get("DB_NAME", "log_analyzer")


def severity_to_priority(severity: str) -> int:
    return {
        "Crítico": 5,
        "Alto": 4,
        "Médio": 3,
        "Baixo": 2,
        "Informativo": 1,
    }.get(severity, 3)


def main() -> None:
    loader = DatasulHybridLoader()
    patterns = loader.get_all_patterns()

    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]

    inserted = 0
    updated = 0
    now = datetime.now(timezone.utc).isoformat()

    for pattern_data in patterns:
        pattern = pattern_data.get("pattern", "")
        if not pattern:
            continue

        document = {
            "id": pattern_data.get("id") or str(uuid.uuid4()),
            "pattern": pattern,
            "description": pattern_data.get("description", ""),
            "category": pattern_data.get("category", "Geral"),
            "severity": pattern_data.get("severity", "Médio"),
            "example": pattern_data.get("example", ""),
            "solution": pattern_data.get("solution", ""),
            "tag": pattern_data.get("tag", "Datasul"),
            "source": pattern_data.get("source", "hybrid_datasul_loader"),
            "active": True,
            "updated_at": now,
            "priority": pattern_data.get("priority", severity_to_priority(pattern_data.get("severity", "Médio"))),
            "regex_valid": True,
            "metadata": pattern_data.get("metadata", {}),
        }

        existing = db.datasul_patterns.find_one({"pattern": pattern})
        if existing:
            db.datasul_patterns.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": document,
                    "$setOnInsert": {"created_at": now},
                },
            )
            updated += 1
        else:
            document["created_at"] = now
            db.datasul_patterns.insert_one(document)
            inserted += 1

    db.datasul_patterns.create_index("pattern")
    db.datasul_patterns.create_index("category")
    db.datasul_patterns.create_index("tag")
    db.datasul_patterns.create_index("severity")
    db.datasul_patterns.create_index("active")
    db.datasul_patterns.create_index([("active", 1), ("priority", -1)])

    total = db.datasul_patterns.count_documents({"active": True})
    print({
        "inserted": inserted,
        "updated": updated,
        "total_active": total,
    })


if __name__ == "__main__":
    main()
