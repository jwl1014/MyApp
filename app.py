import streamlit as st

from storage import QTY_MAX, QTY_MIN, data_version, load_items, new_item, update_items

st.set_page_config(page_title="쇼핑 리스트", page_icon="🛒", layout="centered")

NAME_MAX_LEN = 50
SYNC_INTERVAL = "2s"  # 다른 탭/기기의 변경을 확인하는 주기

# Streamlit은 좁은 화면에서 columns를 세로로 쌓는다. 행 컨테이너의 key(st-key-* 클래스)로
# 대상을 좁혀 열 너비를 직접 지정해 모바일에서도 한 줄을 유지한다.
# 완료 항목의 행은 key가 row_done_* 이고, 이름의 취소선은 이 클래스로 입힌다.
CUSTOM_CSS = """
<style>
.block-container { padding-top: 2.5rem; max-width: 720px; }
h1 { padding-bottom: 0.25rem; }
@media (max-width: 400px) { h1 { font-size: 2rem !important; } }

/* 공통: 행 안의 columns는 줄바꿈 없이 가로 배치 */
.st-key-add_row [data-testid="stHorizontalBlock"],
[class*="st-key-row_"] [data-testid="stHorizontalBlock"],
.st-key-undo_bar [data-testid="stHorizontalBlock"],
.st-key-footer [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    align-items: center;
    gap: 0.5rem;
}
.st-key-add_row [data-testid="stColumn"],
[class*="st-key-row_"] [data-testid="stColumn"],
.st-key-undo_bar [data-testid="stColumn"],
.st-key-footer [data-testid="stColumn"] {
    min-width: 0 !important;
    width: auto !important;
}

/* 추가 폼: [품목명 | 수량 | 추가] */
.st-key-add_row [data-testid="stColumn"]:nth-child(1) { flex: 1 1 auto !important; }
.st-key-add_row [data-testid="stColumn"]:nth-child(2) { flex: 0 0 6.5rem !important; }
.st-key-add_row [data-testid="stColumn"]:nth-child(3) { flex: 0 0 auto !important; }

/* 아이템 행: [체크 | 이름 | 수량 | 수정 | 삭제] — 터치 영역은 최소 40px */
[class*="st-key-row_"] { padding: 0.15rem 0.5rem !important; gap: 0 !important; }
[class*="st-key-row_"] [data-testid="stColumn"]:nth-child(1) { flex: 0 0 2.5rem !important; }
[class*="st-key-row_"] [data-testid="stColumn"]:nth-child(2) { flex: 1 1 auto !important; }
[class*="st-key-row_"] [data-testid="stColumn"]:nth-child(3) { flex: 0 0 2.75rem !important; text-align: right; }
[class*="st-key-row_"] [data-testid="stColumn"]:nth-child(4),
[class*="st-key-row_"] [data-testid="stColumn"]:nth-child(5) { flex: 0 0 2.5rem !important; }
[class*="st-key-row_"] [data-testid="stText"] {
    font-family: inherit;
    font-size: 1rem;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}
[class*="st-key-row_done_"] [data-testid="stText"],
[class*="st-key-row_done_"] [data-testid="stText"] span { color: rgba(31, 42, 31, 0.45); }
[class*="st-key-row_done_"] [data-testid="stColumn"]:nth-child(2) [data-testid="stText"] { text-decoration: line-through; }
[class*="st-key-row_"] [data-testid="stCheckbox"] label {
    margin: 0;
    min-width: 2.5rem;
    min-height: 2.5rem;
    align-items: center;
    justify-content: center;
}
[class*="st-key-row_"] button { min-width: 2.5rem; min-height: 2.5rem; padding: 0.25rem; }

/* 편집 행: 좁은 화면에서는 이름 입력을 한 줄 전체로 */
[class*="st-key-editrow_"] [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; align-items: flex-end; gap: 0.5rem; }
[class*="st-key-editrow_"] [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 0 0 auto !important; }
[class*="st-key-editrow_"] [data-testid="stColumn"]:nth-child(1) { flex: 1 1 14rem !important; }
[class*="st-key-editrow_"] [data-testid="stColumn"]:nth-child(2) { flex: 0 0 7.5rem !important; }

.st-key-item_list { gap: 0.5rem; }

/* 삭제 되돌리기 바: [메시지 | 되돌리기] */
.st-key-undo_bar {
    background: #F1F7F1;
    border-radius: 0.5rem;
    padding: 0.25rem 0.5rem 0.25rem 0.75rem !important;
}
.st-key-undo_bar [data-testid="stColumn"]:nth-child(1) { flex: 1 1 auto !important; }
.st-key-undo_bar [data-testid="stColumn"]:nth-child(2) { flex: 0 0 auto !important; }
.st-key-undo_bar [data-testid="stMarkdownContainer"] p { margin: 0; overflow-wrap: anywhere; }
.st-key-undo_bar code { font-size: 0.95em; color: inherit; background: rgba(46, 125, 50, 0.12); padding: 0.1em 0.35em; }

/* 하단 버튼 */
.st-key-footer [data-testid="stColumn"] { flex: 1 1 0 !important; }
.st-key-footer [data-testid="stElementContainer"],
.st-key-footer [data-testid="stButton"],
.st-key-footer button { width: 100% !important; }
.st-key-clear_all button { color: #C62828; border-color: #EF9A9A; }
.st-key-clear_all button:hover { color: #FFFFFF; background: #C62828; border-color: #C62828; }
.st-key-confirm_clear_yes button { background: #C62828; border-color: #C62828; color: #FFFFFF; }
.st-key-confirm_clear_yes button:hover { background: #B71C1C; border-color: #B71C1C; }
</style>
"""


# ---------- 상태 / 헬퍼 ----------

def init_state() -> None:
    for key, default in (("editing_id", None), ("confirm_clear", False), ("flash", []), ("last_deleted", None)):
        if key not in st.session_state:
            st.session_state[key] = default

    # 매 실행마다 파일에서 새로 읽는다. 버전을 먼저 기록해, 읽는 사이에 바뀌면 다음 동기화 확인에서 다시 그린다.
    # 주의: session_state.items는 dict의 .items() 메서드와 충돌하므로 shopping_items를 사용한다.
    st.session_state.seen_version = data_version()
    st.session_state.shopping_items = load_items()

    # 다른 탭에서 지워진 항목을 편집 중이었다면 편집 모드를 해제한다
    if st.session_state.editing_id and find_item(items(), st.session_state.editing_id) is None:
        st.session_state.editing_id = None


def items() -> list[dict]:
    """이번 실행에서 읽은 목록 (렌더링용). 변경은 반드시 update_items()로 한다."""
    return st.session_state.shopping_items


def flash(level: str, message: str) -> None:
    """콜백에서 발생한 메시지를 다음 렌더링에서 표시하도록 저장한다."""
    st.session_state.flash.append((level, message))


def find_item(item_list: list[dict], item_id: str) -> dict | None:
    return next((item for item in item_list if item["id"] == item_id), None)


def normalize(name: str) -> str:
    return name.strip().casefold()


def code(text: str) -> str:
    """사용자 입력을 마크다운 인라인 코드로 감싼다. 코드 안은 링크·서식·수식이 해석되지 않는다."""
    longest, run = 0, 0
    for ch in text:
        run = run + 1 if ch == "`" else 0
        longest = max(longest, run)
    fence = "`" * (longest + 1)
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def validate_name(item_list: list[dict], name: str, exclude_id: str | None = None) -> str | None:
    """오류 메시지를 반환한다. 문제가 없으면 None."""
    if not name:
        return "품목명을 입력해 주세요."
    if len(name) > NAME_MAX_LEN:
        return f"품목명은 {NAME_MAX_LEN}자 이하로 입력해 주세요. (지금 {len(name)}자)"
    key = normalize(name)
    if any(normalize(item["name"]) == key and item["id"] != exclude_id for item in item_list):
        return f"{code(name)}은(는) 이미 리스트에 있어요."
    return None


def clamp_qty(value) -> tuple[int, bool]:
    """수량을 허용 범위로 맞춘다. (수량, 조정 여부)를 반환한다."""
    try:
        qty = int(value)
    except (TypeError, ValueError):
        return QTY_MIN, True
    clamped = max(QTY_MIN, min(QTY_MAX, qty))
    return clamped, clamped != qty


def flash_qty_adjusted(qty: int) -> None:
    flash("info", f"수량은 {QTY_MIN}~{QTY_MAX}개까지 입력할 수 있어서 {qty}개로 맞췄어요.")


# ---------- 콜백 ----------
# 모든 변경은 update_items()로 최신 파일 내용에 id 기준으로 적용한다.

def on_add() -> None:
    st.session_state.last_deleted = None
    name = st.session_state.add_name.strip()
    qty, adjusted = clamp_qty(st.session_state.add_qty)

    def mutate(item_list: list[dict]) -> bool:
        error = validate_name(item_list, name)
        if error:
            flash("warning", error)
            return False
        item_list.append(new_item(name, qty))
        return True

    if update_items(mutate):
        flash("toast", f"{code(name)} 추가했어요")
        if adjusted:
            flash_qty_adjusted(qty)


def on_toggle(item_id: str) -> None:
    st.session_state.last_deleted = None
    checked = st.session_state[f"chk_{item_id}"]

    def mutate(item_list: list[dict]) -> bool:
        item = find_item(item_list, item_id)
        if item is None or item["checked"] == checked:
            return False
        item["checked"] = checked
        return True

    update_items(mutate)


def on_start_edit(item_id: str) -> None:
    st.session_state.last_deleted = None
    item = find_item(load_items(), item_id)
    if item is None:
        flash("warning", "이미 삭제된 항목이에요.")
        return
    # 편집 위젯을 현재 값으로 채운다 (이전 편집에서 남은 값 제거)
    st.session_state[f"edit_name_{item_id}"] = item["name"]
    st.session_state[f"edit_qty_{item_id}"] = item["quantity"]
    st.session_state.editing_id = item_id


def on_save_edit(item_id: str) -> None:
    name = st.session_state[f"edit_name_{item_id}"].strip()
    qty, adjusted = clamp_qty(st.session_state[f"edit_qty_{item_id}"])
    outcome = []

    def mutate(item_list: list[dict]) -> bool:
        item = find_item(item_list, item_id)
        if item is None:
            outcome.append("missing")
            return False
        error = validate_name(item_list, name, exclude_id=item_id)
        if error:
            outcome.append(error)
            return False
        item["name"] = name
        item["quantity"] = qty
        return True

    update_items(mutate)
    if outcome == ["missing"]:
        flash("warning", "이미 삭제된 항목이에요.")
    elif outcome:
        flash("warning", outcome[0])
        return  # 편집 모드 유지
    elif adjusted:
        flash_qty_adjusted(qty)
    st.session_state.editing_id = None


def on_cancel_edit() -> None:
    st.session_state.editing_id = None


def remove_where(predicate) -> list[tuple[int, dict]]:
    """조건에 맞는 항목을 지우고, 되돌리기용으로 (원래 위치, 항목) 목록을 반환한다."""
    removed: list[tuple[int, dict]] = []

    def mutate(item_list: list[dict]) -> bool:
        removed.extend((i, item) for i, item in enumerate(item_list) if predicate(item))
        item_list[:] = [item for item in item_list if not predicate(item)]
        return bool(removed)

    update_items(mutate)
    if st.session_state.editing_id in {item["id"] for _, item in removed}:
        st.session_state.editing_id = None
    st.session_state.last_deleted = removed or None
    return removed


def on_delete(item_id: str) -> None:
    remove_where(lambda item: item["id"] == item_id)


def on_clear_checked() -> None:
    remove_where(lambda item: item["checked"])


def on_undo_delete() -> None:
    removed = st.session_state.last_deleted or []
    st.session_state.last_deleted = None
    skipped = []

    def mutate(item_list: list[dict]) -> bool:
        changed = False
        # 원래 위치가 작은 것부터 넣어야 순서가 복원된다
        for index, item in sorted(removed, key=lambda pair: pair[0]):
            if find_item(item_list, item["id"]) is not None:
                continue
            if validate_name(item_list, item["name"]) is not None:
                skipped.append(item["name"])
                continue
            item_list.insert(min(index, len(item_list)), item)
            changed = True
        return changed

    update_items(mutate)
    if skipped:
        flash("warning", f"같은 이름이 이미 있어서 되돌리지 못했어요: {', '.join(code(n) for n in skipped)}")


def on_request_clear_all() -> None:
    st.session_state.last_deleted = None
    st.session_state.confirm_clear = True


def on_confirm_clear_all() -> None:
    st.session_state.confirm_clear = False
    remove_where(lambda item: True)


def on_cancel_clear_all() -> None:
    st.session_state.confirm_clear = False


# ---------- 렌더링 ----------

def render_header() -> None:
    st.title("🛒 쇼핑 리스트")
    total = len(items())
    done = sum(1 for item in items() if item["checked"])
    st.caption(f"전체 {total}개 · 완료 {done}개")
    st.progress(done / total if total else 0.0)
    if total and done == total:
        st.success("장보기 완료! 🎉 체크된 항목을 정리해 보세요.")


def render_flash() -> None:
    for level, message in st.session_state.flash:
        getattr(st, level)(message)
    st.session_state.flash = []


def render_add_form() -> None:
    # max_chars / min_value / max_value는 쓰지 않는다. 브라우저 쪽에서 범위 밖 값을 조용히 버리기 때문에
    # (붙여넣은 긴 글이 통째로 사라지거나, 수량 100이 1로 저장됨) 서버에서 검증하고 안내한다.
    with st.form("add_form", clear_on_submit=True, border=False):
        with st.container(key="add_row"):
            name_col, qty_col, btn_col = st.columns([4, 1.2, 0.8], vertical_alignment="bottom")
            name_col.text_input("품목명", key="add_name", placeholder="예: 우유", label_visibility="collapsed")
            qty_col.number_input("수량", key="add_qty", value=1, step=1, label_visibility="collapsed")
            btn_col.form_submit_button("추가", type="primary", on_click=on_add)


def render_undo_bar() -> None:
    removed = st.session_state.last_deleted
    if not removed:
        return
    message = f"{code(removed[0][1]['name'])} 삭제했어요." if len(removed) == 1 else f"{len(removed)}개 항목을 삭제했어요."
    with st.container(key="undo_bar"):
        msg_col, btn_col = st.columns([4, 1], vertical_alignment="center")
        msg_col.markdown(message)
        btn_col.button("되돌리기", key="undo_delete", type="tertiary", on_click=on_undo_delete)


def render_edit_row(item: dict) -> None:
    item_id = item["id"]
    with st.container(key=f"editrow_{item_id}", border=True):
        name_col, qty_col, save_col, cancel_col = st.columns([4, 1.5, 1, 1], vertical_alignment="bottom")
        name_col.text_input("품목명 수정", key=f"edit_name_{item_id}")
        qty_col.number_input("수량", key=f"edit_qty_{item_id}", step=1)
        save_col.button("저장", key=f"save_{item_id}", type="primary", on_click=on_save_edit, args=(item_id,))
        cancel_col.button("취소", key=f"cancel_{item_id}", on_click=on_cancel_edit)


def render_item_row(item: dict) -> None:
    item_id = item["id"]
    if st.session_state.editing_id == item_id:
        render_edit_row(item)
        return

    # 체크 상태는 항상 저장된 데이터 기준으로 맞춘다
    st.session_state[f"chk_{item_id}"] = item["checked"]

    row_key = f"row_done_{item_id}" if item["checked"] else f"row_{item_id}"
    with st.container(key=row_key, border=True):
        chk_col, name_col, qty_col, edit_col, del_col = st.columns([0.6, 5, 1, 0.8, 0.8], vertical_alignment="center")
        # 라벨은 화면에 보이지 않고 스크린리더용 이름으로만 쓰인다
        chk_col.checkbox(
            item["name"],
            key=f"chk_{item_id}",
            on_change=on_toggle,
            args=(item_id,),
            label_visibility="collapsed",
        )
        # 이름은 마크다운이 아닌 일반 텍스트로 표시한다 (링크·서식·수식·URL 자동 링크가 생기지 않음)
        name_col.text(item["name"])
        qty_col.text(f"x{item['quantity']}")
        edit_col.button("✏️", key=f"edit_{item_id}", help="수정", type="tertiary", on_click=on_start_edit, args=(item_id,))
        del_col.button("🗑️", key=f"del_{item_id}", help="삭제", type="tertiary", on_click=on_delete, args=(item_id,))


def render_item_list() -> None:
    if not items():
        st.info("리스트가 비어 있어요. 살 물건을 추가해 보세요!", icon="🧺")
        return
    with st.container(key="item_list"):
        # 미완료 → 완료 순. sorted는 안정 정렬이라 그룹 안에서는 추가 순서가 유지된다.
        for item in sorted(items(), key=lambda item: item["checked"]):
            render_item_row(item)


def render_footer_actions() -> None:
    if not items():
        # 확인 창을 띄운 채 리스트가 비면, 다음에 항목을 추가했을 때 확인 창이 다시 나타나지 않도록 초기화
        st.session_state.confirm_clear = False
        return
    st.divider()

    with st.container(key="footer"):
        if st.session_state.confirm_clear:
            st.warning("정말 모든 항목을 삭제할까요?", icon="⚠️")
            yes_col, no_col = st.columns(2)
            yes_col.button("모두 삭제", key="confirm_clear_yes", type="primary", on_click=on_confirm_clear_all)
            no_col.button("취소", key="confirm_clear_no", on_click=on_cancel_clear_all)
            return

        has_checked = any(item["checked"] for item in items())
        left, right = st.columns(2)
        left.button("체크된 항목 지우기", key="clear_checked", disabled=not has_checked, on_click=on_clear_checked)
        right.button("🗑️ 전체 삭제", key="clear_all", on_click=on_request_clear_all)


@st.fragment(run_every=SYNC_INTERVAL)
def sync_external_changes() -> None:
    """다른 탭/기기가 파일을 바꿨으면 전체 화면을 다시 그린다."""
    if data_version() != st.session_state.seen_version:
        st.rerun()


def main() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    init_state()
    render_header()
    render_flash()
    render_add_form()
    render_undo_bar()
    render_item_list()
    render_footer_actions()
    sync_external_changes()


main()
