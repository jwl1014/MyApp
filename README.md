# 🛒 쇼핑 리스트

아이템 추가, 수정, 삭제, 체크 기능을 제공하는 가벼운 쇼핑 리스트 웹 앱입니다. (Python + Streamlit)

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 http://localhost:8501 로 접속합니다.

## 배포 (Streamlit Community Cloud)

1. 이 저장소를 GitHub에 push합니다.
2. https://share.streamlit.io 에 GitHub 계정으로 로그인합니다.
3. "New app"에서 저장소, 브랜치, 메인 파일(`app.py`)을 선택합니다.
4. Deploy를 누르면 `*.streamlit.app` URL이 발급됩니다.

> 데이터는 `data/items.json`에 저장됩니다. Streamlit Community Cloud에서는 앱이 재시작되면 이 파일이 초기화될 수 있습니다.

## 구조

- `app.py` — Streamlit UI
- `storage.py` — 데이터 로드/저장 (`load_items`, `save_items`, `new_item`)
- `PRD.md` — 요구사항 문서
