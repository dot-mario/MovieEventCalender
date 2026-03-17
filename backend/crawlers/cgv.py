import os
import sys
import urllib.parse
import json
import re  # 정규식 모듈 추가
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# 단독 실행 시 모듈 경로 인식 에러 방지용
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.models import MovieEvent

def extract_events(data):
    """
    JSON 데이터의 구조가 어떻게 생겼든 상관없이, 
    'evntNo'와 'evntNm'을 가진 이벤트 객체만 모두 찾아내어 리스트로 반환하는 재귀 함수입니다.
    """
    events = []
    if isinstance(data, dict):
        if 'evntNo' in data and 'evntNm' in data:
            events.append(data)
        for key, value in data.items():
            events.extend(extract_events(value))
    elif isinstance(data, list):
        for item in data:
            events.extend(extract_events(item))
    return events

def get_cgv_coupons():
    keyword = urllib.parse.quote("쿠폰")
    target_url = f"https://cgv.co.kr/tme/itgrSrch?swrd={keyword}"
    results = []
    
    print("[CGV] Playwright 브라우저 시작 (광역 네트워크 인터셉트 중)...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, 
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
            }
        )
        page = context.new_page()
        
        intercepted_events = []
        
        def handle_response(response):
            # CGV API 응답 캡처 (이벤트 관련 키워드 포함 여부 확인)
            if "api.cgv.co.kr" in response.url and response.status == 200:
                try:
                    data = response.json()
                    json_str = json.dumps(data, ensure_ascii=False)
                    # "evntNo"가 포함된 모든 응답을 일단 파싱 시도 (쿠폰 키워드 필터링은 나중에 수행)
                    if "evntNo" in json_str:
                        found_events = extract_events(data)
                        intercepted_events.extend(found_events)
                except Exception:
                    pass 

        page.on("response", handle_response)
        
        try:
            page.goto(target_url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(5000) # 추가 로딩 대기
            
        except PlaywrightTimeoutError:
            print("[CGV] 페이지 로딩 타임아웃 또는 networkidle 도달 실패. 현재까지 수집된 데이터로 진행합니다.")
        except Exception as e:
            print(f"[CGV] 브라우저 자동화 크롤링 중 오류: {e}")
            
        if not intercepted_events:
            print("\n[CGV] ❌ 타겟 데이터를 찾을 수 없습니다. (차단되었거나 인터셉트 실패)")
            browser.close()
            return []
            
        seen_ids = set()
        
        for event in intercepted_events:
            raw_title = event.get("evntNm", "")
            
            if "쿠폰" not in raw_title:
                continue
                
            event_id = str(event.get("evntNo", ""))
            
            if event_id in seen_ids:
                continue
            seen_ids.add(event_id)
            
            # 대괄호 안의 영화 이름만 추출 (없으면 원본 유지)
            title_match = re.search(r'\[(.*?)\]', raw_title)
            movie_title = title_match.group(1).strip() if title_match else raw_title
            
            start_date = event.get("evntStartDt", "")
            end_date = event.get("evntEndDt", "")
            if end_date:
                end_date = f"{end_date} 23:59:59"
                
            if event_id:
                img_path = event.get("mduBanrPhyscFilePathnm", "")
                img_file = event.get("mduBanrPhyscFnm", "")
                image_url = ""
                if img_path and img_file:
                    image_url = f"https://cdn.cgv.co.kr/{img_path}/{img_file}"
                
                # 원본 제목(raw_title)을 기준으로 카테고리 판별
                category_name = "쿠폰"
                if "스피드" in raw_title:
                    category_name = "스피드쿠폰"
                elif "서프라이즈" in raw_title:
                    category_name = "서프라이즈쿠폰"
                
                movie_event = MovieEvent(
                    id=f"cgv-{event_id}",
                    theater="CGV",
                    title=movie_title,  # 추출한 영화 이름 할당
                    startDate=start_date,
                    url=f"https://cgv.co.kr/evt/eventDetail?evntNo={event_id}",
                    imageUrl=image_url,
                    category=category_name
                )
                results.append(movie_event)
                
        browser.close()
            
    return results

if __name__ == "__main__":
    events = get_cgv_coupons()
    event_dicts = [event.to_dict() for event in events]
    print(json.dumps(event_dicts, indent=2, ensure_ascii=False))
