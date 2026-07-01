# CGV '스피드 쿠폰' 크롤링 기술 분석 및 구현 전략

## 1. 데이터 수집 접근 방식

*   **타겟 URL**: https://cgv.co.kr/tme/itgrSrch?swrd=쿠폰
*   **수집 방식**: **Playwright를 이용한 네트워크 인터셉트 (Network Interception)**
*   **배경**: CGV API에는 Cloudflare 보안 솔루션이 적용되어, 요청할 때 복잡한 클라이언트 검증 키(Client Key)를 요구합니다. 이를 우회하려 브라우저를 실행해 실제 페이지를 로드하고 내부에서 일어나는 API 응답을 가로채는 방식을 사용합니다. 이때 스피드 쿠폰과 서프라이즈 쿠폰을 모두 수집하기 위해 통합 검색어인 '쿠폰'을 사용해 데이터를 폭넓게 확보합니다.

## 2. 기술적 특징 및 보안 우회

*   **Headless Browser**: Playwright의 Chromium 엔진을 사용하며, 자동화 탐지를 피하려고 `AutomationControlled` 플래그를 비활성화합니다.
*   **User-Agent 설정**: 실제 브라우저와 유사한 User-Agent를 설정하여 봇 차단을 방지합니다.
*   **응답 가로채기**: `page.on("response", ...)` 이벤트로 `api.cgv.co.kr`이 보내는 모든 응답에서 쿠폰 관련 JSON 데이터를 필터링합니다.

## 3. Response 파싱 및 데이터 추출 로직

단순히 JSON 경로에 접근하는 대신 구조 변화에 유연하게 대응하려고 재귀 함수(`extract_events`)를 사용합니다.

*   **재귀적 데이터 탐색**: JSON 데이터 내부에서 `evntNo`(이벤트 번호)와 `evntNm`(이벤트 이름) 쌍을 가진 모든 객체를 찾습니다.
*   **영화 제목 정규식 추출**: `[영화제목] 스피드 쿠폰` 또는 `[영화제목] 서프라이즈 쿠폰` 형태에서 대괄호 내부의 텍스트만 추출해 온전한 제목을 얻습니다.
*   **이미지 URL 조합**: `mduBanrPhyscFilePathnm`(이미지 경로)과 `mduBanrPhyscFnm`(이미지 파일명) 필드를 결합해 `https://cdn.cgv.co.kr/{이미지경로}/{이미지파일명}` 형태의 CDN 주소를 생성합니다.
*   **카테고리 판별**: 원본 이벤트 제목(evntNm)의 키워드를 판별해 '스피드쿠폰' 혹은 '서프라이즈쿠폰'으로 동적 분류하며, 판별이 어려울 때는 기본값 '쿠폰'을 부여합니다.
*   **상세 페이지 URL**: 추출한 `evntNo`로 `https://cgv.co.kr/evt/eventDetail?evntNo={evntNo}`를 조합합니다.
