import requests
import urllib.parse
from datetime import datetime

def get_cgv_speed_coupons():
    """
    CGV 스피드 쿠폰 이벤트를 크롤링하여 통일된 JSON 포맷 리스트로 반환합니다.
    """
    keyword = urllib.parse.quote("스피드")
    url = f"https://api.cgv.co.kr/tme/more/itgrSrch/searchItgrSrchEvnt?coCd=A420&swrd={keyword}&lmtSrchYn=N"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    results = []
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data.get("statusCode") == 0 and "data" in data:
            event_list = data["data"].get("evntLst", [])
            
            for event in event_list:
                # 2차 검증: 스피드쿠폰 관련인지 확인 (분석서 기반)
                if "스피드" not in event.get("evntNm", ""):
                    continue
                    
                event_id = event.get("evntNo")
                title = event.get("evntNm")
                start_date_str = event.get("evntStartDt")
                end_date_str = event.get("evntEndDt")
                
                # 공통 인터페이스 포맷 구성
                if event_id:
                    results.append({
                        "id": f"cgv-{event_id}",
                        "theater": "CGV",
                        "title": title,
                        "startDate": start_date_str,
                        "endDate": end_date_str,
                        # CGV 모바일 예매링크 (고유 URL 패턴 명세화)
                        "url": f"https://m.cgv.co.kr/WebApp/EventNotiV4/EventDetailGeneralUnited.aspx?seq={event_id}",
                        # 현재 시간과 비교하여 이벤트 진행 여부(isOngoing)를 체크하거나 단순 boolean 등 프론트 편의 제공용
                        # (우선 크롤링 당시에는 시작/진행상태 여부 판별 용도보다는 프론트에서 필터할 수 있게 Raw 제공)
                    })
                    
    except Exception as e:
        print(f"[CGV] 스피드 쿠폰 크롤링 중 오류 발생: {e}")
        
    return results

if __name__ == "__main__":
    import json
    print(json.dumps(get_cgv_speed_coupons(), indent=2, ensure_ascii=False))
