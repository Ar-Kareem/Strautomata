"""Compact binary replay files for the Match Viewer (written by export_history, read by the viewer).

Layout under ``public/history/`` (``replays/`` is gitignored, the lock file is committed)::

    replays/<game>_<world>/<stage>/vocab.json      every distinct action of the stage, as JSON values
    replays/<game>_<world>/<stage>/<botA>.rpl      every match of every pair (botA, botB) with botA < botB
    replays.lock.json                              content hash of replays/ (names the release asset)

A ``.rpl`` file is gzip over::

    "RPL1"  varint(len(header))  header (UTF-8 JSON)  match records

``header = {"bot": botA, "pairs": [[botB, n_matches], ...], "extras": [{...}, ...]}``; the records
follow in ``pairs`` order, matching the ``detail`` slot of each row in ``matches.json``.  One record::

    varint n_plies
    varint players     0/1 = strictly alternating starting with that player, 2 = explicit list follows
    [varint player] * n_plies               (only when players == 2)
    varint action_id * n_plies              (index into vocab.json)
    varint think * n_plies                  (0 = unknown, else centiseconds + 1)
    varint extras                           (0 = none, else index + 1 into header["extras"])
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional

MAGIC = b"RPL1"
EXPLICIT_PLAYERS = 2
REPLAYS_DIR = "replays"
LOCK_FILE = "replays.lock.json"
RELEASE_PREFIX = "replays-"


def _varint(n: int, out: bytearray) -> None:
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return


def _read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    n = shift = 0
    while True:
        b = buf[pos]
        pos += 1
        n |= (b & 0x7F) << shift
        if b < 0x80:
            return n, pos
        shift += 7


class Vocab:
    """Action <-> id table shared by all replay files of one stage."""

    def __init__(self) -> None:
        self.ids: dict[str, int] = {}
        self.values: list[Any] = []

    def id(self, action: Any) -> int:
        key = json.dumps(action, separators=(",", ":"), ensure_ascii=False)
        i = self.ids.get(key)
        if i is None:
            i = self.ids[key] = len(self.values)
            self.values.append(action)
        return i


class ReplayFileWriter:
    """Accumulates the encoded matches of one ``.rpl`` file (all pairs of one bot)."""

    def __init__(self, bot: str, vocab: Vocab) -> None:
        self.bot = bot
        self.vocab = vocab
        self.pairs: dict[str, bytearray] = {}
        self.counts: dict[str, int] = {}
        self.extras: dict[str, int] = {}

    def add(self, other: str, players: list[int], actions: list[Any], think: list[Optional[float]],
            extras: Optional[dict[str, Any]]) -> int:
        """Append one match against ``other``; returns its slot within that pair."""
        buf = self.pairs.setdefault(other, bytearray())
        _varint(len(actions), buf)
        first = players[0] if players else 0
        if first in (0, 1) and all(p == (first + i) % 2 for i, p in enumerate(players)):
            _varint(first, buf)
        else:
            _varint(EXPLICIT_PLAYERS, buf)
            for p in players:
                _varint(p, buf)
        for a in actions:
            _varint(self.vocab.id(a), buf)
        for t in think:
            _varint(0 if t is None else max(0, round(t * 100)) + 1, buf)
        ref = 0
        if extras:
            key = json.dumps(extras, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
            ref = self.extras.setdefault(key, len(self.extras)) + 1
        _varint(ref, buf)
        slot = self.counts.get(other, 0)
        self.counts[other] = slot + 1
        return slot

    def write(self, path: Path) -> int:
        header = {
            "bot": self.bot,
            "pairs": [[other, self.counts[other]] for other in self.pairs],
            "extras": [json.loads(k) for k in self.extras],
        }
        head = json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        out = bytearray(MAGIC)
        _varint(len(head), out)
        out += head
        for buf in self.pairs.values():
            out += buf
        data = gzip.compress(bytes(out), compresslevel=9, mtime=0)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return len(data)


def write_vocab(path: Path, vocab: Vocab) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(vocab.values, separators=(",", ":"), ensure_ascii=False)
    path.write_text(text, encoding="utf-8")
    return len(text.encode("utf-8"))


def read_replay_file(path: Path, vocab: list[Any]) -> dict[str, list[dict[str, Any]]]:
    """Decode a ``.rpl`` file into ``{botB: [{"moves": [[player, action], ...], "think": [...], **extras}]}``."""
    buf = gzip.decompress(path.read_bytes())
    assert buf[:4] == MAGIC, f"{path}: not a replay file"
    n, pos = _read_varint(buf, 4)
    header = json.loads(buf[pos:pos + n].decode("utf-8"))
    pos += n
    out: dict[str, list[dict[str, Any]]] = {}
    for other, count in header["pairs"]:
        matches = out.setdefault(other, [])
        for _ in range(count):
            plies, pos = _read_varint(buf, pos)
            mode, pos = _read_varint(buf, pos)
            if mode == EXPLICIT_PLAYERS:
                players = []
                for _ in range(plies):
                    p, pos = _read_varint(buf, pos)
                    players.append(p)
            else:
                players = [(mode + i) % 2 for i in range(plies)]
            moves = []
            for p in players:
                a, pos = _read_varint(buf, pos)
                moves.append([p, vocab[a]])
            think = []
            for _ in range(plies):
                t, pos = _read_varint(buf, pos)
                think.append(None if t == 0 else (t - 1) / 100)
            ref, pos = _read_varint(buf, pos)
            extras = header["extras"][ref - 1] if ref else {}
            matches.append({"moves": moves, "think": think, **extras})
    return out


def tree_hash(root: Path) -> str:
    """Content hash of a directory, independent of timestamps (mirrored in scripts/check_replays.cjs)."""
    lines = []
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            p = Path(dirpath) / name
            lines.append(f"{p.relative_to(root).as_posix()}\0{hashlib.sha256(p.read_bytes()).hexdigest()}\n")
    return hashlib.sha256("".join(sorted(lines)).encode("utf-8")).hexdigest()[:16]


def write_lock(history: Path) -> dict[str, Any]:
    root = history / REPLAYS_DIR
    files = [p for p in root.rglob("*") if p.is_file()]
    lock = {"hash": tree_hash(root), "files": len(files), "bytes": sum(p.stat().st_size for p in files)}
    (history / LOCK_FILE).write_text(json.dumps(lock, indent=2) + "\n")
    return lock
