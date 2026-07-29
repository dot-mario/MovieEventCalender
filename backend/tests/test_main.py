import unittest
from unittest.mock import patch

import main as backend_main
from crawlers.models import MovieEvent


def sample_event(event_id, theater):
    return MovieEvent(
        id=event_id,
        theater=theater,
        title="테스트 영화",
        startDate="2026-08-01 14:00:00",
        url="https://example.com/event",
        category="테스트",
    )


class MainPipelineTest(unittest.TestCase):
    @patch.object(
        backend_main,
        "get_megabox_zero_tickets",
        return_value=[sample_event("mega-1", "MEGABOX")],
    )
    @patch.object(
        backend_main,
        "get_lottecinema_moviesadagu",
        return_value=[sample_event("lotte-1", "LOTTECINEMA")],
    )
    @patch.object(
        backend_main,
        "get_cgv_coupons",
        return_value=[sample_event("cgv-1", "CGV")],
    )
    def test_fetch_all_events_merges_successful_crawlers(
        self,
        _cgv_mock,
        _lotte_mock,
        _megabox_mock,
    ):
        events = backend_main.fetch_all_events()

        self.assertEqual(
            {"cgv-1", "lotte-1", "mega-1"},
            {event.id for event in events},
        )

    @patch.object(
        backend_main,
        "get_megabox_zero_tickets",
        return_value=[sample_event("mega-1", "MEGABOX")],
    )
    @patch.object(
        backend_main,
        "get_lottecinema_moviesadagu",
        side_effect=RuntimeError("API 구조 변경"),
    )
    @patch.object(
        backend_main,
        "get_cgv_coupons",
        return_value=[sample_event("cgv-1", "CGV")],
    )
    def test_fetch_all_events_fails_instead_of_publishing_partial_data(
        self,
        _cgv_mock,
        _lotte_mock,
        _megabox_mock,
    ):
        with self.assertRaisesRegex(RuntimeError, "LotteCinema"):
            backend_main.fetch_all_events()


if __name__ == "__main__":
    unittest.main()
