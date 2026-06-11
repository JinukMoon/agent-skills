"""공용 설정 — 테니스장 예약 자동화."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.join(BASE_DIR, "browser_profile")  # 헤드 로그인용 프로필 (MFA bypass 쿠키)
STATE_FILE = os.path.join(BASE_DIR, "state.json")  # 세션 쿠키 백업 (storage_state)

SITE = "https://athletics.snu.ac.kr"
LIST_URL = f"{SITE}/facility/list?sc=y&facility_category_idx=5&court_type=grass"
LOGIN_URL = f"{SITE}/member/login"

# 동반 이용자 명단 — 개인정보(PII)는 코드/skill에 넣지 않는다.
# 각 컴퓨터의 로컬 파일 members.local.json 에 저장하고 거기서 읽는다.
# 본인(로그인 계정)은 사이트가 자동으로 채우므로, 여기엔 '동반자'만 둔다.
# 형식: [{"name": "...", "userno": "...", "mobile": "...", "dept": "..."}, ...]
MEMBERS_FILE = os.path.join(BASE_DIR, "members.local.json")


def load_members():
    """members.local.json 에서 동반자 명단을 읽는다. 파일 없으면 [] (첫 사용 설정 필요)."""
    if not os.path.exists(MEMBERS_FILE):
        return []
    import json
    with open(MEMBERS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return [(m["name"], m["userno"], m["mobile"], m.get("dept", "")) for m in data]


# 모듈 로드 시 1회 읽음 (각 스크립트 실행은 새 프로세스라 매번 최신값)
MEMBERS = load_members()

# 우선순위 목록 파일
TARGETS_FILE = os.path.join(BASE_DIR, "targets.txt")

# 한글 요일 → Python weekday (월=0 ... 일=6)
_WEEKDAY = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}
_WEEKDAY_KR = {v: k for k, v in _WEEKDAY.items()}


def parse_targets(path=None):
    """targets.txt → [(표시, py_weekday|None, 날짜|None, 시작시, 종료시), ...] 우선순위 순.

    각 줄 형식 (둘 다 허용):
      '토 20-22'            요일 지정 → 열린 날짜 중 그 요일을 자동 매칭
      '2026-06-20 14-16'   날짜 직접 지정 (정확)
      '06-20 14-16'        날짜 직접 지정 (올해 기준)
    """
    import re as _re
    import datetime as _dt
    path = path or TARGETS_FILE
    targets = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 2:
                raise ValueError(f"형식 오류: {raw!r} (예: '토 20-22' 또는 '06-20 14-16')")
            head, trange = parts
            s, e = trange.split("-")
            s, e = int(s), int(e)

            py_wd, date = None, None
            if _re.fullmatch(r"\d{4}-\d{2}-\d{2}", head):
                date = head
            elif _re.fullmatch(r"\d{1,2}-\d{1,2}", head):
                mm, dd = head.split("-")
                year = _dt.date.today().year
                date = f"{year}-{int(mm):02d}-{int(dd):02d}"
            elif head in _WEEKDAY:
                py_wd = _WEEKDAY[head]
            else:
                raise ValueError(f"요일/날짜 오류: {head!r} (예: '토' 또는 '06-20')")

            display = date if date else head
            targets.append((display, py_wd, date, s, e))
    return targets


def weekday_kr(date_str):
    """'2026-06-20' → '토'."""
    import datetime as _dt
    d = _dt.date.fromisoformat(date_str)
    return _WEEKDAY_KR[d.weekday()]


def launch(p, headless=True):
    """저장된 프로필로 persistent context 실행 (헤드 로그인용)."""
    return p.chromium.launch_persistent_context(
        PROFILE_DIR,
        headless=headless,
        viewport={"width": 1400, "height": 900},
        locale="ko-KR",
    )


def launch_with_state(p, headless=True):
    """state.json의 세션 쿠키를 주입한 일반 context 실행 (무인 작업용).

    반환: (browser, context) — 둘 다 닫아야 함.
    """
    if not os.path.exists(STATE_FILE):
        raise FileNotFoundError("state.json 없음 — run.sh login 을 먼저 실행하세요")
    browser = p.chromium.launch(headless=headless)
    ctx = browser.new_context(
        storage_state=STATE_FILE,
        viewport={"width": 1400, "height": 900},
        locale="ko-KR",
    )
    return browser, ctx


def save_state(ctx):
    """현재 세션 쿠키를 state.json으로 백업 (세션 쿠키 포함)."""
    ctx.storage_state(path=STATE_FILE)


def is_logged_in(page):
    """로그인 상태 정확 판정 — 로그아웃 링크(/mypage/logout) 존재 여부로 판단.

    목록 페이지에는 로그아웃 상태에서도 /mypage 링크가 있으므로
    그것으로 판단하면 오탐이 난다. 로그아웃 링크만이 확실한 신호다.
    (이 사이트의 로그아웃 경로는 /mypage/logout)
    """
    return page.locator("a[href*='logout']").count() > 0
