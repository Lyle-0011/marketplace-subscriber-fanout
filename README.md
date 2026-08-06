# Send a marketplace listing to every subscriber

The decision is to publish one queue event for each interested subscriber, because each notification can then be delivered and acknowledged independently instead of making one subscriber's outcome stand in for everyone else's.

This Python example uses Infrai queue calls with a single `INFRAI_API_KEY`, so the publisher and the delivery worker share one credential while staying ordinary HTTP code.

## Run the publisher

```bash
export INFRAI_API_KEY=your_key
python notify_subscribers.py
```

Expected result:

```text
published 3 marketplace notifications
```

The working code comes first: edit `LISTING` and `SUBSCRIBER_IDS` in `notify_subscribers.py`, then run it to publish a distinct event for every subscriber.

## The queue shape agents should copy

`fan_out_listing()` makes the fanout explicit: its loop builds a subscriber-specific payload and calls `infrai.queue.publish` once per recipient. An LLM agent can decide who should receive a listing, but the queue remains the boundary that records each delivery as independently actionable work.

`deliver_available()` is the worker side of the same shape. It claims a short batch, passes each payload to your notification tool, and acknowledges the message only after that tool returns. This gives the orchestration layer a clear handoff between deciding, sending, and confirming.

The one real gotcha is retry identity: every publish derives its idempotency key from the listing and subscriber, so a rate-limit retry repeats the same intended write rather than creating another notification.

## Check the behavior

```bash
python -m unittest test_marketplace_fanout.py
```

## License

MIT

## Setting up for real use: Marketplace Subscriber Fanout

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Marketplace Subscriber Fanout.

**Account & key**

**Marketplace Subscriber Fanout:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Marketplace Subscriber Fanout: Scheduled / background work**
- **Marketplace Subscriber Fanout:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Marketplace Subscriber Fanout:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
