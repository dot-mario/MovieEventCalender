import unittest

from crawlers.megabox import extract_event_items


class MegaboxCrawlerTest(unittest.TestCase):
    def test_distinguishes_empty_list_from_invalid_response(self):
        self.assertEqual([], extract_event_items('<div class="event-list"></div>'))

        with self.assertRaisesRegex(RuntimeError, "event-list"):
            extract_event_items("<html>blocked</html>")


if __name__ == "__main__":
    unittest.main()
