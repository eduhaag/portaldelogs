import json
from pathlib import Path
from pymongo import MongoClient

STORE_PATH = Path(__file__).parent / "data" / "local_pattern_store.json"
MONGO_URL = "mongodb://root:root@localhost:27017/?authSource=admin"
DB_NAME = "log_analyzer"


def main() -> None:
    if not STORE_PATH.exists():
        print("No local fallback store found")
        return

    data = json.loads(STORE_PATH.read_text(encoding="utf-8"))
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]

    migrated = {}
    for name in ("custom_patterns", "non_error_patterns", "session_patterns"):
        count = 0
        for doc in data.get(name, []):
            item = dict(doc)
            item.pop("_id", None)
            key = {"id": item.get("id")} if item.get("id") else {
                "pattern": item.get("pattern"),
                "created_at": item.get("created_at"),
            }
            db[name].update_one(key, {"$set": item}, upsert=True)
            count += 1
        migrated[name] = count

    print(migrated)
    print(db.list_collection_names())


if __name__ == "__main__":
    main()
