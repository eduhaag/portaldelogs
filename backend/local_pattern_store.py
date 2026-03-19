import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

STORE_PATH = Path(__file__).parent / "data" / "local_pattern_store.json"
COLLECTIONS = (
    "custom_patterns",
    "non_error_patterns",
    "session_patterns",
    "auth_users",
    "status_checks",
    "log_analysis",
    "analysis_changes",
    "issues",
)


def _default_store() -> Dict[str, List[Dict[str, Any]]]:
    return {name: [] for name in COLLECTIONS}


def _ensure_store_file() -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not STORE_PATH.exists():
        STORE_PATH.write_text(
            json.dumps(_default_store(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _load_store() -> Dict[str, List[Dict[str, Any]]]:
    _ensure_store_file()
    try:
        data = json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        data = _default_store()

    for collection in COLLECTIONS:
        values = data.get(collection, [])
        data[collection] = values if isinstance(values, list) else []

    return data


def _save_store(store: Dict[str, List[Dict[str, Any]]]) -> None:
    _ensure_store_file()
    STORE_PATH.write_text(
        json.dumps(store, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _matches_filters(item: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
    if not filters:
        return True

    for key, expected in filters.items():
        if item.get(key) != expected:
            return False

    return True


def _sort_records(records: List[Dict[str, Any]], sort_field: Optional[str], descending: bool) -> List[Dict[str, Any]]:
    if not sort_field:
        return records

    return sorted(
        records,
        key=lambda item: str(item.get(sort_field, "")),
        reverse=descending,
    )


def list_records(
    collection: str,
    filters: Optional[Dict[str, Any]] = None,
    sort_field: Optional[str] = None,
    descending: bool = False,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    store = _load_store()
    records = [
        deepcopy(item)
        for item in store.get(collection, [])
        if _matches_filters(item, filters)
    ]
    records = _sort_records(records, sort_field, descending)
    if limit is not None:
        records = records[:limit]
    return records


def find_record(
    collection: str,
    filters: Optional[Dict[str, Any]] = None,
    sort_field: Optional[str] = None,
    descending: bool = False,
) -> Optional[Dict[str, Any]]:
    records = list_records(
        collection,
        filters=filters,
        sort_field=sort_field,
        descending=descending,
        limit=1,
    )
    return records[0] if records else None


def insert_record(collection: str, record: Dict[str, Any]) -> Dict[str, Any]:
    store = _load_store()
    cloned = deepcopy(record)
    store.setdefault(collection, []).append(cloned)
    _save_store(store)
    return deepcopy(cloned)


def update_records(collection: str, filters: Dict[str, Any], updates: Dict[str, Any]) -> int:
    store = _load_store()
    count = 0

    for item in store.get(collection, []):
        if _matches_filters(item, filters):
            item.update(deepcopy(updates))
            count += 1

    if count:
        _save_store(store)

    return count


def delete_records(collection: str, filters: Dict[str, Any], limit: Optional[int] = None) -> int:
    store = _load_store()
    original_records = store.get(collection, [])
    kept_records: List[Dict[str, Any]] = []
    deleted_count = 0

    for item in original_records:
        should_delete = _matches_filters(item, filters) and (limit is None or deleted_count < limit)
        if should_delete:
            deleted_count += 1
            continue
        kept_records.append(item)

    if deleted_count:
        store[collection] = kept_records
        _save_store(store)

    return deleted_count
