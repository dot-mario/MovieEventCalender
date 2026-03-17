import { useState, useEffect, useMemo } from 'react';
import EventCard from './components/EventCard';
import TheaterFilter from './components/TheaterFilter';
import type { MovieEvent, TheaterFilter as TheaterFilterType, SortMode } from './types';

function App() {
  const [events, setEvents] = useState<MovieEvent[]>([]);
  const [filter, setFilter] = useState<TheaterFilterType>('ALL');
  const [sortMode, setSortMode] = useState<SortMode>('time');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(new Date());
  const [icsCopied, setIcsCopied] = useState(false);

  // 매 분마다 현재 시간 업데이트 (잔여시간 갱신)
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/events.json`)
      .then((res) => {
        if (!res.ok) throw new Error('데이터를 불러올 수 없습니다.');
        return res.json();
      })
      .then((data: MovieEvent[]) => {
        data.sort((a, b) => new Date(b.startDate).getTime() - new Date(a.startDate).getTime());
        setEvents(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const counts = useMemo(() => {
    const c: Record<TheaterFilterType, number> = { ALL: events.length, CGV: 0, MEGABOX: 0, LOTTECINEMA: 0 };
    events.forEach((e) => c[e.theater]++);
    return c;
  }, [events]);

  const filtered = useMemo(() => {
    if (filter === 'ALL') return events;
    return events.filter((e) => e.theater === filter);
  }, [events, filter]);

  // 다가오는 이벤트 vs 지난 이벤트 분리
  const { upcoming, past } = useMemo(() => {
    const up: MovieEvent[] = [];
    const pa: MovieEvent[] = [];
    filtered.forEach((e) => {
      if (new Date(e.startDate).getTime() > now.getTime()) {
        up.push(e);
      } else {
        pa.push(e);
      }
    });
    // 둘 다 최신순(내림차순)으로 정렬
    up.sort((a, b) => new Date(b.startDate).getTime() - new Date(a.startDate).getTime());
    pa.sort((a, b) => new Date(b.startDate).getTime() - new Date(a.startDate).getTime());
    return { upcoming: up, past: pa };
  }, [filtered, now]);

  // 영화별 그룹핑
  const groupedByMovie = useMemo(() => {
    const groups = new Map<string, MovieEvent[]>();
    filtered.forEach((e) => {
      const list = groups.get(e.title) || [];
      list.push(e);
      groups.set(e.title, list);
    });
    // 그룹 내 이벤트를 최신순으로 정렬하고, 그룹 간 정렬도 가장 최신 이벤트 기준으로 내림차순 정렬
    return Array.from(groups.entries())
      .map(([title, events]) => {
        const sortedEvents = [...events].sort((a, b) => new Date(b.startDate).getTime() - new Date(a.startDate).getTime());
        return [title, sortedEvents] as [string, MovieEvent[]];
      })
      .sort(([, a], [, b]) => {
        const aMax = new Date(a[0].startDate).getTime();
        const bMax = new Date(b[0].startDate).getTime();
        return bMax - aMax;
      });
  }, [filtered]);

  // ICS 구독 URL (현재 호스트 기준)
  const icsUrl = `${window.location.origin}${import.meta.env.BASE_URL}data/events.ics`;

  const handleCopyIcs = async () => {
    try {
      await navigator.clipboard.writeText(icsUrl);
      setIcsCopied(true);
      setTimeout(() => setIcsCopied(false), 2000);
    } catch {
      // fallback
      const input = document.createElement('input');
      input.value = icsUrl;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      document.body.removeChild(input);
      setIcsCopied(true);
      setTimeout(() => setIcsCopied(false), 2000);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* 배경 효과 */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute top-0 left-1/4 h-96 w-96 rounded-full bg-purple-500/5 blur-3xl" />
        <div className="absolute bottom-0 right-1/4 h-96 w-96 rounded-full bg-sky-500/5 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 h-96 w-96 -translate-x-1/2 -translate-y-1/2 rounded-full bg-red-500/5 blur-3xl" />
      </div>

      {/* 헤더 */}
      <header className="border-b border-white/5 backdrop-blur-xl">
        <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-col gap-1">
              <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl">
                <span className="bg-gradient-to-r from-red-400 via-purple-400 to-sky-400 bg-clip-text text-transparent">
                  🎬 MovieEventCalendar
                </span>
              </h1>
              <p className="text-sm text-gray-500">
                CGV · 메가박스 · 롯데시네마 선착순 할인 이벤트 한눈에
              </p>
            </div>

            {/* ICS 구독 버튼 */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleCopyIcs}
                className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-medium text-gray-300 transition-all hover:bg-white/10 hover:text-white active:scale-95"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {icsCopied ? '✓ 복사됨!' : '구독 URL 복사'}
              </button>
              <a
                href={`${import.meta.env.BASE_URL}data/events.ics`}
                download="movie_events.ics"
                className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-medium text-gray-300 transition-all hover:bg-white/10 hover:text-white active:scale-95"
                title="ICS 파일 다운로드"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                .ics 다운로드
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* 메인 */}
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center gap-3 py-32">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-700 border-t-purple-400" />
            <p className="text-sm text-gray-500">이벤트 정보를 불러오는 중...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center gap-3 py-32">
            <span className="text-4xl">⚠️</span>
            <p className="text-sm text-gray-400">{error}</p>
          </div>
        ) : (
          <>
            {/* 필터 + 정렬 */}
            <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <TheaterFilter current={filter} onChange={setFilter} counts={counts} />

              {/* 정렬 토글 */}
              <div className="flex w-fit items-center gap-1 rounded-xl border border-white/10 bg-white/5 p-1">
                <button
                  onClick={() => setSortMode('time')}
                  className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-all ${
                    sortMode === 'time'
                      ? 'bg-white/15 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  ⏱ 시간순
                </button>
                <button
                  onClick={() => setSortMode('movie')}
                  className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-all ${
                    sortMode === 'movie'
                      ? 'bg-white/15 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  🎬 영화별
                </button>
              </div>
            </div>

            {/* 시간순 정렬 */}
            {sortMode === 'time' && (
              <>
                {/* 다가오는 이벤트 */}
                {upcoming.length > 0 && (
                  <section className="mb-12">
                    <h2 className="mb-5 flex items-center gap-2 text-lg font-bold text-white">
                      <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                      다가오는 이벤트
                      <span className="text-sm font-normal text-gray-500">({upcoming.length})</span>
                    </h2>
                    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                      {upcoming.map((event) => (
                        <EventCard key={`${event.id}-${event.startDate}`} event={event} />
                      ))}
                    </div>
                  </section>
                )}

                {/* 지난 이벤트 */}
                {past.length > 0 && (
                  <section>
                    <h2 className="mb-5 flex items-center gap-2 text-lg font-bold text-gray-500">
                      지난 이벤트
                      <span className="text-sm font-normal text-gray-600">({past.length})</span>
                    </h2>
                    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                      {past.map((event) => (
                        <EventCard key={`${event.id}-${event.startDate}`} event={event} />
                      ))}
                    </div>
                  </section>
                )}
              </>
            )}

            {/* 영화별 정렬 */}
            {sortMode === 'movie' && (
              <div className="space-y-10">
                {groupedByMovie.map(([title, movieEvents]) => (
                  <section key={title}>
                    <h2 className="mb-5 flex items-center gap-2 text-lg font-bold text-white">
                      🎬 {title}
                      <span className="text-sm font-normal text-gray-500">({movieEvents.length})</span>
                    </h2>
                    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                      {movieEvents.map((event) => (
                        <EventCard key={`${event.id}-${event.startDate}`} event={event} />
                      ))}
                    </div>
                  </section>
                ))}
              </div>
            )}

            {/* 데이터 없음 */}
            {filtered.length === 0 && (
              <div className="flex flex-col items-center justify-center gap-3 py-32">
                <span className="text-4xl">🔍</span>
                <p className="text-sm text-gray-500">해당 극장의 이벤트가 없습니다.</p>
              </div>
            )}
          </>
        )}
      </main>

      {/* 푸터 */}
      <footer className="border-t border-white/5 py-8">
        <p className="text-center text-xs text-gray-600">
          이벤트 정보는 각 극장 공식 사이트를 기반으로 자동 수집됩니다.
        </p>
      </footer>
    </div>
  );
}

export default App;
