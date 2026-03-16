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
    (multipart/form-data 형식으로 API에 페이로드를 전송합니다.)
    """
    base_url = "https://www.lottecinema.co.kr/NLCMW/"
    api_url = "https://www.lottecinema.co.kr/LCWS/Event/EventData.aspx"
    
    # curl에서 확인된 실제 User-Agent 변수화 (헤더와 페이로드 내부에서 공통 사용)
    ua_string = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36"
    
    headers = {
        "User-Agent": ua_string,
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.lottecinema.co.kr"
        # Content-Type은 requests 모듈이 files 인자를 받을 때 자동으로 multipart/form-data와 boundary를 설정하므로 명시하지 않습니다.
    }
    
    results = []
    
    with requests.Session() as session:
        try:
            # 1. 메인 페이지 접근: 초기 세션 쿠키 발급 및 ID 추출
            res = session.get(base_url, headers=headers)
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
                
            # 2. 이벤트 상세 페이지 방문 (WAF 통과 및 세션 쿠키 설정용)
            detail_url = f"https://www.lottecinema.co.kr/NLCMW/Event/EventTemplateSpeedMulti?eventId={main_event_id}"
            headers["Referer"] = base_url
            session.get(detail_url, headers=headers)
            
            # 3. API 요청
            headers["Referer"] = detail_url
            
            # 실제 브라우저가 전송하는 것과 동일한 필드값 구성
            inner_payload = {
                "MethodName": "GetSpeedEventDetailMulti",
                "channelType": "MW",
                "osType": "A",
                "osVersion": ua_string, 
                "EventID": "",
                "MainEventID": main_event_id
            }
            
            # multipart/form-data 전송을 위한 튜플 매핑
            multipart_payload = {
                "paramList": (None, json.dumps(inner_payload))
            }
            
            # data 대신 files 사용
            api_res = session.post(api_url, files=multipart_payload, headers=headers)
            api_res.raise_for_status()
            
            data = api_res.json()
            
            # 4. 데이터 파싱
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
                        
                        if not title or not start_date:
                            continue
                        
                        unique_key = (title, start_date, start_time)
                        if unique_key not in seen:
                            seen.add(unique_key)
                            
                            full_start_date = f"{start_date} {start_time}".strip()
                            
                            results.append(MovieEvent(
                                id=f"lotte-{main_event_id}-{movie_cd}",
                                theater="LOTTECINEMA",
                                title=title,
                                startDate=full_start_date,
                                url=detail_url,
                                imageUrl=img_url,
                                category="무비싸다구"
                            ))
            else:
                print("[Lotte] API 응답은 성공했으나 이벤트 상세 데이터가 없습니다. 파싱된 이벤트 ID가 '무비싸다구' 이벤트인지 확인하세요.")
                print(f"서버 반환 데이터: {data}")
                        
        except Exception as e:
            print(f"[Lotte] 무비싸다구 크롤링 중 오류 발생: {e}")
            
    return results

if __name__ == "__main__":
    events = get_lottecinema_moviesadagu()
    event_dicts = [event.to_dict() for event in events]
    print(json.dumps(event_dicts, indent=2, ensure_ascii=False))