import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

# 단독 실행 시 모듈 경로 인식 에러 방지용
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.models import MovieEvent

LIST_TIMEOUT = 10
DETAIL_TIMEOUT = 5


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
        "orderReqCd": "ONGlist",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36"
    }

    results = []
    with requests.Session() as session:
        try:
            # 1. 목록 페이지 조회 (최대 3회 재시도)
            response = None
            for attempt in range(3):
                try:
                    response = session.post(
                        url,
                        data=payload,
                        headers=headers,
                        timeout=LIST_TIMEOUT,
                    )
                    response.raise_for_status()
                    break
                except requests.RequestException as error:
                    print(f"[Megabox] 목록 조회 실패 (시도 {attempt + 1}/3): {error}")
                    if attempt == 2:
                        raise
                    time.sleep(2)

            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.select(".event-list .item")

            for item in items:
                a_tag = item.find("a")
                title_tag = item.select_one(".title")
                if not a_tag or not title_tag:
                    continue

                onclick_text = a_tag.get("onclick", "")
                match = re.search(r"fn_eventDetail\('(\d+)'", onclick_text)
                event_id = match.group(1) if match else None
                if not event_id:
                    continue

                raw_title = title_tag.text.strip()
                title_match = re.search(r"\[(.*?)\]", raw_title)
                clean_title = title_match.group(1).strip() if title_match else raw_title

                img_tag = item.select_one("img")
                img_url = img_tag.get("data-src", "") if img_tag else ""
                detail_url = f"https://megabox.co.kr/event/detail?eventNo={event_id}"

                # 2. 상세 페이지에서 정확한 시작 시간을 파싱합니다.
                detail_res = session.get(
                    detail_url,
                    headers=headers,
                    timeout=DETAIL_TIMEOUT,
                )
                detail_res.raise_for_status()
                time_match = re.search(
                    r"기간\s*(\d{4})\s*\.\s*(\d{1,2})\s*\.\s*"
                    r"(\d{1,2}).*?(\d{1,2}:\d{2})",
                    detail_res.text,
                )
                if not time_match:
                    raise RuntimeError(
                        f"상세 페이지에서 시작 시간을 찾을 수 없습니다 (ID: {event_id})"
                    )

                year, month, day, time_str = time_match.groups()
                start_date = f"{year}-{int(month):02d}-{int(day):02d} {time_str}:00"

                results.append(
                    MovieEvent(
                        id=f"mega-{event_id}",
                        theater="MEGABOX",
                        title=clean_title,
                        startDate=start_date,
                        url=detail_url,
                        imageUrl=img_url,
                        category="빵원티켓",
                    )
                )

        except Exception as error:
            print(f"[Megabox] 빵원티켓 크롤링 중 오류 발생: {error}")
            raise RuntimeError("메가박스 크롤링에 실패했습니다.") from error

    return results


if __name__ == "__main__":
    # 단독 모듈로 실행 테스트
    events = get_megabox_zero_tickets()
    event_dicts = [event.to_dict() for event in events]
    print(json.dumps(event_dicts, indent=2, ensure_ascii=False))
