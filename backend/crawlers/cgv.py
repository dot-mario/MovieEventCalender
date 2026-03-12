import os
import sys
import urllib.parse
import json
from playwright.sync_api import sync_playwright

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

def get_cgv_speed_coupons():
    keyword = urllib.parse.quote("스피드")
    target_url = f"https://cgv.co.kr/tme/itgrSrch?swrd={keyword}"
    results = []
    
    print("[CGV] Playwright 브라우저 시작 (광역 네트워크 인터셉트 중)...")
    
    with sync_playwright() as p:
        # 봇 탐지 우회 옵션을 유지한 채 백그라운드 실행(headless=True)
        browser = p.chromium.launch(
            headless=True, 
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        intercepted_events = []
        
        # 특정 API 이름 대신, 데이터 내용물로 필터링하는 넓은 그물망
        def handle_response(response):
            # cgv 관련 API에서 200 OK 응답이 온 경우만 확인
            if "api.cgv.co.kr" in response.url and response.status == 200:
                try:
                    data = response.json()
                    # 응답 데이터를 통째로 문자열로 바꿔서 타겟 데이터가 있는지 빠른 검사
                    json_str = json.dumps(data, ensure_ascii=False)
                    if "evntNo" in json_str and "스피드" in json_str:
                        # 타겟 데이터가 있으면 정밀 탐색 함수(extract_events)로 객체 추출
                        found_events = extract_events(data)
                        intercepted_events.extend(found_events)
                except Exception:
                    pass # JSON이 아닌 응답(이미지 등)은 무시

        page.on("response", handle_response)
        
        try:
            # 네트워크 통신이 끝날 때까지 대기
            page.goto(target_url, wait_until="networkidle", timeout=20000)
            
            if not intercepted_events:
                print("\n[CGV] ❌ 타겟 데이터를 찾을 수 없습니다.")
                return []
                
            # 중복 제거 (동일 이벤트가 여러 API에서 올 경우 대비)
            seen_ids = set()
            
            for event in intercepted_events:
                title = event.get("evntNm", "")
                
                if "스피드" not in title:
                    continue
                    
                event_id = str(event.get("evntNo", ""))
                
                if event_id in seen_ids:
                    continue
                seen_ids.add(event_id)
                
                start_date = event.get("evntStartDt", "")
                end_date = event.get("evntEndDt", "")
                if end_date:
                    end_date = f"{end_date} 23:59:59"
                    
                if event_id:
                    # 이미지 URL 조합 로직 추가
                    img_path = event.get("mduBanrPhyscFilePathnm", "")
                    img_file = event.get("mduBanrPhyscFnm", "")
                    image_url = ""
                    if img_path and img_file:
                        # CDN 호스트명 추가
                        image_url = f"https://cdn.cgv.co.kr/{img_path}/{img_file}"
                    
                    movie_event = MovieEvent(
                        id=f"cgv-{event_id}",
                        theater="CGV",
                        title=title,
                        startDate=start_date,
                        url=f"https://cgv.co.kr/evt/eventDetail?evntNo={event_id}",
                        imageUrl=image_url,
                        category="스피드쿠폰"
                    )
                    results.append(movie_event)
                    
        except Exception as e:
            print(f"[CGV] 브라우저 자동화 크롤링 중 오류: {e}")
            
        finally:
            browser.close()
            
    return results

if __name__ == "__main__":
    print(json.dumps(get_cgv_speed_coupons(), indent=2, ensure_ascii=False))