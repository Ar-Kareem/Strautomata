
# Battleship policy for a 10x10 board.
# Required API:
#   policy(board: list[list[int]]) -> tuple[int, int]

SIZE = 10
FLEET = (5, 4, 3, 3, 2)
UNIQUE_LENGTHS = tuple(sorted(set(FLEET)))


def _make_segments(length):
    segs = []

    # Horizontal placements
    for r in range(SIZE):
        base = r * SIZE
        for c in range(SIZE - length + 1):
            segs.append(tuple(base + c + k for k in range(length)))

    # Vertical placements
    for r in range(SIZE - length + 1):
        for c in range(SIZE):
            segs.append(tuple((r + k) * SIZE + c for k in range(length)))

    return tuple(segs)


_SEGMENTS_BY_LEN = {L: _make_segments(L) for L in UNIQUE_LENGTHS}
_SEGMENTS_WITH_MULTIPLICITY = tuple(
    (L, cells) for L in FLEET for cells in _SEGMENTS_BY_LEN[L]
)

_ADJ = []
for idx in range(SIZE * SIZE):
    r, c = divmod(idx, SIZE)
    nbs = []
    if r > 0:
        nbs.append((r - 1) * SIZE + c)
    if r + 1 < SIZE:
        nbs.append((r + 1) * SIZE + c)
    if c > 0:
        nbs.append(r * SIZE + c - 1)
    if c + 1 < SIZE:
        nbs.append(r * SIZE + c + 1)
    _ADJ.append(tuple(nbs))
_ADJ = tuple(_ADJ)

# For scoring isolated hits: all legal ship segments containing an adjacent pair.
_PAIR_SEGMENTS = {(i, j): [] for i in range(SIZE * SIZE) for j in _ADJ[i]}
for L, cells in _SEGMENTS_WITH_MULTIPLICITY:
    s = set(cells)
    for i in cells:
        for j in _ADJ[i]:
            if j in s:
                _PAIR_SEGMENTS[(i, j)].append((L, cells))
_PAIR_SEGMENTS = {k: tuple(v) for k, v in _PAIR_SEGMENTS.items()}


def _fallback(board):
    """Return the first legal unknown cell if anything unexpected happens."""
    try:
        for r in range(SIZE):
            for c in range(SIZE):
                if board[r][c] == 0:
                    return (r, c)
    except Exception:
        pass
    return (0, 0)


def _center_bonus(idx):
    r, c = divmod(idx, SIZE)
    return 10.0 - (abs(r - 4.5) + abs(c - 4.5))


def _hunt_heat(flat):
    """
    Probability-style heat map for undiscovered ships.

    For each ship, every placement that lies entirely on unknown cells is treated
    as possible. Placements are normalized per ship length so each ship
    contributes comparable total probability mass.
    """
    heat = [0.0] * (SIZE * SIZE)

    for L in FLEET:
        valid = []
        for cells in _SEGMENTS_BY_LEN[L]:
            ok = True
            for idx in cells:
                if flat[idx] != 0:
                    ok = False
                    break
            if ok:
                valid.append(cells)

        if not valid:
            continue

        w = 1.0 / len(valid)
        for cells in valid:
            for idx in cells:
                heat[idx] += w

    return heat


def _line_target(flat):
    """
    Score cells that complete or extend a known line of hits.

    Any segment with at least two hits and no misses is considered a possible
    ship. Unknown cells between hits are scored highest, then immediate
    extensions, then farther cells in the same possible segment.
    """
    scores = [0.0] * (SIZE * SIZE)
    line_members = set()

    for L in FLEET:
        for cells in _SEGMENTS_BY_LEN[L]:
            hit_pos = []
            unk_pos = []
            bad = False

            for p, idx in enumerate(cells):
                v = flat[idx]
                if v == -1:
                    bad = True
                    break
                if v == 1:
                    hit_pos.append(p)
                elif v == 0:
                    unk_pos.append(p)

            if bad or len(hit_pos) < 2:
                continue

            for p in hit_pos:
                line_members.add(cells[p])

            if not unk_pos:
                continue

            k = len(hit_pos)
            mn = hit_pos[0]
            mx = hit_pos[-1]
            span = mx - mn + 1
            density = k / float(span)

            base = 200000.0 * k * k * (1.0 + density)

            for p in unk_pos:
                if mn < p < mx:
                    # Fill a gap between known hits.
                    mult = 6.0
                else:
                    # Extend a line, preferring the immediately adjacent end.
                    d = min(abs(p - mn), abs(p - mx))
                    mult = 3.0 if d == 1 else 1.0 / float(d)

                scores[cells[p]] += base * mult

    return scores, line_members


def _isolated_target(flat, hits, line_members, hunt):
    """
    Score cells adjacent to isolated hits.

    Hits that are already part of a multi-hit line are excluded here; those are
    handled by _line_target. For isolated hits, adjacent unknown cells are ranked
    by how many ship placements can contain both the hit and that adjacent cell.
    """
    scores = [0.0] * (SIZE * SIZE)

    for h in hits:
        if h in line_members:
            continue

        for nb in _ADJ[h]:
            if flat[nb] != 0:
                continue

            cnt = 0
            length_sum = 0.0

            for L, cells in _PAIR_SEGMENTS.get((h, nb), ()):
                ok = True
                for idx in cells:
                    if flat[idx] == -1:
                        ok = False
                        break
                if ok:
                    cnt += 1
                    length_sum += L

            if cnt:
                scores[nb] += 75000.0
                scores[nb] += 12000.0 * cnt
                scores[nb] += 3000.0 * length_sum
                scores[nb] += 1000.0 * hunt[nb]

    return scores


def _choose_positive(scores, flat, tiebreak=None):
    best_idx = -1
    best_val = None

    for idx, s in enumerate(scores):
        if flat[idx] != 0 or s <= 0.0:
            continue

        tb = tiebreak[idx] if tiebreak is not None else 0.0
        val = (s, tb, _center_bonus(idx), -idx)

        if best_val is None or val > best_val:
            best_val = val
            best_idx = idx

    return best_idx


def _choose_hunt(flat, heat):
    """
    Choose a hunt-mode shot from the probability heatmap.

    A mild checkerboard preference helps discover ships efficiently because the
    smallest ship has length 2, but the probability heat still dominates.
    """
    totals = [0.0, 0.0]
    for idx, v in enumerate(flat):
        if v == 0:
            r, c = divmod(idx, SIZE)
            totals[(r + c) & 1] += heat[idx]

    preferred_parity = 0 if totals[0] >= totals[1] else 1

    best_idx = -1
    best_val = None

    for idx, v in enumerate(flat):
        if v != 0:
            continue

        r, c = divmod(idx, SIZE)
        raw = heat[idx]
        score = raw

        if raw > 0.0:
            if ((r + c) & 1) == preferred_parity:
                score *= 1.30
            else:
                score *= 0.90

        local_open = 0
        for nb in _ADJ[idx]:
            if flat[nb] == 0:
                local_open += 1

        val = (score, raw, local_open, _center_bonus(idx), -idx)

        if best_val is None or val > best_val:
            best_val = val
            best_idx = idx

    if best_idx >= 0:
        return best_idx

    # Should only happen if there are no legal cells.
    return 0


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        flat = []
        for r in range(SIZE):
            row = board[r]
            for c in range(SIZE):
                flat.append(row[c])

        has_unknown = False
        hits = []
        for idx, v in enumerate(flat):
            if v == 0:
                has_unknown = True
            elif v == 1:
                hits.append(idx)

        if not has_unknown:
            return (0, 0)

        hunt = _hunt_heat(flat)

        if hits:
            # First priority: extend/fill any line with multiple hits.
            line_scores, line_members = _line_target(flat)
            idx = _choose_positive(line_scores, flat, hunt)
            if idx >= 0:
                return divmod(idx, SIZE)

            # Second priority: chase isolated single hits.
            isolated_scores = _isolated_target(flat, hits, line_members, hunt)
            idx = _choose_positive(isolated_scores, flat, hunt)
            if idx >= 0:
                return divmod(idx, SIZE)

        # Otherwise hunt using global placement density.
        idx = _choose_hunt(flat, hunt)
        if flat[idx] == 0:
            return divmod(idx, SIZE)

        return _fallback(board)

    except Exception:
        return _fallback(board)
