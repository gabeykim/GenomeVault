"""M2 graph: the on-device health graph in SQLite (PLAN F1, M2). Never leaves the device (I2, I3).

``load_profile()`` (CONTRACTS, owner A) returns Alex's Profile with lab staleness set: a lab dated
more than 90 days before *today* has ``stale=True``. *today* is ``date.today()`` unless the
``GV_TODAY`` env var (ISO date) pins it, so a demo or test can be replayed on a fixed date.

Storage: if ``GV_GRAPH_DB`` names a SQLite file, the graph is read from it (built from ``data/`` by
``ingest`` the first time). Otherwise the graph is built fresh in memory on each call, which keeps
the repo free of generated files and is fast enough for per-request use (tiny tables).
"""
from __future__ import annotations

import os
import pathlib
import sqlite3
from datetime import date, timedelta
from typing import Optional

from . import ingest
from .contracts import Drug, Lab, Profile

STALE_DAYS = 90

SCHEMA = """
CREATE TABLE IF NOT EXISTS gene      (gene TEXT PRIMARY KEY, genotype TEXT NOT NULL, phenotype TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS med       (ingredient TEXT NOT NULL, dose_mg REAL);
CREATE TABLE IF NOT EXISTS condition (name TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS allergy   (name TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS lab       (test TEXT NOT NULL, value REAL NOT NULL, unit TEXT NOT NULL, date TEXT NOT NULL);
"""


def today() -> date:
    pinned = os.getenv("GV_TODAY")
    return date.fromisoformat(pinned) if pinned else date.today()


def is_stale(lab_date: date, on: date) -> bool:
    return lab_date < on - timedelta(days=STALE_DAYS)


def save(profile: Profile, conn: sqlite3.Connection) -> None:
    """Replace the graph's contents with *profile* (stale flags are derived on read, not stored)."""
    conn.executescript(SCHEMA)
    with conn:
        for t in ("gene", "med", "condition", "allergy", "lab"):
            conn.execute(f"DELETE FROM {t}")
        conn.executemany("INSERT INTO gene VALUES (?,?,?)",
                         [(g, gt, profile.phenotypes.get(g, ingest.INDETERMINATE))
                          for g, gt in profile.genotypes.items()])
        conn.executemany("INSERT INTO med VALUES (?,?)", [(m.ingredient, m.dose_mg) for m in profile.meds])
        conn.executemany("INSERT INTO condition VALUES (?)", [(c,) for c in profile.conditions])
        conn.executemany("INSERT INTO allergy VALUES (?)", [(a,) for a in profile.allergies])
        conn.executemany("INSERT INTO lab VALUES (?,?,?,?)",
                         [(l.test, l.value, l.unit, l.date.isoformat()) for l in profile.labs])


def read(conn: sqlite3.Connection, on: Optional[date] = None) -> Profile:
    on = on or today()
    genes = conn.execute("SELECT gene, genotype, phenotype FROM gene ORDER BY rowid").fetchall()
    labs = [Lab(test=t, value=v, unit=u, date=date.fromisoformat(d), stale=is_stale(date.fromisoformat(d), on))
            for t, v, u, d in conn.execute("SELECT test, value, unit, date FROM lab ORDER BY rowid")]
    return Profile(
        genotypes={g: gt for g, gt, _ in genes},
        phenotypes={g: ph for g, _, ph in genes},
        meds=[Drug(ingredient=i, dose_mg=d) for i, d in conn.execute("SELECT ingredient, dose_mg FROM med ORDER BY rowid")],
        conditions=[c for (c,) in conn.execute("SELECT name FROM condition ORDER BY rowid")],
        allergies=[a for (a,) in conn.execute("SELECT name FROM allergy ORDER BY rowid")],
        labs=labs,
    )


def build(db: str | pathlib.Path = ":memory:", vcf=ingest.VCF, records=ingest.RECORDS) -> sqlite3.Connection:
    """Ingest the VCF + records (M1) into a SQLite graph and return the open connection."""
    conn = sqlite3.connect(str(db))
    save(ingest.ingest(vcf, records), conn)
    return conn


def load_profile(db: Optional[str | pathlib.Path] = None, on: Optional[date] = None) -> Profile:
    """CONTRACTS ``graph.load_profile() -> Profile``. Optional args are local extras for tests."""
    conn = sqlite3.connect(str(db or os.getenv("GV_GRAPH_DB") or ":memory:"))
    try:
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='gene'").fetchone():
            save(ingest.ingest(), conn)               # first use: ingest data/ into the graph (M1)
        return read(conn, on)
    finally:
        conn.close()
