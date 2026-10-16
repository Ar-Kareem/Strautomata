
import random
from collections import deque
from typing import List, Tuple, Dict

# Fleet (standard): 5, 4, 3, 3, 2
FLEET = (5, 4, 3, 3, 2)
N = 10

# ---- Bitmask helpers over 100 cells (Python int supports big bitmasks) ----
def _idx(r: int, c: int) -> int:
    return r * N + c

def _rc(i: int) -> Tuple[int, int]:
    return divmod(i, N)

def _bit(i: int) -> int:
    return 1 << i

# Precompute all placements for each ship length as (mask, indices_list)
PLACEMENTS: Dict[int, List[Tuple[int, Tuple[int, ...]]]] = {L: [] for L in set(FLEET)}
for L in set(FLEET):
    # Horizontal
    for r in range(N):
        for c0 in range(N - L + 1):
            idxs = tuple(_idx(r, c0 + k) for k in range(L))
            m = 0
            for i in idxs:
                m |= _bit(i)
            PLACEMENTS[L].append((m, idxs))
    # Vertical
    for c in range(N):
        for r0 in range(N - L + 1):
            idxs = tuple(_idx(r0 + k, c) for k in range(L))
            m = 0
            for i in idxs:
                m |= _bit(i)
            PLACEMENTS[L].append((m, idxs))


def _board_seed(board: List[List[int]]) -> int:
    # Deterministic seed from board content
    flat = []
    for r in range(N):
        flat.extend(board[r])
    h = 2166136261
    for v in flat:
        h ^= (v + 2)  # map -1,0,1 to 1,2,3
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def _masks_from_board(board: List[List[int]]) -> Tuple[int, int, List[int]]:
    missmask = 0
    hitmask = 0
    unknown = []
    for r in range(N):
        row = board[r]
        for c in range(N):
            v = row[c]
            i = _idx(r, c)
            if v == -1:
                missmask |= _bit(i)
            elif v == 1:
                hitmask |= _bit(i)
            else:
                unknown.append(i)
    return missmask, hitmask, unknown


def _hit_components(board: List[List[int]]) -> List[List[int]]:
    seen = [[False] * N for _ in range(N)]
    comps: List[List[int]] = []
    for r in range(N):
        for c in range(N):
            if board[r][c] != 1 or seen[r][c]:
                continue
            q = deque([(r, c)])
            seen[r][c] = True
            comp: List[int] = []
            while q:
                rr, cc = q.popleft()
                comp.append(_idx(rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < N and 0 <= nc < N and (not seen[nr][nc]) and board[nr][nc] == 1:
                        seen[nr][nc] = True
                        q.append((nr, nc))
            comps.append(comp)
    return comps


def _neighbors(i: int) -> List[int]:
    r, c = _rc(i)
    out = []
    if r > 0:
        out.append(_idx(r - 1, c))
    if r < N - 1:
        out.append(_idx(r + 1, c))
    if c > 0:
        out.append(_idx(r, c - 1))
    if c < N - 1:
        out.append(_idx(r, c + 1))
    return out


def _exact_heat_no_hits(missmask: int, board: List[List[int]]) -> List[float]:
    # Exact placement counting when there are no hits: strong hunt behavior
    heat = [0.0] * (N * N)
    # Pre-filter placements that don't cover misses
    for L in FLEET:
        for m, idxs in PLACEMENTS[L]:
            if m & missmask:
                continue
            for i in idxs:
                r, c = _rc(i)
                if board[r][c] == 0:
                    heat[i] += 1.0
    return heat


def _monte_carlo_heat(
    missmask: int,
    hitmask: int,
    board: List[List[int]],
    rng: random.Random,
    target_samples: int = 500,
    max_attempts: int = 8000,
) -> Tuple[List[float], int]:
    # Monte Carlo estimate of occupancy probabilities, consistent with hits/misses
    heat = [0.0] * (N * N)

    # Pre-filter placements by missmask for each length for speed
    placements_nomiss: Dict[int, List[Tuple[int, Tuple[int, ...]]]] = {}
    for L in set(FLEET):
        lst = []
        for m, idxs in PLACEMENTS[L]:
            if m & missmask:
                continue
            lst.append((m, idxs))
        placements_nomiss[L] = lst

    lengths = sorted(FLEET, reverse=True)

    accepted = 0
    attempts = 0

    # If there are many hits, bias ship placement to cover remaining hits early
    while attempts < max_attempts and accepted < target_samples:
        attempts += 1
        occ = 0
        fleetmask = 0
        remaining_hits = hitmask

        ok = True
        for L in lengths:
            candidates = placements_nomiss[L]
            # Filter by non-overlap
            # Bias: if remaining_hits exist, prefer placements that cover at least one remaining hit
            want_cover = (remaining_hits != 0) and (rng.random() < 0.85)

            pick = None
            # Try a few random picks before giving up to avoid O(K) scans too often
            for _ in range(40):
                m, idxs = candidates[rng.randrange(len(candidates))]
                if m & occ:
                    continue
                if want_cover and (m & remaining_hits) == 0:
                    continue
                pick = (m, idxs)
                break

            if pick is None:
                # Fallback to a short scan
                # First try cover-remaining if desired, else any non-overlapping
                found = None
                if want_cover:
                    for m, idxs in candidates:
                        if (m & occ) == 0 and (m & remaining_hits) != 0:
                            found = (m, idxs)
                            break
                if found is None:
                    for m, idxs in candidates:
                        if (m & occ) == 0:
                            found = (m, idxs)
                            break
                if found is None:
                    ok = False
                    break
                pick = found

            m, idxs = pick
            occ |= m
            fleetmask |= m
            remaining_hits &= ~m  # hits covered by this ship

        if not ok:
            continue
        if remaining_hits != 0:
            continue  # not all hits covered

        accepted += 1
        # Add probability mass to unknown cells occupied by ships in this sample
        # (also fine if a ship covers already-hit cells; we only score unknown for choosing next shot)
        for i in range(N * N):
            if (fleetmask >> i) & 1:
                r, c = _rc(i)
                if board[r][c] == 0:
                    heat[i] += 1.0

    return heat, accepted


def _target_boost_scores(board: List[List[int]], missmask: int) -> List[float]:
    # Score unknown cells adjacent to hits by counting compatible placements that include (hit & candidate).
    # This tends to finish ships quickly.
    boost = [0.0] * (N * N)

    hits = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1:
                hits.append(_idx(r, c))
    if not hits:
        return boost

    # Pre-filter placements by missmask once
    placements_nomiss = {L: [p for p in PLACEMENTS[L] if (p[0] & missmask) == 0] for L in set(FLEET)}

    # Candidate set: unknown neighbors of hits
    cand_set = set()
    for h in hits:
        for nb in _neighbors(h):
            rr, cc = _rc(nb)
            if board[rr][cc] == 0:
                cand_set.add(nb)

    # Extra: cells that bridge two hits in line (hit-0-hit) get a large boost
    for r in range(N):
        for c in range(N - 2):
            if board[r][c] == 1 and board[r][c + 2] == 1 and board[r][c + 1] == 0:
                boost[_idx(r, c + 1)] += 50.0
    for c in range(N):
        for r in range(N - 2):
            if board[r][c] == 1 and board[r + 2][c] == 1 and board[r + 1][c] == 0:
                boost[_idx(r + 1, c)] += 50.0

    # Component-based extension preference: if a component is a straight line, favor end extensions
    comps = _hit_components(board)
    end_favor = set()
    for comp in comps:
        if len(comp) < 2:
            continue
        coords = [_rc(i) for i in comp]
        rows = {r for r, _ in coords}
        cols = {c for _, c in coords}
        if len(rows) == 1:
            r = next(iter(rows))
            minc = min(c for _, c in coords)
            maxc = max(c for _, c in coords)
            left = _idx(r, minc - 1) if minc - 1 >= 0 else None
            right = _idx(r, maxc + 1) if maxc + 1 < N else None
            if left is not None and board[r][minc - 1] == 0:
                end_favor.add(left)
            if right is not None and board[r][maxc + 1] == 0:
                end_favor.add(right)
        elif len(cols) == 1:
            c = next(iter(cols))
            minr = min(r for r, _ in coords)
            maxr = max(r for r, _ in coords)
            up = _idx(minr - 1, c) if minr - 1 >= 0 else None
            down = _idx(maxr + 1, c) if maxr + 1 < N else None
            if up is not None and board[minr - 1][c] == 0:
                end_favor.add(up)
            if down is not None and board[maxr + 1][c] == 0:
                end_favor.add(down)

    # Count placements that include both candidate and an adjacent hit
    for cand in cand_set:
        cand_r, cand_c = _rc(cand)
        adj_hits = []
        for nb in _neighbors(cand):
            rr, cc = _rc(nb)
            if board[rr][cc] == 1:
                adj_hits.append(nb)
        if not adj_hits:
            continue

        score = 0.0
        cand_bit = _bit(cand)
        for L in FLEET:
            for m, _ in placements_nomiss[L]:
                if (m & cand_bit) == 0:
                    continue
                # include at least one adjacent hit
                for h in adj_hits:
                    if m & _bit(h):
                        score += 1.0
                        break

        # Favor inferred end extensions
        if cand in end_favor:
            score *= 2.5

        boost[cand] += score

    return boost


def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Defensive: ensure we always return a legal move
    if not board or len(board) != N or any(len(row) != N for row in board):
        return (0, 0)

    missmask, hitmask, unknown = _masks_from_board(board)
    if not unknown:
        # No legal moves; return something valid in range
        return (0, 0)

    rng = random.Random(_board_seed(board))

    # Compute base heatmap
    if hitmask == 0:
        heat = _exact_heat_no_hits(missmask, board)
    else:
        heat, accepted = _monte_carlo_heat(missmask, hitmask, board, rng)
        # If MC failed (rare but possible), fall back to something reasonable
        if accepted == 0:
            heat = [0.0] * (N * N)

    # Add strong local targeting boost when hits exist
    if hitmask != 0:
        boost = _target_boost_scores(board, missmask)
        # Combine: boost is scaled to dominate when appropriate
        for i in range(N * N):
            heat[i] += 6.0 * boost[i]

    # Choose best unknown cell (tie-break deterministically via rng)
    best_val = None
    best_cells = []
    for i in unknown:
        v = heat[i]
        if best_val is None or v > best_val:
            best_val = v
            best_cells = [i]
        elif v == best_val:
            best_cells.append(i)

    if not best_cells:
        # Absolute fallback
        i = unknown[0]
        return _rc(i)

    choice = best_cells[rng.randrange(len(best_cells))]

    r, c = _rc(choice)
    # Final legality check: if chosen is somehow invalid, pick first unknown
    if board[r][c] != 0:
        i = unknown[0]
        return _rc(i)
    return (r, c)
