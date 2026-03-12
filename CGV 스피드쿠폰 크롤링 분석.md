# **CGV '스피드 쿠폰' 크롤링 기술 분석 및 구현 전략**

## **1\. 데이터 수집 엔드포인트**

* **URL**: https://api.cgv.co.kr/tme/more/itgrSrch/searchItgrSrchEvnt  
* **Method**: GET  
* **특징**: 통합 검색 API를 직접 호출하여, 검색어('스피드')에 매칭되는 이벤트 목록을 JSON 형태로 깔끔하게 반환받음. 3사 중 가장 직관적이고 파싱이 용이한 구조.

## **2\. Request Parameters (Query String)**

GET 요청 시 URL 파라미터로 아래 데이터를 전송함.

| 파라미터 | 값 | 설명 |
| :---- | :---- | :---- |
| coCd | A420 | 플랫폼/회사 코드 추정 (고정값 사용 가능) |
| swrd | %EC%8A%A4%ED%94%BC%EB%93%9C | 검색어 ('스피드'의 URL Encoding) |
| lmtSrchYn | N | 제한 검색 여부 추정 (고정값 사용 가능) |

## **3\. Response 파싱 및 데이터 추출 로직**

응답으로 반환되는 JSON 데이터 구조 내에서 data.evntLst 배열을 순회하며 필요한 정보를 추출함.

```json
{  
  "statusCode": 0,  
  "data": {  
    "totalCnt": 1,  
    "evntLst": \[  
      {  
        "evntNo": "202603036625",  
        "evntNm": "\[프로젝트 헤일메리\] 스피드 쿠폰",  
        "evntStartDt": "2026-03-06 15:00:00",  
        "evntEndDt": "2026-03-24 23:59:59"  
      }  
    \]  
  }  
}
```

* **이벤트 아이디 추출**: evntNo 필드값 획득.  
* **텍스트 노드 추출**: evntNm(제목), evntStartDt, evntEndDt(기간) 필드값 획득.  
* **최종 예매 URL 조합**:  
  추출한 evntNo를 CGV 모바일 이벤트 상세 페이지 URL 패턴에 결합.  
  (예상 패턴) https://m.cgv.co.kr/WebApp/EventNotiV4/EventDetailGeneralUnited.aspx?seq={evntNo}

## **4\. Python 크롤링 구현 코드**

```python
import requests  
import urllib.parse

def get\_cgv\_speed\_coupons():  
    \# 검색어 인코딩  
    keyword \= urllib.parse.quote("스피드")  
    url \= f"\[https://api.cgv.co.kr/tme/more/itgrSrch/searchItgrSrchEvnt?coCd=A420\&swrd=\](https://api.cgv.co.kr/tme/more/itgrSrch/searchItgrSrchEvnt?coCd=A420\&swrd=){keyword}\&lmtSrchYn=N"  
      
    headers \= {  
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"  
    }  
      
    try:  
        response \= requests.get(url, headers=headers)  
        response.raise\_for\_status()  
        data \= response.json()  
          
        results \= \[\]  
          
        if data.get("statusCode") \== 0 and "data" in data:  
            event\_list \= data\["data"\].get("evntLst", \[\])  
              
            for event in event\_list:  
                \# "스피드 쿠폰"이 이름에 포함되어 있는지 2차 검증 (필요 시)  
                if "스피드" not in event.get("evntNm", ""):  
                    continue  
                      
                event\_id \= event.get("evntNo")  
                title \= event.get("evntNm")  
                start\_date \= event.get("evntStartDt")  
                end\_date \= event.get("evntEndDt")  
                  
                if event\_id:  
                    results.append({  
                        "title": title,  
                        "date": f"{start\_date} \~ {end\_date}",  
                        "event\_id": event\_id,  
                        \# CGV 모바일 이벤트 링크 패턴 (실제 URL 구조 확인 후 변경 필요)  
                        "url": f"\[https://m.cgv.co.kr/WebApp/EventNotiV4/EventDetailGeneralUnited.aspx?seq=\](https://m.cgv.co.kr/WebApp/EventNotiV4/EventDetailGeneralUnited.aspx?seq=){event\_id}"  
                    })  
                      
        return results

    except Exception as e:  
        print(f"Error fetching CGV events: {e}")  
        return \[\]

\# 테스트 실행  
if \_\_name\_\_ \== "\_\_main\_\_":  
    speed\_events \= get\_cgv\_speed\_coupons()  
    for event in speed\_events:  
        print(f"제목: {event\['title'\]}\\n기간: {event\['date'\]}\\n링크: {event\['url'\]}\\n")  
```