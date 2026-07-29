import unittest

from crawlers.cgv import (
    build_movie_events,
    extract_event_search_payload,
    is_cgv_search_api_url,
    normalize_start_date,
)


class CgvCrawlerTest(unittest.TestCase):
    def test_matches_old_and_new_search_api_urls(self):
        old_url = (
            "https://api.cgv.co.kr/tme/more/itgrSrch/"
            "searchItgrSrchAll?coCd=A420&swrd=%EC%BF%A0%ED%8F%B0"
        )
        new_url = (
            "https://cgv.co.kr/api/v1/common/timeline/more/itgrSrch/"
            "searchItgrSrchAll?coCd=A420&swrd=%EC%BF%A0%ED%8F%B0"
        )

        self.assertTrue(is_cgv_search_api_url(old_url))
        self.assertTrue(is_cgv_search_api_url(new_url))
        self.assertFalse(
            is_cgv_search_api_url(
                "https://api.cgv.co.kr/tme/more/itgrSrch/searchItgrSrchMov"
            )
        )

    def test_extracts_event_list_and_distinguishes_empty_result(self):
        payload = {
            "statusCode": 0,
            "data": {
                "itgrSrchEvntSearchResData": {
                    "totalCnt": 1,
                    "evntLst": [
                        {
                            "evntNo": "100",
                            "evntNm": "[테스트] 스피드 쿠폰",
                        }
                    ],
                }
            },
        }

        schema_found, events = extract_event_search_payload(payload)
        self.assertTrue(schema_found)
        self.assertEqual(["100"], [event["evntNo"] for event in events])

        schema_found, events = extract_event_search_payload({"data": {"evntLst": []}})
        self.assertTrue(schema_found)
        self.assertEqual([], events)

    def test_builds_only_movie_coupon_events_and_deduplicates(self):
        raw_events = [
            {
                "evntNo": "101",
                "evntNm": "[산양들] 서프라이즈 쿠폰",
                "evntStartDt": "20260727",
                "mduBanrPhyscFilePathnm": "/cgvpomscontent/ips/evnt/2026/0724/",
                "mduBanrPhyscFnm": "/banner.jpg",
            },
            {
                "evntNo": "102",
                "evntNm": "[호프] 스피드 쿠폰",
                "evntStartDt": "2026-07-24",
            },
            {
                "evntNo": "101",
                "evntNm": "[산양들] 서프라이즈 쿠폰",
                "evntStartDt": "20260727",
            },
            {
                "evntNo": "103",
                "evntNm": "내 차 보험료 조회하고 영화 할인쿠폰 받기",
                "evntStartDt": "20260101",
            },
        ]

        events = build_movie_events(raw_events)

        self.assertEqual(["cgv-101", "cgv-102"], [event.id for event in events])
        self.assertEqual(["산양들", "호프"], [event.title for event in events])
        self.assertEqual(
            ["서프라이즈쿠폰", "스피드쿠폰"],
            [event.category for event in events],
        )
        self.assertEqual("2026-07-27 00:00:00", events[0].startDate)
        self.assertEqual(
            "https://cdn.cgv.co.kr/cgvpomscontent/ips/evnt/2026/0724/banner.jpg",
            events[0].imageUrl,
        )

    def test_normalizes_supported_date_formats(self):
        self.assertEqual(
            "2026-07-29 14:00:00",
            normalize_start_date("20260729140000"),
        )
        self.assertEqual(
            "2026-07-29 00:00:00",
            normalize_start_date("2026.07.29"),
        )
        self.assertEqual("", normalize_start_date("not-a-date"))


if __name__ == "__main__":
    unittest.main()
