# 🎬 MovieEventCalender - Frontend

영화 선착순 할인 이벤트 통합 대시보드의 프론트엔드 애플리케이션입니다.

CGV(스피드쿠폰), 메가박스(빵원티켓), 롯데시네마(무비싸다구) 3사의 선착순 영화 할인 이벤트 정보를 단일 웹페이지에서 한눈에 확인할 수 있습니다.

## 주요 기능

- **3사 통합 타임라인** — 현재 진행 중이거나 예정된 이벤트를 시간순으로 정렬하여 제공
- **극장별 필터링** — CGV / 메가박스 / 롯데시네마 별 선택적 조회
- **캘린더 연동** — Google Calendar 단건 추가 및 ICS 구독을 통한 사전 알림
- **모바일 반응형** — 별도 앱 설치 없이 모바일 브라우저에서 최적화된 UI 제공

## 기술 스택

| 구분 | 기술 |
|------|------|
| 프레임워크 | React 19 + TypeScript |
| 빌드 도구 | Vite 7 |
| 스타일링 | Tailwind CSS 4 |
| 린트 | ESLint + typescript-eslint |
| 데이터 | 정적 JSON (`public/data/events.json`) Fetch |

## 프로젝트 구조

```
frontend/
├── public/
│   └── data/
│       └── events.json        # 크롤러가 생성한 이벤트 데이터 (자동 업데이트)
├── src/
│   ├── components/
│   │   ├── EventCard.tsx      # 개별 이벤트 카드 컴포넌트
│   │   └── TheaterFilter.tsx  # 극장 필터 컴포넌트
│   ├── App.tsx                # 메인 애플리케이션
│   ├── main.tsx               # 엔트리 포인트
│   ├── types.ts               # 타입 정의
│   └── index.css              # 글로벌 스타일
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

## 시작하기

### 사전 요구사항

- Node.js 18+
- npm

### 설치 및 실행

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build

# 빌드 결과 미리보기
npm run preview
```

## 데이터 흐름

프론트엔드는 **자체 백엔드 서버 없이** 동작하는 정적 아키텍처입니다.

```
[GitHub Actions] → Python 크롤러 실행 (2시간 주기)
       ↓
[events.json] → frontend/public/data/ 에 자동 커밋
       ↓
[React App] → fetch()로 JSON 로드 → 브라우저에서 렌더링
```

## 관련 문서

- [기획서](../영화%20할인%20통합%20대시보드%20기획서.md) — 서비스 기획 및 핵심 컨셉
- [CGV 크롤링 분석](../CGV%20스피드쿠폰%20크롤링%20분석.md)
- [메가박스 크롤링 분석](../메가박스%20빵원티켓%20크롤링%20분석.md)
- [롯데시네마 크롤링 분석](../롯데시네마%20무비싸다구%20크롤링%20분석.md)
