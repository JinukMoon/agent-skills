"""테니스장 예약 자동 제출 — 날짜·시간 우선순위 목록 방식 (timelist 고속 스캔).

targets.txt 의 우선순위를 위에서부터 시도한다. 각 항목(요일+시간)에 대해
잔디코트 1~14 중 빈 코트를 자동으로 잡고, 성공하면 즉시 종료한다.

★ 안전 규칙 (절대 어기지 않음):
  - 다음 우선순위로 넘어가는 경우는 **그 날짜·시간대 14개 코트가 모두 확실히 매진**일 때뿐.
  - 예약 성공은 사이트의 결과 페이지 리다이렉트로 **검증**된 뒤에만 종료로 인정.
  - 빈 코트가 있는데 실패하면 절대 advance 하지 않는다:
      · 누가 먼저 채감(race) → 다른 빈 코트로 재시도
      · 진짜 오류(error)가 반복 → 멈추고 사용자에게 알림 (잘못된 advance보다 멈춤이 안전)

빈자리 탐지는 가벼운 timelist JSON(~2KB)으로, 실제 폼 로드는 빈 코트에만.

사용:
  ./run.sh reserve -- --dry                   # 지금 열린 날짜로 제출 직전까지 테스트
  ./run.sh reserve -- --now                   # 즉시 실제 제출
  ./run.sh reserve -- --fill                  # 채우기만 하고 대기 (제출은 직접)
  ./run.sh reserve -- --fire 09:30:00         # 정각 발사 후 자동 제출
"""

import argparse
import datetime
import re
import sys
import time

from playwright.sync_api import sync_playwright

import common

# 잔디코트 1~14 → facility_idx = 코트번호 + 2
COURTS = list(range(1, 15))

# 빈 코트가 있는데도 예약이 반복 실패할 때, 이 횟수를 넘으면 멈추고 알린다.
ERROR_BUDGET = 3


def court_to_idx(court_no):
    return court_no + 2


def log(msg):
    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{now}] {msg}", flush=True)


def wait_until(t_target):
    while True:
        remain = (t_target - datetime.datetime.now()).total_seconds()
        if remain <= 0:
            return
        time.sleep(min(remain, 0.2))


def server_offset(samples=5):
    """서버시간 - 로컬시간 (초). 양수=서버가 로컬보다 앞.
    athletics 응답의 HTTP Date 헤더 기반 (초단위 해상도라 ±1s 노이즈 → median)."""
    import urllib.request
    import email.utils
    offs = []
    for _ in range(samples):
        try:
            t0 = time.time()
            r = urllib.request.urlopen(
                urllib.request.Request(common.SITE + "/", method="HEAD"), timeout=8)
            t1 = time.time()
            d = r.headers.get("Date")
            if d:
                se = email.utils.parsedate_to_datetime(d).timestamp()
                offs.append(se - (t0 + t1) / 2)
        except Exception:
            pass
        time.sleep(0.25)
    if not offs:
        return 0.0
    offs.sort()
    return offs[len(offs) // 2]


# ───────────────────────── 고속 빈자리 탐지 (timelist JSON) ─────────────────────────

def timelist(req, facility_idx, date):
    """timelist JSON으로 시간별 사용여부를 가져온다. 반환: {시작시: used(bool)} 또는 None(실패)."""
    url = (f"{common.SITE}/facility/reservation"
           f"?mode=timelist&facility_idx={facility_idx}&date={date}")
    try:
        r = req.get(url, timeout=10000)
        if not r.ok:
            return None
        data = r.json()
        if data.get("errcode"):
            return None
        out = {}
        for slot in data.get("datalist", []):
            h = int(slot["stime"][:2])
            out[h] = (slot.get("used") == "y")
        return out
    except Exception:
        return None


def court_slot_status(req, court, date, stime, etime):
    """[stime, etime) 구간에 대해 'free' | 'taken' | 'unknown' 반환."""
    tl = timelist(req, court_to_idx(court), date)
    if tl is None:
        return "unknown"
    statuses = [tl.get(h) for h in range(stime, etime)]
    if any(s is None for s in statuses):
        # 그 시간대 슬롯이 목록에 없음 = 날짜 미오픈/범위밖
        return "unknown"
    if all(s is False for s in statuses):
        return "free"
    return "taken"


def scan_courts(req, date, stime, etime):
    """14개 코트를 timelist로 스캔. 반환: (free[], taken[], unknown[])."""
    free, taken, unknown = [], [], []
    for c in COURTS:
        st = court_slot_status(req, c, date, stime, etime)
        (free if st == "free" else taken if st == "taken" else unknown).append(c)
    return free, taken, unknown


# ───────────────────────── 폼 채우기 (빈 코트에만 무거운 폼 로드) ─────────────────────────

def prepare_form(page, facility_idx, date, time_range, verbose=False):
    """폼 입력 — 제출 직전까지 완료. 반환: 'ok' | 'closed' | 'taken' | 'error'."""
    stime, etime = time_range
    url = (f"{common.SITE}/facility/reservation"
           f"?mode=form&facility_idx={facility_idx}&date={date}")

    def _d(dialog):
        dialog.accept()

    page.on("dialog", _d)
    try:
        page.goto(url, timeout=30000)
        page.wait_for_load_state("domcontentloaded")
    finally:
        page.remove_listener("dialog", _d)

    if page.locator("#dataform").count() == 0 or page.locator("#sTime").count() == 0:
        return "closed"

    s_label = f"{stime:02d}시 00분"
    e_label = f"{etime:02d}시 00분"
    try:
        page.select_option("#sTime", label=s_label)
        page.select_option("#eTime", label=e_label)
    except Exception:
        return "error"

    used = page.evaluate("""([s,e]) => {
        const so = [...document.querySelectorAll('#sTime option')];
        const sseq = parseInt(so.find(o=>o.textContent.trim()===s)?.dataset.sequence);
        const eseq = parseInt([...document.querySelectorAll('#eTime option')]
                       .find(o=>o.textContent.trim()===e)?.dataset.sequence);
        let used = false;
        so.forEach(o => {
            const q = parseInt(o.dataset.sequence);
            if (q >= sseq && q <= eseq && o.dataset.used === 'y') used = true;
        });
        return used;
    }""", [s_label, e_label])
    if used:
        return "taken"

    need_rows = 1 + len(common.MEMBERS)
    for _ in range(need_rows - 2):
        page.click("#btn-add-member")
        time.sleep(0.05)

    for i, (name, userno, mobile, dept) in enumerate(common.MEMBERS, start=2):
        page.fill(f"#member_name{i}", name)
        page.fill(f"#member_userno{i}", userno)
        page.fill(f"#member_mobile{i}", mobile)
        page.fill(f"#member_department{i}", dept)

    # 멤버 인증 — 실패 dialog를 잡아 원인을 즉시 구분 (1인1일1예약 규칙 등)
    auth_msgs = []

    def _auth_dialog(d):
        auth_msgs.append(d.message)
        d.accept()

    page.on("dialog", _auth_dialog)
    try:
        for i in range(1, need_rows + 1):
            btn = page.locator(f".btn-check-attendance[data-idx='{i}']")
            if btn.count() == 0:
                continue
            auth_msgs.clear()
            btn.click()
            ok_auth = False
            for _ in range(80):  # 최대 ~8초, 단 실패 dialog 뜨면 즉시 탈출
                if page.evaluate(
                        f"document.querySelector('#member_check{i}').value === '1'"):
                    ok_auth = True
                    break
                if auth_msgs:
                    break
                page.wait_for_timeout(100)
            if not ok_auth:
                joined = " ".join(auth_msgs)
                # '유사 시설에 이미 등록/예약' = 그 날짜는 이 멤버로 불가 (1일1예약)
                if "유사 시설" in joined or "등록할 수 없습니다" in joined:
                    return "conflict"
                return "error"
    finally:
        page.remove_listener("dialog", _auth_dialog)

    page.evaluate("""() => {
        for (const id of ['oath','privacy']) {
            const el = document.querySelector('#'+id);
            if (el && !el.checked) {
                el.checked = true;
                el.dispatchEvent(new Event('change', {bubbles:true}));
            }
        }
    }""")

    m = re.search(r'let\s+token\s*=\s*"([0-9a-f]+)"', page.content())
    if not m:
        return "error"
    page.evaluate(
        """t => {
            document.querySelector('#csrftoken').value = t;
            const b = document.querySelector('#btn-human');
            if (b) { b.classList.remove('btn-outline-danger');
                     b.classList.add('btn-outline-success');
                     b.setAttribute('disabled','disabled'); }
        }""", m.group(1))
    return "ok"


def recaptcha_ok(page):
    v = page.evaluate(
        "() => (document.querySelector('#g-recaptcha-response')||{}).value || ''")
    return len(v) > 0


def solve_recaptcha(page, timeout_s=120):
    if recaptcha_ok(page):
        return True
    try:
        frame = page.frame_locator("iframe[src*='recaptcha/api2/anchor']")
        frame.locator("#recaptcha-anchor").click(timeout=5000)
        log("  reCAPTCHA 체크박스 클릭")
    except Exception as e:
        log(f"  reCAPTCHA 클릭 실패: {e}")

    deadline = time.time() + timeout_s
    warned = False
    while time.time() < deadline:
        if recaptcha_ok(page):
            log("  reCAPTCHA 통과")
            return True
        if not warned:
            log("  >>> 이미지 챌린지가 떴다면 브라우저 창에서 직접 풀어주세요 <<<")
            warned = True
        time.sleep(0.5)
    return False


def submit(page):
    """제출 + confirm/alert 처리. 성공(결과페이지 리다이렉트) 시 (True, msgs)."""
    msgs = []

    def on_dialog(dialog):
        msgs.append(dialog.message)
        dialog.accept()

    page.on("dialog", on_dialog)
    try:
        page.click("#btn-reservation-ajax")
        try:
            page.wait_for_url("**/mypage?mode=result**", timeout=20000)
            return True, msgs
        except Exception:
            time.sleep(1.5)
            return False, msgs
    finally:
        page.remove_listener("dialog", on_dialog)


def attempt_book(page, req, court, date, stime, etime, args):
    """한 코트에 예약 시도. 반환:
       'success' | 'race'(누가 채감) | 'error'(예상밖 실패)
       | 'conflict'(1일1예약 등 멤버가 그날 이미 예약) | 'dry' | 'fill'
    """
    st = prepare_form(page, court_to_idx(court), date, (stime, etime))
    if st == "taken":
        return "race"
    if st == "conflict":
        return "conflict"
    if st == "closed":
        # timelist는 비었다 했는데 폼이 없다 = 예상밖
        return "error"
    if st == "error":
        return "error"

    # st == 'ok'
    log(f"  ★ 빈 코트 잡음: 잔디코트 {court} ({date} {stime}-{etime}시) — 폼 준비 완료")
    if args.dry:
        return "dry"
    if not solve_recaptcha(page):
        return "error"
    if args.fill:
        return "fill"

    ok, msgs = submit(page)
    if ok:
        return "success"

    # 제출 실패 — race인지 error인지 timelist로 재판정
    status = court_slot_status(req, court, date, stime, etime)
    if status == "taken":
        log(f"  (잔디코트 {court} 제출 실패: 직전에 누가 채감) msgs={msgs}")
        return "race"
    log(f"  (잔디코트 {court} 제출 실패: 빈데도 실패 msgs={msgs})")
    return "error"


def alert_stop(ctx, browser, msg):
    log("=" * 50)
    log(f"⚠️  멈춤: {msg}")
    log("⚠️  안전을 위해 다음 우선순위로 넘어가지 않고 중단합니다.")
    log("⚠️  창을 확인하시고, 필요하면 직접 예약하거나 다시 실행하세요.")
    log("=" * 50)
    # 사용자가 창을 확인할 수 있게 잠시 유지
    time.sleep(120)
    ctx.close(); browser.close()
    sys.exit(3)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--now", action="store_true", help="즉시 제출")
    g.add_argument("--fill", action="store_true", help="채우기만 하고 대기")
    g.add_argument("--dry", action="store_true", help="제출 직전까지만 (테스트)")
    ap.add_argument("--fire", help="제출 시각 HH:MM:SS")
    ap.add_argument("--targets", help="우선순위 목록 파일", default=None)
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args()

    if not common.MEMBERS:
        log("동반자 미설정 — members.local.json 이 없습니다.")
        log("첫 사용 설정이 필요합니다: 같이 칠 동반자 1명의 이름/학번/전화번호/학과를")
        log(f"  {common.MEMBERS_FILE}")
        log("에 저장하세요. (이 파일은 이 컴퓨터에만 저장되며 공유되지 않습니다.)")
        sys.exit(2)

    targets = common.parse_targets(args.targets)
    if not targets:
        log("targets.txt 에 목록이 없습니다.")
        sys.exit(2)

    log("=== 우선순위 목록 ===")
    for n, (disp, _wd, _date, s, e) in enumerate(targets, 1):
        log(f"  {n}. {disp} {s}-{e}시")

    fire_at = None
    if args.fire:
        h, m_, s = map(int, args.fire.split(":"))
        fire_at = datetime.datetime.combine(
            datetime.date.today(), datetime.time(h, m_, s))
        if fire_at < datetime.datetime.now():
            log("발사 시각이 지남 — 즉시 모드")
            fire_at = None

    with sync_playwright() as p:
        browser, ctx = common.launch_with_state(p, headless=args.headless)
        req = ctx.request
        page = ctx.new_page()

        page.goto(common.LIST_URL, timeout=30000)
        page.wait_for_load_state("domcontentloaded")
        if not common.is_logged_in(page):
            log("FATAL: 세션 만료 — ./run.sh login 후 재실행")
            sys.exit(2)
        log("세션 유효")

        if fire_at:
            off = server_offset()
            log(f"서버시간 오프셋 {off:+.2f}초 (양수=서버가 로컬보다 앞)")

            def srv_now():
                return datetime.datetime.now() + datetime.timedelta(seconds=off)

            log(f"발사(서버시간 기준) {fire_at.strftime('%H:%M:%S')} — 5초 전부터 카운트다운")
            last_log = 0.0
            while srv_now() < fire_at:
                rem = (fire_at - srv_now()).total_seconds()
                if rem <= 5 and time.time() - last_log >= 0.5:
                    log(f"  서버 {srv_now().strftime('%H:%M:%S.%f')[:-3]}  (D-{rem:0.1f}s)")
                    last_log = time.time()
                time.sleep(0.02)
            log(f">>> 발사! (서버시간 {srv_now().strftime('%H:%M:%S.%f')[:-3]}) <<<")

        # 발사 후: 우선순위에 '명시된 날짜'가 실제로 열릴 때까지 폴링 (fire 모드).
        # 9:30에 다음 주가 열리는 '바로 그 순간'을 잡기 위함. 이번 주 날짜는 항상
        # 들어있으므로 "날짜 목록이 비었나"로 판단하면 안 되고, 타겟 날짜 출현을 봐야 한다.
        # 이미 열린 날짜면 즉시 통과. (날짜 미지정 요일-타겟은 한 번만 조회.)
        want_dates = [t[2] for t in targets if t[2]]  # 명시 날짜들 (MM-DD/풀날짜)
        open_deadline = time.time() + (90 if fire_at else 0)
        open_dates = get_open_dates(req)
        if fire_at and want_dates:
            polls = 0
            while not all(d in open_dates for d in want_dates) and time.time() < open_deadline:
                time.sleep(0.15)
                open_dates = get_open_dates(req)
                polls += 1
            log(f"날짜 오픈 폴링 {polls}회")
        log(f"열린 날짜: {open_dates}")
        missing = [d for d in want_dates if d not in open_dates]
        if missing:
            log(f"⚠️ 발사 후에도 안 열린 명시 날짜: {missing} (그래도 진행)")

        # 한 날짜·시간대에서 빈 코트 하나 확보 (멀티 예약의 단위 동작)
        def secure_one(date, stime, etime):
            """반환: ('booked'|'dry'|'fill', court) | 'full' | 'conflict'.
            'conflict' = 멤버가 그날 이미 예약(1일1예약 등) → 그 날짜는 어떤 코트도 불가.
            빈 코트가 있는데 반복 실패하면 alert_stop으로 중단(잘못된 건너뜀 방지)."""
            errors = 0
            while True:
                free, taken, unknown = scan_courts(req, date, stime, etime)
                log(f"  스캔: 빈코트={free} 매진={len(taken)} 불명={unknown}")
                if not free:
                    if not unknown:
                        return "full"  # ★ 14개 모두 확실히 매진 — 정당한 '넘어감' 사유
                    errors += 1
                    if errors > ERROR_BUDGET:
                        alert_stop(ctx, browser,
                                   f"{date} {stime}-{etime}시 스캔 불안정(불명 {unknown}). "
                                   f"매진 단정 불가.")
                    time.sleep(0.3)
                    continue
                for court in free:
                    outcome = attempt_book(page, req, court, date, stime, etime, args)
                    if outcome == "success":
                        return ("booked", court)
                    if outcome == "dry":
                        return ("dry", court)
                    if outcome == "fill":
                        return ("fill", court)
                    if outcome == "conflict":
                        # 멤버가 그날 이미 예약 → 코트 더 볼 필요 없음, 즉시 알림
                        return "conflict"
                    # race(누가 채감) / error → 다음 빈 코트 시도
                errors += 1
                if errors > ERROR_BUDGET:
                    alert_stop(ctx, browser,
                               f"{date} {stime}-{etime}시: 빈 코트가 있는데 예약 "
                               f"{ERROR_BUDGET}회 연속 실패. 잘못된 건너뜀 방지 위해 중단.")
                log("  빈 코트 있었으나 모두 실패 — 재스캔 후 재시도")
                time.sleep(0.3)

        # ── 우선순위 목록을 위에서부터 '전부' 예약 (성공해도 다음으로 계속) ──
        booked, full, skipped, conflicts = [], [], [], []
        for rank, (day_kr, py_wd, want_date, stime, etime) in enumerate(targets, 1):
            if want_date is not None:
                # 날짜 직접 지정
                dates = [want_date] if want_date in open_dates else []
            else:
                # 요일 지정 → 열린 날짜 중 매칭 (이른 날짜 우선)
                dates = sorted(d for d in open_dates
                               if datetime.date.fromisoformat(d).weekday() == py_wd)
            if not dates:
                why = "지정 날짜가 안 열림" if want_date else "해당 요일 열린 날짜 없음"
                log(f"[{rank}순위] {day_kr} {stime}-{etime}시 — {why}, 건너뜀")
                skipped.append((rank, day_kr, stime, etime))
                continue

            secured = False
            conflicted = False
            for date in dates:
                log(f"[{rank}순위] {day_kr} {stime}-{etime}시 → {date} 시도")
                r = secure_one(date, stime, etime)
                if r == "full":
                    log(f"  → {date} 14개 코트 모두 매진")
                    continue  # 같은 요일의 다음 날짜 시도
                if r == "conflict":
                    log(f"  → {date} 멤버가 그날 이미 예약 있음(1일1예약) "
                        f"— 즉시 다음 우선순위로")
                    conflicted = True
                    break  # 다른 날짜도 안 보고 바로 다음 우선순위
                kind, court = r
                if kind == "booked":
                    log(f"✅ 예약 성공(검증됨): 잔디코트 {court} / {date} "
                        f"{stime}-{etime}시 ({day_kr})")
                    common.save_state(ctx)
                    booked.append((rank, day_kr, date, court, stime, etime))
                elif kind == "dry":
                    log(f"  [DRY] 잔디코트 {court} 예약 가능 — 제출 생략")
                    booked.append((rank, day_kr, date, court, stime, etime))
                elif kind == "fill":
                    log("FILL 모드 — 첫 항목 폼 준비 완료. 창에서 직접 제출하세요. (10분 유지)")
                    time.sleep(600)
                    ctx.close(); browser.close()
                    sys.exit(0)
                secured = True
                break  # 이 우선순위 1건 확보 → 다음 우선순위로
            if conflicted:
                conflicts.append((rank, day_kr, stime, etime))
            elif not secured:
                log(f"[{rank}순위] {day_kr} {stime}-{etime}시 — 매칭 날짜 모두 매진")
                full.append((rank, day_kr, stime, etime))

        # ── 결과 요약 ──
        log("=" * 50)
        log("===== 결과 요약 =====")
        tag = "[DRY] " if args.dry else ""
        for rank, day_kr, date, court, s, e in booked:
            log(f"  ✅ {tag}{rank}순위 {day_kr} {date} {s}-{e}시 → 잔디코트 {court}")
        for rank, day_kr, s, e in full:
            log(f"  ✗ {rank}순위 {day_kr} {s}-{e}시 — 매진")
        for rank, day_kr, s, e in conflicts:
            log(f"  ⊘ {rank}순위 {day_kr} {s}-{e}시 — 그날 이미 예약 있음(1일1예약)")
        for rank, day_kr, s, e in skipped:
            log(f"  – {rank}순위 {day_kr} {s}-{e}시 — 날짜 없음")
        verb = "예약 가능(DRY)" if args.dry else "예약 완료"
        log(f"총 {len(booked)}건 {verb}, {len(full)}건 매진, "
            f"{len(conflicts)}건 충돌, {len(skipped)}건 스킵")
        log("=" * 50)

        ctx.close(); browser.close()
        sys.exit(0 if booked else 1)


def get_open_dates(req):
    """예약 가능한 날짜 목록(YYYY-MM-DD). facility view 페이지에서 추출 (가벼운 GET)."""
    try:
        r = req.get(f"{common.SITE}/facility/list?mode=view&facility_idx=3",
                    timeout=15000)
        if not r.ok:
            return []
        return re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"', r.text())
    except Exception:
        return []


if __name__ == "__main__":
    main()
