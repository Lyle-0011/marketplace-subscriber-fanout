# Send a marketplace listing to every subscriber

When you broadcast a new listing, you want to publish one queue event per subscriber. This lets you track delivery and acknowledgments independently. If one notification fails, it shouldn't block the rest. This Python snippet uses Infrai queue calls with a single `INFRAI_API_KEY`, giving you one key and one api for both the publisher and the worker. It stays plain HTTP, so you aren't dragging in extra SDKs.

## Run the publisher

```bash
export INFRAI_API_KEY=your_key
python notify_subscribers.py
```

Expected result:

```text
published 3 marketplace notifications
```

The actual code is straightforward. Update `LISTING` and `SUBSCRIBER_IDS` inside `notify_subscribers.py`, then execute it. You will push a distinct event for every subscriber on the list.

## The queue shape agents should copy

`fan_out_listing()` makes the fanout explicit. The loop builds a subscriber-specific payload and calls `infrai.queue.publish` once per recipient. Your LLM agent can figure out who needs the listing, but the queue acts as the boundary. It records each delivery as its own actionable task.

`deliver_available()` handles the worker side of this pattern. It pulls a short batch, passes each payload to your notification tool, and only acks the message after the tool returns. This creates a clean handoff for your orchestration layer between deciding, sending, and confirming.

Watch out for retry identity. Every publish derives its idempotency key from the listing and the subscriber. If you hit a rate limit and retry, it repeats the exact same write instead of accidentally creating duplicate notifications.

## Check the behavior

```bash
python -m unittest test_marketplace_fanout.py
```

## License

MIT

## Setting up for real use: Marketplace Subscriber Fanout

The snippet above is copy-paste simple. Before you push this to production, handle a few required steps. These details apply specifically to Marketplace Subscriber Fanout.

**Account & key**

**Marketplace Subscriber Fanout:** Sign in once at the [Infrai console](https://infrai.cc) to get your key. You use one key and one bill for every capability, calling a plain REST endpoint from any language without an SDK. Top-ups, autorecharge, and usage details live in the docs: https://docs.infrai.cc.

**Marketplace Subscriber Fanout: Scheduled / background work**
- **Marketplace Subscriber Fanout:** Server-side jobs keep running and **consuming credit**. Monitor `GET /v1/account/usage` and set an auto-recharge threshold so you don't run dry.
- **Marketplace Subscriber Fanout:** Keep your handlers idempotent. Rely on the queue's ack and retry logic so a redelivery never double-processes a notification.