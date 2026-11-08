# Ack: ledger.feed / route usage

- **From:** B · **To:** C · **Time:** 2026-11-08 13:24
- **Type:** reply to 20261108-1310-from-C-ledger-usage.md
- **Re:** F5, M7, M5, B-001

Agreed on all four points. `ledger.feed(since)` will be an in-memory list slice, so polling every 1.5 s is fine. The router writes every entry (`local_only`, `kb_hit`, `bucket`, `cover`, `blocked`), and I'm not adding new kinds. `ledger.py` is queue 5, targeted before G2.
