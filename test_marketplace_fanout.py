"""Focused behavior test for subscriber-specific event construction."""
import unittest
from unittest.mock import patch

from marketplace_fanout import fan_out_listing


class FanoutTests(unittest.TestCase):
    def test_publishes_one_event_per_subscriber(self):
        listing = {"id": "listing-1", "title": "Desk lamp"}
        with patch("marketplace_fanout.infrai.queue.publish") as publish:
            count = fan_out_listing(listing, ["sam", "lee"])

        self.assertEqual(count, 2)
        self.assertEqual(publish.call_count, 2)
        self.assertEqual(publish.call_args_list[0].args[0]["subscriber_id"], "sam")
        self.assertEqual(publish.call_args_list[1].args[1], "listing-1:lee")


if __name__ == "__main__":
    unittest.main()
