import type { MovieEvent } from './types';

export const parseEventDate = (value: string) =>
  new Date(`${value.replace(' ', 'T')}+09:00`);

export const eventStartTime = (event: MovieEvent) =>
  parseEventDate(event.startDate).getTime();
