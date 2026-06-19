"""Local, encrypted-at-rest "DNA" vector store backed by SQLite.

Every successful trade, failed UI interaction, and Zone-2 decision is recorded
here. Retrieval uses a dependency-free bag-of-words cosine similarity so the
store runs anywhere; a production deployment can swap in a real local vector DB
(e.g. ChromaDB) behind the same interface via the ``aegis[vector]`` extra.

NOTE ON ENCRYPTION: the bundled :class:`XorCipher` is a *stand-in* for real
at-rest encryption (it makes the on-disk text non-plaintext but is NOT secure).
Production should bind to an OS keychain / a vetted AEAD cipher. The interface is
deliberately pluggable so swapping it does not touch call sites.
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class Cipher:
    """At-rest cipher interface."""

    def encrypt(self, plaintext: str) -> bytes:  # pragma: no cover - trivial
        return plaintext.encode("utf-8")

    def decrypt(self, blob: bytes) -> str:  # pragma: no cover - trivial
        return blob.decode("utf-8")


class XorCipher(Cipher):
    """Keystream XOR — a placeholder for real disk encryption (NOT secure)."""

    def __init__(self, key: str) -> None:
        self._seed = hashlib.sha256(key.encode("utf-8")).digest()

    def _keystream(self, n: int) -> bytes:
        out = bytearray()
        counter = 0
        while len(out) < n:
            out += hashlib.sha256(self._seed + counter.to_bytes(8, "big")).digest()
            counter += 1
        return bytes(out[:n])

    def encrypt(self, plaintext: str) -> bytes:
        data = plaintext.encode("utf-8")
        ks = self._keystream(len(data))
        return bytes(b ^ k for b, k in zip(data, ks))

    def decrypt(self, blob: bytes) -> str:
        ks = self._keystream(len(blob))
        return bytes(b ^ k for b, k in zip(blob, ks)).decode("utf-8")


@dataclass
class CrystalRecord:
    """One crystallised memory of an Aegis interaction."""

    kind: str            # "trade" | "ui_nav" | "approval" | ...
    description: str
    payload: dict = field(default_factory=dict)
    ts: float = field(default_factory=time.time)
    score: float = 0.0   # populated by search()


def _tokenize(text: str) -> Counter:
    return Counter(t for t in text.lower().split() if t.isalnum() or "_" in t)


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


class DNAStore:
    """SQLite-backed, encrypted-at-rest memory with bag-of-words retrieval."""

    def __init__(self, path: str | Path = ":memory:", cipher: Optional[Cipher] = None) -> None:
        self.path = str(path)
        self.cipher = cipher or Cipher()
        # The daemon is concurrent (telemetry thread + threadpool-served API), so
        # the DNA memory is written from many threads. A single sqlite connection
        # is not safe for concurrent use, so we open it cross-thread and serialise
        # every access behind a lock.
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._lock = threading.Lock()
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS dna ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " kind TEXT NOT NULL,"
            " ts REAL NOT NULL,"
            " blob BLOB NOT NULL)"
        )
        self._conn.commit()

    def remember(self, record: CrystalRecord) -> int:
        doc = json.dumps(
            {"kind": record.kind, "description": record.description, "payload": record.payload, "ts": record.ts}
        )
        blob = self.cipher.encrypt(doc)
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO dna (kind, ts, blob) VALUES (?, ?, ?)",
                (record.kind, record.ts, blob),
            )
            self._conn.commit()
            return int(cur.lastrowid)

    def _all(self) -> list[CrystalRecord]:
        with self._lock:
            rows = self._conn.execute("SELECT blob FROM dna ORDER BY ts DESC").fetchall()
        out: list[CrystalRecord] = []
        for (blob,) in rows:
            # A single corrupt row, or one written under a different key, must not
            # take down the whole memory: skip what we cannot decrypt/parse.
            try:
                doc = json.loads(self.cipher.decrypt(blob))
                out.append(
                    CrystalRecord(
                        kind=doc["kind"],
                        description=doc["description"],
                        payload=doc["payload"],
                        ts=doc["ts"],
                    )
                )
            except (UnicodeDecodeError, ValueError, KeyError):
                continue
        return out

    def search(self, query: str, *, kind: Optional[str] = None, top_k: int = 5) -> list[CrystalRecord]:
        q = _tokenize(query)
        scored: list[CrystalRecord] = []
        for rec in self._all():
            if kind and rec.kind != kind:
                continue
            rec.score = _cosine(q, _tokenize(rec.description))
            if rec.score > 0:
                scored.append(rec)
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

    def count(self) -> int:
        with self._lock:
            return int(self._conn.execute("SELECT COUNT(*) FROM dna").fetchone()[0])

    def close(self) -> None:
        with self._lock:
            self._conn.close()
