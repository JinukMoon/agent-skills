"""1회 수동 로그인 — 브라우저 창이 뜨면 SNU SSO 로그인을 직접 진행.

MFA(인증코드) 화면에서 "이 브라우저에서 추가인증 생략" 류의 체크박스가 있으면
반드시 체크할 것 (세션이 오래 유지됨).

로그인이 완료되면 스크립트가 자동으로 감지하고 종료한다.
"""

import time

from playwright.sync_api import sync_playwright

import common


def snapshot(page):
    """현재 페이지의 로그인 판정 단서들을 수집."""
    try:
        url = page.url
        has_logout = page.locator("a[href*='logout']").count()
        has_pw = page.locator("#user_passwd, input[name='user_passwd']").count()
        has_mypage = page.locator("a[href*='mypage']").count()
        return url, has_logout, has_pw, has_mypage
    except Exception as e:
        return f"(접근불가: {e})", -1, -1, -1


def main():
    with sync_playwright() as p:
        ctx = common.launch(p, headless=False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(common.LOGIN_URL)

        print("브라우저에서 로그인을 진행하세요. (최대 10분 대기)", flush=True)
        deadline = time.time() + 600
        ok = False
        last = None
        while time.time() < deadline:
            url, has_logout, has_pw, has_mypage = snapshot(page)
            line = f"url={url} | logout={has_logout} pw={has_pw} mypage={has_mypage}"
            if line != last:  # 상태가 바뀔 때만 출력
                print(line, flush=True)
                last = line
            # 로그인 판정: athletics 도메인 + 로그아웃 링크 존재 + 비밀번호 입력칸 없음
            if ("athletics.snu.ac.kr" in str(url)
                    and has_logout > 0 and has_pw == 0):
                ok = True
                break
            time.sleep(3)

        if ok:
            print("로그인 감지!", flush=True)
            try:
                page.goto(common.LIST_URL)
                page.wait_for_load_state("networkidle")
            except Exception:
                pass
            common.save_state(ctx)
            print("세션이 state.json에 백업되었습니다.", flush=True)
        else:
            print("시간 초과 — 로그인이 감지되지 않았습니다.", flush=True)
        ctx.close()


if __name__ == "__main__":
    main()
