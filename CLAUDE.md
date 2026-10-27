# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

A lightweight shopping list web app (add / edit / delete / check items) built with Streamlit, targeting Streamlit Community Cloud. All four build stages in `PROMPTS.md` are done (skeleton → features → UI → Playwright review), and every issue found in the stage-4 review has been fixed and re-verified. The app is ready to deploy but is not in a git repository yet.

- `PRD.md` — source of truth for features (IDs F-01 to F-09), data model, UI wireframe, and non-functional requirements (each action ≤1s with 100 items; works at mobile width). Reference feature IDs when reporting.
- `PROMPTS.md` — the stage prompts. Their completion criteria double as the regression checklist.

The user communicates in Korean; respond in Korean.

## Commands

```bash
pip install -r requirements.txt
streamlit run app.py                                             # local dev
streamlit run app.py --server.headless true --server.port 8501   # for Playwright (run in background)
```

There is no test suite, linter, or build step. Verify by driving the running app with Playwright (see below), and test `storage.py` directly with Python. On Windows, set `PYTHONIOENCODING=utf-8` when printing Korean or emoji to the console, or `print` raises `UnicodeEncodeError` (cp949).

## Architecture

- `storage.py` — the only persistence layer, backed by `data/items.json` (gitignored). UI code must go through it only, so the backend can later be swapped (Google Sheets / Supabase) without touching `app.py`.
  - Every session (browser tab/device) shares one file, so **all changes go through `update_items(mutate)`**: it re-reads the file, applies `mutate(items) -> bool` in place, and saves when it returns True, all under a process-wide `RLock`. Never save a session's own copy of the list; that silently overwrites other tabs' changes.
  - `load_items()` returns `[]` for a missing or empty file. A corrupt or non-list file is renamed to `items.json.corrupt-<timestamp>` rather than overwritten. Duplicate ids are re-assigned and saved immediately, because duplicate ids crash the widget keys.
  - `save_items()` writes a `.tmp` file and then calls `os.replace`, retrying on Windows `PermissionError` (antivirus or indexer briefly holding the file).
  - `data_version()` is the file mtime; the UI uses it to detect external changes.
- `app.py` — single-page UI split into render functions (header, add form, undo bar, item list, footer actions).
  - `init_state()` reloads `st.session_state.shopping_items` from the file on **every** run. That list is render-only; never mutate it.
  - `sync_external_changes()` is an `st.fragment(run_every="2s")` that calls `st.rerun()` when `data_version()` differs from the version seen this run, so other tabs' changes appear without interaction. Unsubmitted input survives these reruns.
  - Deletes (single, clear-checked, clear-all) store `(original_index, item)` pairs in `last_deleted` for the "되돌리기" (undo) bar. Any other action clears it.
- Layout CSS lives in `CUSTOM_CSS` in `app.py`. Streamlit stacks `st.columns` vertically on narrow screens, so each row is wrapped in a keyed container (`add_row`, `row_{id}` / `row_done_{id}`, `editrow_{id}`, `undo_bar`, `footer`) and CSS targets the generated `.st-key-*` class with `:nth-child` column widths. Checked rows use the `row_done_` key prefix, which is what applies the strikethrough and muted color. If you add or reorder columns in a row, update the matching CSS. Row tap targets are kept at ≥40px for mobile. Theme colors are in `.streamlit/config.toml`, and theme changes need a server restart.
- Item shape: `{id: uuid4 str, name: str (1–50 chars, trimmed), quantity: int (1–99), checked: bool, created_at: ISO 8601 str}`.

## Streamlit rules that matter here

- Never name a session_state key `items` (or `keys`, `values`, `get`, etc.): `st.session_state.items` resolves to the dict-like `.items()` method, not the stored list. The list lives under `shopping_items`.
- Mutate data only in `on_click` / `on_change` callbacks, via `update_items()`, looking items up by `id` inside the mutator.
- Widget keys must be derived from the item `id` (`f"chk_{id}"`, `f"del_{id}"`), never from list index — index keys cause the wrong item to be checked/deleted after a rerun.
- Messages raised inside callbacks are stashed with `flash(level, msg)` and shown on the next render (`level` is an `st` function name: `warning`, `info`, `toast`).
- User-entered text must never be interpreted as markup:
  - Never use `unsafe_allow_html=True` for it. A `<style>` block is the only acceptable use.
  - Item names in rows are rendered with `st.text` (plain text) and strikethrough comes from CSS. Don't switch to `st.markdown`: backslash-escaping does not stop GFM auto-linking of bare URLs.
  - In markdown messages (toast, warning, undo bar), wrap names with `code(name)` (an inline code span), which renders literally.
  - The checkbox's hidden label intentionally gets the raw name, because it doubles as the screen-reader name and escaping would make readers speak backslashes.
- Don't use `max_chars`, `min_value`, or `max_value` on inputs. The browser silently discards out-of-range input: a pasted string over the limit is wiped, and a quantity of 100 is submitted as the default of 1. Validate server-side instead (`validate_name`, `clamp_qty`) and show a message.

## Verifying with Playwright

`streamlit.testing.v1.AppTest` misses frontend behavior (form clearing, markdown rendering, client-side input rejection), so check UI changes in a real browser:

- Wait for each rerun to finish before asserting: wait until `document.querySelector('[data-testid="stApp"]').dataset.testScriptState !== 'running'`. The 2s sync fragment also briefly sets it to `running`.
- Locate a row by its checkbox, whose `aria-label` is the raw item name: `[class*="st-key-row_"]` filtered with `has: getByRole('checkbox', {name, exact: true})`, then `.first()`, because a rerun can briefly leave two copies in the DOM. Click the row's `label` to toggle; clicking the hidden input is intercepted.
- Measure the visible name in a row's 2nd column. The first `stMarkdownContainer` in a row is the hidden checkbox label.
- The Playwright MCP can only write files under the project directory: save screenshots to `.playwright-mcp/` (gitignored).
- Seed test data by writing `data/items.json` directly. A new page load picks it up, and open pages pick it up via the sync fragment. Before testing, back up any real `data/items.json`, and restore it afterward.
- To check concurrency, open several pages (`page.context().newPage()`), and run threaded `update_items()` calls in Python.
- When the user asks for a review, report findings first and wait for approval before fixing.

## Deployment caveats

- The Streamlit Community Cloud filesystem is ephemeral: `data/items.json` is lost on app restart. This is an accepted v1 limitation (PRD v1.1 plans an external store).
- The `RLock` only serializes writes within one process. That is fine on Streamlit Community Cloud (single process), but running multiple server processes against the same file would need a file lock or a real database.
- `requirements.txt` pins `streamlit>=1.61,<2`; the app was only verified on 1.61.1 (it uses `st.fragment(run_every=)`, `st.container(key=)`, and `type="tertiary"`).
- A public deployment URL means every visitor shares and can edit the same list.
