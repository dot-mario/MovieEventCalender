import requests
from bs4 import BeautifulSoup
import re

def get_megabox_zero_tickets():
    """
    메가박스 '빵원티켓' 이벤트를 크롤링하여 통일된 JSON 포맷 리스트로 반환합니다.
    (HTML DOM 및 JavaScript 속성 파싱 방식 사용)
    """
    url = "https://m.megabox.co.kr/on/oh/ohe/Event/eventMngDiv.do"
    
    # x-www-form-urlencoded용 폼 데이터
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
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('.event-list .item')
        
        for item in items:
            a_tag = item.find('a')
            if not a_tag: 
                continue
                
            # 1. onclick 속성에서 fn_eventDetail 인자 추출 (이벤트 ID)
            onclick_text = a_tag.get('onclick', '')
            match = re.search(r"fn_eventDetail\('(\d+)'", onclick_text)
            event_id = match.group(1) if match else None
            
            # 2. 제목 추출
            title_tag = item.select_one('.title')
            title = title_tag.text.strip() if title_tag else "제목 없음"
            
            # 3. 날짜 추출 (형식: 2026.03.01 ~ 2026.03.15)
            date_tag = item.select_one('.date')
            date_str = date_tag.text.strip() if date_tag else ""
            
            # 공통 인터페이스 맞추기 (startDate, endDate 분리)
            start_date = ""
            end_date = ""
            if "~" in date_str:
                parts = date_str.split("~")
                start_date = parts[0].strip().replace(".", "-") + " 00:00:00"
                end_date = parts[1].strip().replace(".", "-") + " 23:59:59"
            
            if event_id:
                results.append({
                    "id": f"mega-{event_id}",
                    "theater": "MEGABOX",
                    "title": title,
                    "startDate": start_date,
                    "endDate": end_date,
                    "url": f"https://megabox.co.kr/event/detail?eventNo={event_id}"
                })
                
    except Exception as e:
        print(f"[Megabox] 빵원티켓 크롤링 중 오류 발생: {e}")
        
    return results

if __name__ == "__main__":
    import json
    print(json.dumps(get_megabox_zero_tickets(), indent=2, ensure_ascii=False))
