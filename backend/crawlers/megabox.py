import os
import sys
import requests
from bs4 import BeautifulSoup
import re
import json

# 단독 실행 시 모듈 경로 인식 에러 방지용
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.models import MovieEvent

def get_megabox_zero_tickets():
    """
    메가박스 '빵원티켓' 목록을 가져온 후, 
    각 이벤트 상세 페이지에 접속하여 정확한 시작 시간(HH:mm)을 파싱하고,
    영화 제목만 깔끔하게 정제하여 반환합니다.
    """
    url = "https://m.megabox.co.kr/on/oh/ohe/Event/eventMngDiv.do"
    
    payload = {
        "currentPage": "1",
        "recordCountPerPage": "10",
        "eventTitle": "빵원",
        "eventStatCd": "ONG",
        "orderReqCd": "ONGlist"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36"
    }
    
    results = []
    
    try:
        # 1. 목록 페이지 조회
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('.event-list .item')
        
        for item in items:
            a_tag = item.find('a')
            if not a_tag: 
                continue
                
            # 이벤트 ID 추출
            onclick_text = a_tag.get('onclick', '')
            match = re.search(r"fn_eventDetail\('(\d+)'", onclick_text)
            event_id = match.group(1) if match else None
            
            # =========================================================
            # [수정된 부분] 제목 추출 및 정제
            # =========================================================
            title_tag = item.select_one('.title')
            raw_title = title_tag.text.strip() if title_tag else "제목 없음"
            
            clean_title = raw_title
            # 정규식: '[' 로 시작하고 ']' 로 끝나는 사이의 모든 문자(.*?)를 추출
            title_match = re.search(r'\[(.*?)\]', raw_title)
            if title_match:
                # 괄호 안의 영화명만 빼냄 (예: "프로젝트 헤일메리")
                clean_title = title_match.group(1).strip()
            # =========================================================
            
            # 1차 파싱: 목록의 날짜 텍스트 (기본값 세팅)
            date_tag = item.select_one('.date')
            date_str = date_tag.text.strip() if date_tag else ""
            start_date = ""
            
            if "~" in date_str:
                parts = date_str.split("~")
                start_date = parts[0].strip().replace(".", "-") + " 00:00:00"
            else:
                start_date = date_str.replace(".", "-") + " 00:00:00"
                
            # 썸네일 추출
            img_tag = item.select_one('img')
            img_url = img_tag.get('data-src', '') if img_tag else ""
            
            if event_id:
                detail_url = f"https://megabox.co.kr/event/detail?eventNo={event_id}"
                
                # 2. 상세 페이지 추가 진입 및 정확한 시간 파싱
                try:
                    detail_res = requests.get(detail_url, headers=headers, timeout=5)
                    time_match = re.search(r'기간\s*(\d{4})\s*\.\s*(\d{1,2})\s*\.\s*(\d{1,2}).*?(\d{1,2}:\d{2})', detail_res.text)
                    
                    if time_match:
                        year, month, day, time_str = time_match.groups()
                        start_date = f"{year}-{int(month):02d}-{int(day):02d} {time_str}:00"
                        
                except Exception as e:
                    print(f"[Megabox] 상세 페이지 파싱 오류 (ID: {event_id}) - 1차 날짜로 대체합니다: {e}")

                # MovieEvent 객체 생성
                results.append(MovieEvent(
                    id=f"mega-{event_id}",
                    theater="MEGABOX",
                    title=clean_title,
                    startDate=start_date,
                    url=detail_url,
                    imageUrl=img_url,
                    category="빵원티켓"
                ))
                
    except Exception as e:
        print(f"[Megabox] 빵원티켓 크롤링 중 오류 발생: {e}")
        
    return results

if __name__ == "__main__":
    # 단독 모듈로 실행 테스트
    events = get_megabox_zero_tickets()
    event_dicts = [event.to_dict() for event in events]
    print(json.dumps(event_dicts, indent=2, ensure_ascii=False))