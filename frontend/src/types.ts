export interface MovieEvent {
  id: string;
  theater: 'CGV' | 'MEGABOX' | 'LOTTECINEMA';
  title: string;
  startDate: string;
  url: string;
  imageUrl: string;
  category: string;
}

export type TheaterFilter = 'ALL' | 'CGV' | 'MEGABOX' | 'LOTTECINEMA';

export type SortMode = 'time' | 'movie';
