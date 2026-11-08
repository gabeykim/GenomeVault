"""Agent C: cover traffic runs with the app (PLAN P6.6, G3; B's router.start_cover / stop_cover)."""
import time

import pytest
from fastapi.testclient import TestClient

import app as app_module

REAL_COVER = app_module.start_cover is not None


class FakeCover:
    def __init__(self, already_running=False):
        self.running = already_running
        self.starts = self.stops = 0

    def start(self, interval_s=None):
        if self.running:
            return False
        self.running, self.starts = True, self.starts + 1
        return True

    def stop(self, timeout=5.0):
        self.running, self.stops = False, self.stops + 1

    def is_running(self):
        return self.running


def _install(monkeypatch, fake, enabled=True):
    monkeypatch.setattr(app_module, "start_cover", fake.start)
    monkeypatch.setattr(app_module, "stop_cover", fake.stop)
    monkeypatch.setattr(app_module, "cover_running", fake.is_running)
    monkeypatch.setattr(app_module, "COVER", enabled)


def test_app_starts_cover_on_startup_and_stops_it_on_shutdown(monkeypatch):
    fake = FakeCover()
    _install(monkeypatch, fake)
    with TestClient(app_module.app) as c:          # the context manager runs the lifespan
        assert fake.starts == 1 and fake.running
        assert c.get("/api/ledger").json()["cover"] is True
        assert c.get("/api/status").json()["cover"] is True
    assert fake.stops == 1 and not fake.running


def test_app_does_not_stop_cover_it_did_not_start(monkeypatch):
    fake = FakeCover(already_running=True)
    _install(monkeypatch, fake)
    with TestClient(app_module.app):
        pass
    assert fake.starts == 0 and fake.stops == 0 and fake.running


def test_gv_cover_0_disables_it(monkeypatch):
    fake = FakeCover()
    _install(monkeypatch, fake, enabled=False)
    with TestClient(app_module.app) as c:
        assert fake.starts == 0
        assert c.get("/api/ledger").json()["cover"] is False


def test_no_cover_without_b_router(monkeypatch):
    for name in ("start_cover", "stop_cover", "cover_running"):
        monkeypatch.setattr(app_module, name, None)
    with TestClient(app_module.app) as c:
        assert c.get("/api/ledger").json()["cover"] is False


def test_ui_shows_cover_state():
    html = (app_module.UI_DIR / "index.html").read_text()
    assert 'id="live-cover"' in html


@pytest.mark.skipif(not REAL_COVER, reason="needs B's router (integrated build)")
def test_real_cover_sends_cover_rows_with_no_personal_fields(monkeypatch):
    monkeypatch.setenv("GV_COVER_INTERVAL_S", "0.05")
    with TestClient(app_module.app) as c:
        deadline = time.time() + 5
        rows = []
        while time.time() < deadline and not rows:
            rows = [e for e in c.get("/api/ledger").json()["entries"] if e["kind"] == "cover"]
            time.sleep(0.05)
        assert rows, "cover traffic shows up in the ledger"
        assert all(e["bytes_out"] > 0 and e["personal_fields_sent"] == 0 for e in rows)
        out = c.get(f"/api/ledger/{rows[0]['seq']}/outbound").json()
        assert len(out["texts"]) == 8 and out["mine"] == []   # cover: nothing in it is the user's
    assert app_module.cover_running() is False
