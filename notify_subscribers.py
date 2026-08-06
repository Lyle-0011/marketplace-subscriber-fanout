"""Publish a new marketplace listing to its interested subscribers."""
from marketplace_fanout import fan_out_listing


LISTING = {"id": "listing-482", "title": "Refurbished studio monitor"}
SUBSCRIBER_IDS = ["subscriber-ava", "subscriber-mika", "subscriber-noor"]


if __name__ == "__main__":
    published = fan_out_listing(LISTING, SUBSCRIBER_IDS)
    print(f"published {published} marketplace notifications")
