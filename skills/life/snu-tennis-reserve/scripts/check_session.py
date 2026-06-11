"""저장된 세션이 살아있는지 헤드리스로 확인."""

import sys

from playwright.sync_api import sync_playwright

import common


def main():
    with sync_playwright() as p:
        browser, ctx = common.launch_with_state(p, headless=True)
        page = ctx.new_page()
        page.goto(common.LIST_URL, timeout=30000)
        page.wait_for_load_state("networkidle")
        ok = common.is_logged_in(page)
        if ok:
            common.save_state(ctx)  # 갱신된 세션 쿠키 반영
        ctx.close()
        browser.close()

    if ok:
        print("OK: 로그인 세션 유효")
        sys.exit(0)
    print("FAIL: 세션 만료 — login_setup.py 를 다시 실행하세요")
    sys.exit(1)


if __name__ == "__main__":
    main()
