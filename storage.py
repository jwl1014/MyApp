"""쇼핑 리스트 데이터 저장 계층.

UI 코드는 이 모듈의 공개 함수만 사용한다. 저장 방식을 외부 저장소로 바꿀 때는 이 파일만 수정하면 된다.

여러 탭/기기(=여러 Streamlit 세션)가 같은 파일을 쓰므로, 변경은 항상 update_items()로
"파일에서 읽기 → 수정 → 저장"을 락 안에서 한 번에 처리한다. 세션별 사본으로 파일 전체를
덮어쓰면 다른 세션의 변경이 사라진다.
"""

import json
import os
import threading
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "items.json"
QTY_MIN, QTY_MAX = 1, 99

# 같은 프로세스의 모든 세션이 공유한다. load_items가 복구 저장을 하므로 재진입 가능한 RLock을 쓴다.
_lock = threading.RLock()
_REPLACE_RETRIES = 20


def data_version() -> int:
    """파일이 바뀌었는지 확인하기 위한 값 (수정 시각, 나노초). 파일이 없으면 0."""
    try:
        return DATA_FILE.stat().st_mtime_ns
    except OSError:
        return 0


def load_items() -> list[dict]:
    """저장된 아이템을 불러온다. 파일이 없거나 비었거나 깨져 있으면 빈 리스트를 반환한다."""
    with _lock:
        try:
            text = DATA_FILE.read_text(encoding="utf-8")
        except OSError:
            return []

        if not text.strip():
            return []

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            _quarantine()
            return []
        if not isinstance(data, list):
            _quarantine()
            return []

        items, seen_ids, repaired = [], set(), False
        for raw in data:
            item = _normalize(raw)
            if item is None:
                continue
            if item["id"] in seen_ids:
                # 중복 id는 위젯 key 충돌로 앱을 멈추게 하므로 새 id를 부여하고 바로 저장한다
                item["id"] = str(uuid.uuid4())
                repaired = True
            seen_ids.add(item["id"])
            items.append(item)

        if repaired:
            save_items(items)
        return items


def save_items(items: list[dict]) -> None:
    """아이템 목록을 JSON 파일로 저장한다. 임시 파일에 쓴 뒤 교체해 저장 도중 중단돼도 파일이 깨지지 않는다."""
    with _lock:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = DATA_FILE.with_name(DATA_FILE.name + ".tmp")
        tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        # Windows에서는 백신/검색 색인이 방금 쓴 파일을 잠깐 열고 있으면 교체가 거부된다. 잠시 후 재시도한다.
        for attempt in range(_REPLACE_RETRIES):
            try:
                os.replace(tmp, DATA_FILE)
                return
            except PermissionError:
                if attempt == _REPLACE_RETRIES - 1:
                    raise
                time.sleep(0.05)


def update_items(mutate: Callable[[list[dict]], bool]) -> bool:
    """최신 목록을 읽어 mutate(items)로 제자리 수정하고, True를 반환하면 저장한다. 저장 여부를 반환한다."""
    with _lock:
        items = load_items()
        changed = mutate(items)
        if changed:
            save_items(items)
        return changed


def new_item(name: str, quantity: int = 1) -> dict:
    """새 아이템을 생성한다."""
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "quantity": quantity,
        "checked": False,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def _quarantine() -> None:
    """읽을 수 없는 파일을 지우지 않고 옆에 보관한다 (다음 저장 때 덮어써져 복구 불가능해지는 것을 방지)."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    try:
        DATA_FILE.rename(DATA_FILE.with_name(f"{DATA_FILE.name}.corrupt-{stamp}"))
    except OSError:
        pass


def _normalize(raw) -> dict | None:
    """저장된 아이템을 검증한다. id나 name이 없으면 버리고, 나머지 필드는 기본값으로 채운다."""
    if not isinstance(raw, dict):
        return None
    item_id, name = raw.get("id"), raw.get("name")
    if not isinstance(item_id, str) or not isinstance(name, str) or not name.strip():
        return None
    quantity = raw.get("quantity")
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        quantity = QTY_MIN
    return {
        "id": item_id,
        "name": name.strip(),
        "quantity": max(QTY_MIN, min(QTY_MAX, quantity)),
        "checked": raw.get("checked") is True,
        "created_at": raw.get("created_at") if isinstance(raw.get("created_at"), str) else "",
    }
