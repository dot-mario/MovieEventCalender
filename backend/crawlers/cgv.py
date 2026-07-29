import json
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime

# 윈도우 환경에서 콘솔 출력(이모지 등) 인코딩 에러 방지
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# 단독 실행 시 모듈 경로 인식 에러 방지용
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.models import MovieEvent

CGV_SEARCH_API_PATH = "/itgrSrch/searchItgrSrchAll"
RELEVANT_COUPON_CATEGORIES = (
    ("스피드", "스피드쿠폰"),
    ("서프라이즈", "서프라이즈쿠폰"),
)


def extract_events(data):
    """
    JSON 데이터의 구조가 어떻게 생겼든 상관없이,
    'evntNo'와 'evntNm'을 가진 이벤트 객체만 모두 찾아내어 리스트로 반환하는 재귀 함수입니다.
    """
    events = []
    if isinstance(data, dict):
        if "evntNo" in data and "evntNm" in data:
            events.append(data)
        for value in data.values():
            events.extend(extract_events(value))
    elif isinstance(data, list):
        for item in data:
            events.extend(extract_events(item))
    return events


def extract_event_search_payload(data):
    """
    통합 검색 응답에서 이벤트 목록(evntLst)을 찾습니다.

    빈 evntLst도 정상 응답으로 구분해야 하므로 목록 존재 여부와 이벤트를
    별도로 반환합니다.
    """
    schema_found = False
    events = []

    if isinstance(data, dict):
        event_list = data.get("evntLst")
        if isinstance(event_list, list):
            schema_found = True
            events.extend(extract_events(event_list))

        for key, value in data.items():
            if key == "evntLst":
                continue
            child_schema_found, child_events = extract_event_search_payload(value)
            schema_found = schema_found or child_schema_found
            events.extend(child_events)
    elif isinstance(data, list):
        for item in data:
            child_schema_found, child_events = extract_event_search_payload(item)
            schema_found = schema_found or child_schema_found
            events.extend(child_events)

    return schema_found, events


def is_cgv_search_api_url(url):
    """
    CGV가 API 호스트를 프록시 경로로 바꾸더라도 검색 API를 식별합니다.
    """
    return CGV_SEARCH_API_PATH in url


def normalize_start_date(value):
    """
    CGV 날짜 값을 프론트엔드 공통 형식으로 정규화합니다.
    """
    raw_value = str(value or "").strip()
    if not raw_value:
        return ""

    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y.%m.%d",
        "%Y%m%d%H%M%S",
        "%Y%m%d",
    )
    for date_format in formats:
        try:
            parsed = datetime.strptime(raw_value, date_format)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    return ""


def build_movie_events(raw_events):
    """
    통합 검색 결과 중 영화 선착순 쿠폰만 MovieEvent로 변환합니다.
    """
    results = []
    seen_ids = set()

    for event in raw_events:
        raw_title = str(event.get("evntNm", "")).strip()
        category_name = next(
            (
                category
                for keyword, category in RELEVANT_COUPON_CATEGORIES
                if keyword in raw_title and "쿠폰" in raw_title
            ),
            None,
        )
        if not category_name:
            continue

        event_id = str(event.get("evntNo", "")).strip()
        if not event_id or event_id in seen_ids:
            continue

        start_date = normalize_start_date(event.get("evntStartDt"))
        if not start_date:
            print(f"[CGV] 시작일 형식을 해석할 수 없어 제외합니다 (ID: {event_id})")
            continue

        seen_ids.add(event_id)

        title_match = re.search(r"\[(.*?)\]", raw_title)
        movie_title = title_match.group(1).strip() if title_match else raw_title

        img_path = str(event.get("mduBanrPhyscFilePathnm", "")).strip("/")
        img_file = str(event.get("mduBanrPhyscFnm", "")).strip("/")
        image_url = ""
        if img_path and img_file:
            image_url = f"https://cdn.cgv.co.kr/{img_path}/{img_file}"

        results.append(
            MovieEvent(
                id=f"cgv-{event_id}",
                theater="CGV",
                title=movie_title,
                startDate=start_date,
                url=f"https://cgv.co.kr/evt/eventDetail?evntNo={event_id}",
                imageUrl=image_url,
                category=category_name,
            )
        )

    return results


def get_cgv_coupons():
    try:
        from playwright.sync_api import (
            TimeoutError as PlaywrightTimeoutError,
        )
        from playwright.sync_api import (
            sync_playwright,
        )
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Playwright가 설치되지 않았습니다. "
            "backend/requirements.txt를 먼저 설치하세요."
        ) from error

    keyword = urllib.parse.quote("쿠폰")
    target_url = f"https://cgv.co.kr/tme/itgrSrch?swrd={keyword}"
    print("[CGV] Playwright 브라우저 시작 (통합 검색 API 대기 중)...")

    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="ko-KR",
                timezone_id="Asia/Seoul",
                viewport={"width": 1920, "height": 1080},
                extra_http_headers={
                    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
                },
            )
            page = context.new_page()

            page.add_init_script(
                """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                """
            )

            intercepted_events = []
            matched_response_count = 0
            parsed_payload_count = 0
            response_errors = []

            def handle_response(response):
                nonlocal matched_response_count, parsed_payload_count
                if not is_cgv_search_api_url(response.url):
                    return

                matched_response_count += 1
                if response.status != 200:
                    response_errors.append(f"{response.status} 응답: {response.url}")
                    return

                try:
                    data = response.json()
                    schema_found, found_events = extract_event_search_payload(data)
                    if not schema_found:
                        response_errors.append(
                            f"evntLst가 없는 응답 구조: {response.url}"
                        )
                        return

                    parsed_payload_count += 1
                    intercepted_events.extend(found_events)
                except Exception as error:
                    response_errors.append(f"JSON 파싱 실패 ({response.url}): {error}")

            page.on("response", handle_response)

            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            except PlaywrightTimeoutError:
                print("[CGV] DOM 로딩 타임아웃. API 응답을 추가로 확인합니다.")
            except Exception as error:
                print(f"[CGV] 페이지 이동 중 오류: {error}")

            # 고정 5초 대기 대신 응답을 0.25초 단위로 확인하고 즉시 종료합니다.
            deadline = time.monotonic() + 10
            while parsed_payload_count == 0 and time.monotonic() < deadline:
                page.wait_for_timeout(250)

            if parsed_payload_count == 0:
                details = "; ".join(response_errors) if response_errors else "응답 없음"
                raise RuntimeError(
                    "CGV 통합 검색 API를 정상 파싱하지 못했습니다 "
                    f"(감지 응답: {matched_response_count}, 상세: {details})"
                )

            results = build_movie_events(intercepted_events)
            print(
                f"[CGV] 검색 API {matched_response_count}개 응답에서 "
                f"영화 쿠폰 {len(results)}개를 선별했습니다."
            )
            return results
        finally:
            if browser is not None:
                browser.close()


if __name__ == "__main__":
    events = get_cgv_coupons()
    event_dicts = [event.to_dict() for event in events]
    print(json.dumps(event_dicts, indent=2, ensure_ascii=False))
