# 🎬 MovieEventCalender - Backend

CGV, 메가박스, 롯데시네마 3사의 선착순 할인 이벤트를 자동으로 수집하는 파이프라인입니다.

## 주요 기능

- **3사 병렬 크롤링** — `ThreadPoolExecutor`를 활용한 멀티스레드 기반 동시 수집
- **통합 데이터 모델** — `MovieEvent` 데이터클래스로 3사 데이터를 단일 포맷으로 정규화
- **이중 출력** — 정적 JSON (`events.json`)과 ICS 캘린더 파일 (`events.ics`)을 동시에 생성
- **GitHub Actions 자동화** — 2시간 주기 스케줄링으로 자동 실행

## 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.10+ |
| HTTP 요청 | Requests |
| HTML 파싱 | BeautifulSoup4 |
| 동적 페이지 | Playwright (Chromium) |
| 자동화 | GitHub Actions (cron) |

## 프로젝트 구조

```
backend/
├── main.py                  # 통합 파이프라인 엔트리 포인트
├── requirements.txt         # Python 의존성
└── crawlers/
    ├── models.py            # MovieEvent 공통 데이터 모델
    ├── cgv.py               # CGV 스피드쿠폰 크롤러
    ├── megabox.py           # 메가박스 빵원티켓 크롤러
    └── lottecinema.py       # 롯데시네마 무비싸다구 크롤러
```

## 실행 방법

### 사전 요구사항

- Python 3.10+
- Playwright Chromium 브라우저

### 로컬 실행

```bash
# 가상환경 생성 및 활성화
conda create -n MovieEventCalender python=3.10
conda activate MovieEventCalender

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium

# 크롤러 실행
python main.py
```

### GitHub Actions (자동)

`.github/workflows/update_events.yml` 워크플로우가 **2시간 간격**으로 자동 실행됩니다.

- `push` (main 브랜치) 시에도 자동으로 작동
- `workflow_dispatch`를 통해 수동으로 실행할 수 있음

## 데이터 모델 (`MovieEvent`)

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | `str` | 고유 식별자 (예: `cgv-12345`) |
| `theater` | `str` | 영화관 코드 (`CGV`, `MEGABOX`, `LOTTECINEMA`) |
| `title` | `str` | 이벤트 제목 |
| `startDate` | `str` | 시작 일시 (`YYYY-MM-DD HH:MM:SS`) |
| `url` | `str` | 상세 페이지 URL |
| `imageUrl` | `str?` | 이미지 URL (선택 사항) |
| `category` | `str?` | 카테고리 (선택 사항) |

## 출력 파일

크롤링 결과는 `frontend/public/data/` 디렉토리에 저장합니다.

- **`events.json`** — 프론트엔드에서 가져와(Fetch) 렌더링할 이벤트 데이터
- **`events.ics`** — 사용자가 캘린더에 구독할 수 있는 ICS 파일 (10분 전 알림 포함)

## 관련 문서

- [기획서](../영화%20할인%20통합%20대시보드%20기획서.md) — 서비스 기획 및 핵심 컨셉
- [CGV 크롤링 분석](../CGV%20스피드쿠폰%20크롤링%20분석.md)
- [메가박스 크롤링 분석](../메가박스%20빵원티켓%20크롤링%20분석.md)
- [롯데시네마 크롤링 분석](../롯데시네마%20무비싸다구%20크롤링%20분석.md)
