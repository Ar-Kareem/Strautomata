
from __future__ import annotations

from collections import deque

N = 19
POINTS = N * N


def _to_idx(r: int, c: int) -> int:
    return (r - 1) * N + (c - 1)


def _in_board(r: int, c: int) -> bool:
    return 1 <= r <= N and 1 <= c <= N


COORDS: list[tuple[int, int]] = []
NEIGHBORS: list[list[int]] = []
DIAGONALS: list[list[int]] = []

for _r in range(1, N + 1):
    for _c in range(1, N + 1):
        COORDS.append((_r, _c))

for _i, (_r, _c) in enumerate(COORDS):
    ns = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = _r + dr, _c + dc
        if _in_board(rr, cc):
            ns.append(_to_idx(rr, cc))
    NEIGHBORS.append(ns)

    ds = []
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        rr, cc = _r + dr, _c + dc
        if _in_board(rr, cc):
            ds.append(_to_idx(rr, cc))
    DIAGONALS.append(ds)


def _transform_corner(r: int, c: int, corner: int) -> tuple[int, int]:
    # 0 NW, 1 NE, 2 SW, 3 SE
    if corner >= 2:
        r = N + 1 - r
    if corner % 2 == 1:
        c = N + 1 - c
    return r, c


STAR_POINTS = {_to_idx(r, c) for r in (4, 10, 16) for c in (4, 10, 16)}
CENTER = _to_idx(10, 10)
CORNER_HOSHI = {
    _to_idx(4, 4),
    _to_idx(4, 16),
    _to_idx(16, 4),
    _to_idx(16, 16),
}
SIDE_HOSHI = STAR_POINTS - CORNER_HOSHI - {CENTER}

THREE_FOUR = set()
THREE_THREE = set()
for _corner in range(4):
    THREE_THREE.add(_to_idx(*_transform_corner(3, 3, _corner)))
    for _p in ((3, 4), (4, 3)):
        THREE_FOUR.add(_to_idx(*_transform_corner(_p[0], _p[1], _corner)))

_BASE_CORNER_MOVES = (
    (4, 4), (3, 4), (4, 3), (3, 3),
    (5, 3), (3, 5), (5, 4), (4, 5),
)
_BASE_APPROACH = (
    (4, 6), (6, 4), (3, 6), (6, 3),
    (5, 6), (6, 5), (4, 7), (7, 4),
)
_BASE_EXTENSION = (
    (4, 10), (10, 4), (3, 10), (10, 3),
    (5, 10), (10, 5),
)

CORNERS = []
for _corner in range(4):
    region = set()
    for rr in range(1, 8):
        for cc in range(1, 8):
            region.add(_to_idx(*_transform_corner(rr, cc, _corner)))

    hoshi = _to_idx(*_transform_corner(4, 4, _corner))
    corner_moves = {
        _to_idx(*_transform_corner(r, c, _corner)) for r, c in _BASE_CORNER_MOVES
    }
    approach = {
        _to_idx(*_transform_corner(r, c, _corner)) for r, c in _BASE_APPROACH
    }
    extension = {
        _to_idx(*_transform_corner(r, c, _corner)) for r, c in _BASE_EXTENSION
    }
    three_three = _to_idx(*_transform_corner(3, 3, _corner))
    CORNERS.append((region, hoshi, corner_moves, approach, extension, three_three))


_OPEN_LINE = [0.0, -140.0, -45.0, 48.0, 68.0, 38.0, 18.0, 7.0, 2.0, 0.0, 1.0]
_MID_LINE = [0.0, -75.0, -6.0, 28.0, 38.0, 24.0, 12.0, 4.0, 1.0, 0.0, 0.0]
_END_LINE = [0.0, -24.0, 8.0, 14.0, 10.0, 4.0, 1.0, 0.0, 0.0, 0.0, 0.0]


_INFLUENCE_WEIGHTS = [0.0, 3.2, 1.8, 1.05, 0.60, 0.35, 0.20]
INFLUENCE_NEAR: list[list[tuple[int, float]]] = []

for i, (r, c) in enumerate(COORDS):
    arr = []
    for dr in range(-6, 7):
        for dc in range(-6, 7):
            d = abs(dr) + abs(dc)
            if d == 0 or d > 6:
                continue
            rr, cc = r + dr, c + dc
            if _in_board(rr, cc):
                arr.append((_to_idx(rr, cc), _INFLUENCE_WEIGHTS[d]))
    INFLUENCE_NEAR.append(arr)


def _state_or_none(x):
    if isinstance(x, (tuple, list)) and len(x) == 2 and isinstance(x[0], int) and isinstance(x[1], int):
        return (x[0], x[1])
    return None


def _make_board(me, opponent):
    board = [0] * POINTS
    me_mask = 0
    opp_mask = 0

    for item in me:
        try:
            r, c = item
        except Exception:
            continue
        if _in_board(r, c):
            i = _to_idx(r, c)
            board[i] = 1
            me_mask |= 1 << i

    for item in opponent:
        try:
            r, c = item
        except Exception:
            continue
        if _in_board(r, c):
            i = _to_idx(r, c)
            if board[i] != 1:
                board[i] = -1
                opp_mask |= 1 << i

    return board, me_mask, opp_mask


def _analyze(board):
    group_id = [-1] * POINTS
    groups = []

    for i, color in enumerate(board):
        if color == 0 or group_id[i] != -1:
            continue

        gid = len(groups)
        stack = [i]
        group_id[i] = gid
        stones = []
        libs = set()

        while stack:
            p = stack.pop()
            stones.append(p)
            for nb in NEIGHBORS[p]:
                v = board[nb]
                if v == 0:
                    libs.add(nb)
                elif v == color and group_id[nb] == -1:
                    group_id[nb] = gid
                    stack.append(nb)

        groups.append((color, stones, libs))

    return group_id, groups


def _collect_group(board, start):
    color = board[start]
    stack = [start]
    seen = {start}
    stones = []
    libs = set()

    while stack:
        p = stack.pop()
        stones.append(p)
        for nb in NEIGHBORS[p]:
            v = board[nb]
            if v == 0:
                libs.add(nb)
            elif v == color and nb not in seen:
                seen.add(nb)
                stack.append(nb)

    return stones, libs


def _simulate(board, idx, group_id, groups):
    if board[idx] != 0:
        return None

    new_board = board[:]
    new_board[idx] = 1
    captured = []
    seen_opp_groups = set()

    for nb in NEIGHBORS[idx]:
        if board[nb] == -1:
            gid = group_id[nb]
            if gid in seen_opp_groups:
                continue
            seen_opp_groups.add(gid)
            _color, stones, libs = groups[gid]
            if len(libs) == 1 and idx in libs:
                captured.extend(stones)

    for s in captured:
        new_board[s] = 0

    new_stones, new_libs = _collect_group(new_board, idx)
    if not new_libs:
        return None

    return new_board, captured, new_stones, new_libs


def _nearest_distance(sources):
    dist = [99] * POINTS
    if not sources:
        return dist

    q = deque()
    for s in sources:
        dist[s] = 0
        q.append(s)

    while q:
        p = q.popleft()
        nd = dist[p] + 1
        for nb in NEIGHBORS[p]:
            if dist[nb] > nd:
                dist[nb] = nd
                q.append(nb)

    return dist


def _eye_status(board, idx, color):
    if board[idx] != 0:
        return 0

    for nb in NEIGHBORS[idx]:
        if board[nb] != color:
            return 0

    enemy_diag = 0
    empty_diag = 0
    for d in DIAGONALS[idx]:
        v = board[d]
        if v == -color:
            enemy_diag += 1
        elif v == 0:
            empty_diag += 1

    if enemy_diag == 0 and empty_diag == 0:
        return 2

    if enemy_diag == 0 and len(DIAGONALS[idx]) < 4 and empty_diag <= 1:
        return 2

    if enemy_diag == 0:
        return 1

    if enemy_diag == 1 and len(DIAGONALS[idx]) <= 2 and empty_diag == 0:
        return 1

    return 0


def _corner_opening_bonus(idx, board, total):
    if total > 140:
        return 0.0

    phase = min(1.0, total / 120.0)
    score = 0.0

    for region, hoshi, corner_moves, approach, extension, three_three in CORNERS:
        has_own = False
        has_opp = False
        for p in region:
            if board[p] == 1:
                has_own = True
            elif board[p] == -1:
                has_opp = True

        if not has_own and not has_opp:
            if idx == hoshi:
                score += 170.0 * (1.0 - 0.35 * phase)
            elif idx in corner_moves:
                score += 115.0 * (1.0 - 0.35 * phase)

        elif has_opp and not has_own:
            if idx in approach:
                score += 105.0 * (1.0 - 0.25 * phase)
            if idx == three_three and total > 35:
                score += 80.0

        elif has_own and not has_opp:
            if idx in extension:
                score += 55.0 * (1.0 - 0.50 * phase)

    return score


def _positional_score(idx, total, own_d, opp_d, own_count, opp_count, board):
    r, c = COORDS[idx]
    edge = min(r, c, N + 1 - r, N + 1 - c)
    if edge > 10:
        edge = 10

    if total < 55:
        score = _OPEN_LINE[edge]
    elif total < 210:
        score = _MID_LINE[edge]
    else:
        score = _END_LINE[edge]

    if total < 90:
        if idx in STAR_POINTS:
            score += 20.0
        if idx in CORNER_HOSHI:
            score += 25.0
        elif idx in SIDE_HOSHI:
            score += 12.0
        if idx == CENTER:
            score += 8.0 if total > 8 else -8.0
        if idx in THREE_THREE and total < 20:
            score -= 18.0

    score += _corner_opening_bonus(idx, board, total)

    if total < 50:
        if own_count == 0 and opp_count > 0:
            score += min(opp_d, 24) * 2.2
        elif own_count > 0:
            if own_d <= 2:
                score -= (3 - own_d) * 25.0
            elif 3 <= own_d <= 8:
                score += (9 - own_d) * 4.0

            if opp_d <= 2 and own_d > 2:
                score -= 18.0
            elif 3 <= opp_d <= 6:
                score += (7 - opp_d) * 3.0
    else:
        if own_d > 8 and opp_d > 8:
            score -= 25.0
        if own_d <= 4:
            score += (5 - own_d) * 8.0
        if opp_d <= 4:
            score += (5 - opp_d) * 9.0

    return score


def _quick_score(idx, board, group_id, groups, sim, own_dist, opp_dist, total, own_count, opp_count):
    new_board, captured, new_stones, new_libs = sim

    score = 0.0
    own_gids = set()
    opp_gids = set()
    own_adj = 0
    opp_adj = 0
    empty_adj = 0

    for nb in NEIGHBORS[idx]:
        v = board[nb]
        if v == 1:
            own_adj += 1
            own_gids.add(group_id[nb])
        elif v == -1:
            opp_adj += 1
            opp_gids.add(group_id[nb])
        else:
            empty_adj += 1

    cap_count = len(captured)
    cap_groups = 0
    if cap_count:
        for g in opp_gids:
            libs = groups[g][2]
            if len(libs) == 1 and idx in libs:
                cap_groups += 1

        score += 650.0 + 430.0 * cap_count + 70.0 * cap_groups
        if cap_count >= 4:
            score += 120.0 * min(cap_count, 12)

    save_size = 0
    for g in own_gids:
        _color, stones, libs = groups[g]
        l = len(libs)
        size = len(stones)
        if idx in libs:
            if l == 1:
                save_size += size
                score += 620.0 + 245.0 * min(size, 30)
            elif l == 2:
                score += 125.0 + 34.0 * min(size, 18)
            elif l == 3:
                score += 28.0 + 6.0 * min(size, 12)

    for g in opp_gids:
        _color, stones, libs = groups[g]
        l = len(libs)
        size = len(stones)
        if idx in libs:
            if l == 2:
                score += 270.0 + 72.0 * min(size, 25)
            elif l == 3:
                score += 48.0 + 13.0 * min(size, 15)
            elif l >= 4 and size >= 6:
                score += 12.0 * min(size, 12)

    if len(own_gids) >= 2:
        weak = 0
        sz = 0
        for g in own_gids:
            sz += min(len(groups[g][1]), 12)
            weak += max(0, 4 - len(groups[g][2]))
        score += 105.0 * (len(own_gids) - 1) + 12.0 * sz + 38.0 * weak

    if len(opp_gids) >= 2:
        sz = 0
        for g in opp_gids:
            sz += min(len(groups[g][1]), 12)
        score += 78.0 * (len(opp_gids) - 1) + 9.0 * sz

    score += own_adj * 7.0 + opp_adj * 8.0 + empty_adj * 1.5

    diag_own = 0
    diag_opp = 0
    for d in DIAGONALS[idx]:
        if board[d] == 1:
            diag_own += 1
        elif board[d] == -1:
            diag_opp += 1
    score += diag_own * 5.0 + diag_opp * 3.0

    new_lib_n = len(new_libs)
    new_size = len(new_stones)

    if new_lib_n == 1:
        penalty = 900.0 + 18.0 * min(new_size, 30)
        if cap_count >= 2:
            penalty *= 0.45
        elif cap_count == 1:
            penalty *= 0.65
        if save_size >= 5:
            penalty *= 0.55
        score -= penalty
    elif new_lib_n == 2:
        if cap_count == 0 and save_size == 0:
            score -= 85.0 + 4.0 * min(new_size, 20)
        else:
            score -= 25.0
    else:
        score += 8.0 * min(new_lib_n, 8)

    if cap_count == 0:
        eye = _eye_status(board, idx, 1)
        if eye == 2:
            score -= 2400.0
        elif eye == 1:
            score -= 650.0

    score += _positional_score(
        idx, total, own_dist[idx], opp_dist[idx], own_count, opp_count, board
    )

    tactical = cap_count > 0 or save_size > 0
    od = own_dist[idx]
    ed = opp_dist[idx]

    if total < 55:
        if own_count == 0 and opp_count > 0:
            score += min(ed, 24) * 2.0
        else:
            if od <= 1 and not tactical:
                score -= 35.0
            if 3 <= od <= 6:
                score += (7 - od) * 7.0
            if 3 <= ed <= 6:
                score += (7 - ed) * 4.0
            if ed <= 1 and od > 2 and not tactical:
                score -= 22.0
    else:
        if od > 8 and ed > 8:
            score -= 30.0
        if od <= 3:
            score += (4 - od) * 10.0
        if ed <= 3:
            score += (4 - ed) * 12.0
        if od == 1 and ed > 4 and not tactical and len(own_gids) == 1:
            score -= 18.0
        if total > 120 and ed > 6 and od <= 2 and not tactical:
            score -= 55.0

    if cap_count == 1 and len(new_stones) == 1 and len(new_libs) == 1:
        score -= 120.0

    return score


def _static_eval(board):
    _gid, groups = _analyze(board)
    score = 0.0

    for v in board:
        score += 3.0 * v

    for color, stones, libs in groups:
        sign = 1.0 if color == 1 else -1.0
        size = len(stones)
        l = len(libs)

        if l == 1:
            score -= sign * (35.0 + 8.0 * size)
        elif l == 2:
            score -= sign * (10.0 + 3.0 * size)
        else:
            score += sign * (1.5 * min(l, 8) + 0.45 * min(size, 25))

        if l <= 10:
            eyes = 0
            for lib in libs:
                if _eye_status(board, lib, color) == 2:
                    eyes += 1
                    if eyes >= 2:
                        break
            if eyes >= 2:
                score += sign * (35.0 + min(size, 25))
            elif eyes == 1:
                score += sign * 8.0

    influence = [0.0] * POINTS
    for i, v in enumerate(board):
        if v:
            for j, w in INFLUENCE_NEAR[i]:
                if board[j] == 0:
                    influence[j] += v * w

    for i, v in enumerate(board):
        if v != 0:
            continue
        x = influence[i]
        if x > 4.0:
            score += 1.0
        elif x > 1.5:
            score += 0.65
        elif x > 0.25:
            score += 0.25 * x
        elif x < -4.0:
            score -= 1.0
        elif x < -1.5:
            score -= 0.65
        elif x < -0.25:
            score += 0.25 * x

    return score


def _has_urgent(groups):
    for _color, stones, libs in groups:
        l = len(libs)
        if l == 1:
            return True
        if len(stones) >= 6 and l == 2:
            return True
    return False


def _state_after(me_mask, opp_mask, idx, captured):
    nm = me_mask | (1 << idx)
    om = opp_mask
    for s in captured:
        om &= ~(1 << s)
    return nm, om


def _is_potential_simple_ko(captured, new_stones, new_libs):
    return len(captured) == 1 and len(new_stones) == 1 and len(new_libs) == 1


def _tiny_noise(idx, state):
    x = ((idx + 1) * 1000003) ^ (state[0] & 0xFFFFFFFF) ^ ((state[1] >> (idx % 61)) & 0xFFFFFFFF)
    x = (x ^ (x >> 16)) & 0xFFFF
    return (x / 65535.0) * 0.05


def _update_memory(memory, current_state, final_state, final_total, action):
    mem = dict(memory) if isinstance(memory, dict) else {}

    raw_seen = mem.get("seen", [])
    combined = []

    try:
        iterator = list(raw_seen)
    except Exception:
        iterator = []

    for s in iterator:
        st = _state_or_none(s)
        if st is not None:
            combined.append(st)

    combined.append(current_state)
    combined.append(final_state)

    out = []
    used = set()
    for st in reversed(combined):
        if st not in used:
            out.append(st)
            used.add(st)
            if len(out) >= 512:
                break
    out.reverse()

    mem["seen"] = out
    mem["last_after"] = final_state
    mem["last_total"] = final_total
    mem["last_move"] = action
    mem["_has_history"] = True
    mem["passes"] = mem.get("passes", 0) + 1 if action == (0, 0) else 0
    return mem


def _policy_impl(me, opponent, memory):
    if not isinstance(memory, dict):
        memory = {}
    else:
        memory = dict(memory)

    board, me_mask, opp_mask = _make_board(me, opponent)

    own_indices = [i for i, v in enumerate(board) if v == 1]
    opp_indices = [i for i, v in enumerate(board) if v == -1]
    own_count = len(own_indices)
    opp_count = len(opp_indices)
    total = own_count + opp_count

    # Reset likely stale memory at the start of a new game.
    last_total = memory.get("last_total")
    if total == 0 or (isinstance(last_total, int) and last_total > 50 and total < 10):
        memory = {}

    current_state = (me_mask, opp_mask)

    group_id, groups = _analyze(board)
    own_dist = _nearest_distance(own_indices)
    opp_dist = _nearest_distance(opp_indices)

    strict_forbidden = set()
    last_after = _state_or_none(memory.get("last_after"))
    if last_after is not None:
        strict_forbidden.add(last_after)

    seen = set()
    raw_seen = memory.get("seen", [])
    try:
        for s in raw_seen:
            st = _state_or_none(s)
            if st is not None:
                seen.add(st)
    except Exception:
        pass

    no_history = (not memory.get("_has_history", False)) and total > 0

    candidates = []

    for idx in range(POINTS):
        if board[idx] != 0:
            continue

        sim = _simulate(board, idx, group_id, groups)
        if sim is None:
            continue

        new_board, captured, new_stones, new_libs = sim
        new_state = _state_after(me_mask, opp_mask, idx, captured)

        # Simple ko and positional-superko safety.
        if new_state in strict_forbidden:
            continue
        if new_state in seen:
            continue
        if no_history and _is_potential_simple_ko(captured, new_stones, new_libs):
            continue

        q = _quick_score(
            idx, board, group_id, groups, sim,
            own_dist, opp_dist, total, own_count, opp_count
        )
        candidates.append((q, idx, sim, new_state))

    if not candidates:
        mem = _update_memory(memory, current_state, current_state, total, (0, 0))
        return (0, 0), mem

    candidates.sort(key=lambda x: x[0], reverse=True)

    if total < 80:
        limit = 150
    elif total < 230:
        limit = 100
    else:
        limit = 75

    top = candidates[:limit]
    base_eval = _static_eval(board)

    best_score = -10**18
    best_idx = None
    best_sim = None
    best_state = None

    for q, idx, sim, st in top:
        ev_delta = _static_eval(sim[0]) - base_eval
        final_score = q + 7.0 * ev_delta + _tiny_noise(idx, current_state)

        if final_score > best_score:
            best_score = final_score
            best_idx = idx
            best_sim = sim
            best_state = st

    urgent = _has_urgent(groups)

    choose_pass = False
    if best_idx is None:
        choose_pass = True
    elif best_score < -1000.0:
        choose_pass = True
    elif not urgent:
        if best_score < -500.0:
            choose_pass = True
        elif total > 330 and best_score < 15.0:
            choose_pass = True
        elif total > 285 and best_score < -40.0:
            choose_pass = True

    if choose_pass:
        mem = _update_memory(memory, current_state, current_state, total, (0, 0))
        return (0, 0), mem

    r, c = COORDS[best_idx]
    action = (r, c)
    final_board = best_sim[0]
    final_total = sum(1 for v in final_board if v != 0)
    mem = _update_memory(memory, current_state, best_state, final_total, action)
    return action, mem


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    try:
        return _policy_impl(me, opponent, memory)
    except Exception:
        # Pass is always legal and prevents disqualification if anything unexpected happens.
        if not isinstance(memory, dict):
            memory = {}
        return (0, 0), memory
