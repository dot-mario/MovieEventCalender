import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
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

    def test_ics_uses_utc_stamp_and_escapes_text(self):
        event = sample_event("cgv-1", "CGV")
        event.title = "테스트, 영화; 특별"
        event.startDate = "2099-08-01 14:00:00"

        with TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "events.ics"
            with (
                patch.object(backend_main, "FRONTEND_DATA_DIR", temp_dir),
                patch.object(backend_main, "ICS_OUTPUT_FILE", str(output_file)),
            ):
                backend_main.save_events_to_ics([event.to_dict()])

            contents = output_file.read_text(encoding="utf-8")

        self.assertIn("DTSTAMP:20990801T050000Z", contents)
        self.assertIn(r"SUMMARY:[CGV] 테스트\, 영화\; 특별 - 테스트", contents)


if __name__ == "__main__":
    unittest.main()
