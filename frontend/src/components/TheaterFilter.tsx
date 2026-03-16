import type { TheaterFilter as TheaterFilterType } from '../types';

const FILTERS: { value: TheaterFilterType; label: string; color: string; activeColor: string }[] = [
  { value: 'ALL', label: '전체', color: 'text-gray-400 hover:text-white', activeColor: 'bg-white/15 text-white' },
  { value: 'CGV', label: 'CGV', color: 'text-gray-400 hover:text-red-400', activeColor: 'bg-red-500/20 text-red-300 border-red-500/30' },
  { value: 'MEGABOX', label: '메가박스', color: 'text-gray-400 hover:text-purple-400', activeColor: 'bg-purple-500/20 text-purple-300 border-purple-500/30' },
  { value: 'LOTTECINEMA', label: '롯데시네마', color: 'text-gray-400 hover:text-sky-400', activeColor: 'bg-sky-500/20 text-sky-300 border-sky-500/30' },
];

interface TheaterFilterProps {
  current: TheaterFilterType;
  onChange: (filter: TheaterFilterType) => void;
  counts: Record<TheaterFilterType, number>;
}

export default function TheaterFilter({ current, onChange, counts }: TheaterFilterProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {FILTERS.map((f) => (
        <button
          key={f.value}
          onClick={() => onChange(f.value)}
          className={`inline-flex items-center gap-1.5 rounded-full border border-transparent px-4 py-2 text-sm font-medium transition-all duration-200 active:scale-95 ${
            current === f.value ? f.activeColor + ' border' : f.color + ' hover:bg-white/5'
          }`}
        >
          {f.label}
          <span className={`text-xs ${current === f.value ? 'opacity-80' : 'opacity-50'}`}>
            {counts[f.value]}
          </span>
        </button>
      ))}
    </div>
  );
}
