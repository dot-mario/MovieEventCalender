import os
import sys
import requests
import re
import json
from datetime import datetime

# 단독 실행 시 모듈 경로 인식 에러 방지용
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.models import MovieEvent

def get_lottecinema_moviesadagu():
    """
    롯데시네마 '무비싸다구' 이벤트를 크롤링하여 MovieEvent 객체 리스트로 반환합니다.
    """
    base_url = "https://www.lottecinema.co.kr/NLCMW/"
    api_url = "https://www.lottecinema.co.kr/LCWS/Event/EventData.aspx"
    
    # 필수 헤더 추가 (Content-Type 및 Referer)
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://www.lottecinema.co.kr/NLCHS/Event/EventDetailST?isEvent=Y"
    }
    
    results = []
    
    try:
        # Step 1: 메인 페이지에서 MainEventID 추출
        res = requests.get(base_url, headers=headers)
        res.raise_for_status()
        
        main_event_id = None
        
        match = re.search(r'EventID"\s*:\s*"(\d+)",\s*"MainEventID"\s*:\s*"(\d+)"', res.text, re.IGNORECASE)
        if match:
            main_event_id = match.group(2)
        else:
            match_url = re.search(r'EventTemplateSpeedMulti\?eventId=(\d+)', res.text, re.IGNORECASE)
            if match_url:
                main_event_id = match_url.group(1)
                 
        if not main_event_id:
            print("[Lotte] 메인 페이지에서 이벤트 ID를 찾을 수 없습니다.")
            return []
            
        # Step 2: 확인된 API 규격에 맞춘 Payload 구성
        inner_payload = {
            "MethodName": "GetSpeedEventDetailMulti",
            "channelType": "MW",
            "osType": "A",
            "osVersion": "Mozilla/5.0",
            "EventID": main_event_id,
            "MainEventID": main_event_id,
            "MemberNo": "0"
        }
        
        payload = {
            "MethodName": "GetSpeedEventDetailMulti",
            "paramList": json.dumps(inner_payload)
        }
        
        api_res = requests.post(api_url, data=payload, headers=headers)
        api_res.raise_for_status()
        
        data = api_res.json()
        
        # Step 3: 중복 제거 및 데이터 파싱
        # SpeedEventDetail은 리스트이므로 [0]으로 접근
        if "SpeedEventDetail" in data and data["SpeedEventDetail"]:
            groups = data["SpeedEventDetail"][0].get("ItemGroup", [])
            seen = set()
            
            for group in groups:
                items = group.get("Items", [])
                for item in items:
                    title = item.get("MovieNm")
                    start_date = item.get("ProgressStartDate")
                    start_time = item.get("ProgressStartTime")
                    img_url = item.get("Img5Url", "")
                    movie_cd = item.get("MovieCd", "unknown")
                    
                    # 유효하지 않은 데이터 건너뛰기
                    if not title or not start_date:
                        continue
                    
                    # 식별 키 생성 및 중복 확인
                    unique_key = (title, start_date, start_time)
                    if unique_key not in seen:
                        seen.add(unique_key)
                        
                        full_start_date = f"{start_date} {start_time}".strip()
                        end_date = f"{start_date} 23:59:59"
                        
                        # MovieEvent 객체 생성
                        results.append(MovieEvent(
                            id=f"lotte-{main_event_id}-{movie_cd}",
                            theater="LOTTECINEMA",
                            title=title,
                            startDate=full_start_date,
                            url=f"https://www.lottecinema.co.kr/NLCMW/Event/EventTemplateSpeedMulti?eventId={main_event_id}",
                            imageUrl=img_url,
                            category="무비싸다구"
                        ))
                        
    except Exception as e:
        print(f"[Lotte] 무비싸다구 크롤링 중 오류 발생: {e}")
        
    return results

if __name__ == "__main__":
    # 단독 실행 테스트용
    events = get_lottecinema_moviesadagu()
    event_dicts = [event.to_dict() for event in events]
    print(json.dumps(event_dicts, indent=2, ensure_ascii=False))