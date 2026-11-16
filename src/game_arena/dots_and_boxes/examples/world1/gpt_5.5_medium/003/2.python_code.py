
import time
import numpy as np

# Dots and Boxes, 4x4 boxes:
# Horizontal valid edges: rows 0..4, cols 0..3  -> 20 edges
# Vertical valid edges:   rows 0..3, cols 0..4  -> 20 edges

FULL_H = (1 << 20) - 1
FULL_V = (1 << 20) - 1

# Precomputed structures
_BOX_HMASKS = []
_BOX_VMASKS = []
_EDGE_BOXES = [[] for _ in range(40)]
_MOVE_STRS = []

for r in range(5):
    for c in range(4):
        _MOVE_STRS.append(f"{r},{c},H")

for r in range(4):
    for c in range(5):
        _MOVE_STRS.append(f"{r},{c},V")

for r in range(4):
    for c in range(4):
        # box index = r*4+c
        hmask = (1 << (r * 4 + c)) | (1 << ((r + 1) * 4 + c))
        vmask = (1 << (r * 5 + c)) | (1 << (r * 5 + c + 1))
        _BOX_HMASKS.append(hmask)
        _BOX_VMASKS.append(vmask)

# Adjacent boxes for horizontal edges
for r in range(5):
    for c in range(4):
        e = r * 4 + c
        if r > 0:
            _EDGE_BOXES[e].append((r - 1) * 4 + c)
        if r < 4:
            _EDGE_BOXES[e].append(r * 4 + c)

# Adjacent boxes for vertical edges
for r in range(4):
    for c in range(5):
        e = 20 + r * 5 + c
        if c > 0:
            _EDGE_BOXES[e].append(r * 4 + (c - 1))
        if c < 4:
            _EDGE_BOXES[e].append(r * 4 + c)


class _SearchTimeout(Exception):
    pass


def _bitcount(x: int) -> int:
    return int(x).bit_count()


def _masks_from_arrays(horizontal: np.ndarray, vertical: np.ndarray):
    hm = 0
    vm = 0

    for r in range(5):
        for c in range(4):
            if horizontal[r, c] != 0:
                hm |= 1 << (r * 4 + c)

    for r in range(4):
        for c in range(5):
            if vertical[r, c] != 0:
                vm |= 1 << (r * 5 + c)

    return hm, vm


def _box_sides(hm: int, vm: int, b: int) -> int:
    return _bitcount(hm & _BOX_HMASKS[b]) + _bitcount(vm & _BOX_VMASKS[b])


def _legal_moves(hm: int, vm: int):
    moves = []

    empty_h = (~hm) & FULL_H
    while empty_h:
        lsb = empty_h & -empty_h
        i = lsb.bit_length() - 1
        moves.append(i)
        empty_h ^= lsb

    empty_v = (~vm) & FULL_V
    while empty_v:
        lsb = empty_v & -empty_v
        i = lsb.bit_length() - 1
        moves.append(20 + i)
        empty_v ^= lsb

    return moves


def _play_move(hm: int, vm: int, e: int):
    if e < 20:
        return hm | (1 << e), vm
    return hm, vm | (1 << (e - 20))


def _capture_count(hm: int, vm: int, e: int) -> int:
    # An empty edge captures each adjacent box that currently has exactly 3 sides.
    cnt = 0
    for b in _EDGE_BOXES[e]:
        if _box_sides(hm, vm, b) == 3:
            cnt += 1
    return cnt


def _danger_count(hm: int, vm: int, e: int) -> int:
    # A non-capturing move is dangerous if it turns a 2-sided box into a 3-sided box.
    cnt = 0
    for b in _EDGE_BOXES[e]:
        if _box_sides(hm, vm, b) == 2:
            cnt += 1
    return cnt


def _has_capture(hm: int, vm: int) -> bool:
    for e in _legal_moves(hm, vm):
        if _capture_count(hm, vm, e) > 0:
            return True
    return False


def _safe_moves(hm: int, vm: int):
    res = []
    for e in _legal_moves(hm, vm):
        if _capture_count(hm, vm, e) == 0 and _danger_count(hm, vm, e) == 0:
            res.append(e)
    return res


def _count_boxes_with_sides(hm: int, vm: int, n: int) -> int:
    total = 0
    for b in range(16):
        if _box_sides(hm, vm, b) == n:
            total += 1
    return total


def _adjacent_side_sum(hm: int, vm: int, e: int) -> int:
    s = 0
    for b in _EDGE_BOXES[e]:
        s += _box_sides(hm, vm, b)
    return s


def _count_safe_moves(hm: int, vm: int) -> int:
    c = 0
    for e in _legal_moves(hm, vm):
        if _capture_count(hm, vm, e) == 0 and _danger_count(hm, vm, e) == 0:
            c += 1
    return c


def _move_order_key(hm: int, vm: int, e: int):
    cap = _capture_count(hm, vm, e)
    danger = _danger_count(hm, vm, e)
    adj = _adjacent_side_sum(hm, vm, e)
    # Captures first, then safe moves, then least dangerous openings.
    return (cap > 0, cap, -danger, -adj)


def _ordered_moves(hm: int, vm: int):
    moves = _legal_moves(hm, vm)
    moves.sort(key=lambda e: _move_order_key(hm, vm, e), reverse=True)
    return moves


def _exact_best_move(hm0: int, vm0: int, deadline: float):
    memo = {}
    nodes = 0

    def ab(hm: int, vm: int, player: int, alpha: int, beta: int) -> int:
        # player = 1 for us to move, -1 for opponent to move.
        # Value is final additional box difference from our perspective.
        nonlocal nodes
        nodes += 1
        if (nodes & 2047) == 0 and time.perf_counter() > deadline:
            raise _SearchTimeout()

        if hm == FULL_H and vm == FULL_V:
            return 0

        key = (hm, vm, player)
        if key in memo:
            return memo[key]

        moves = _ordered_moves(hm, vm)

        if player == 1:
            best = -100
            cut = False
            for e in moves:
                cap = _capture_count(hm, vm, e)
                nhm, nvm = _play_move(hm, vm, e)
                nxt = player if cap else -player
                val = cap + ab(nhm, nvm, nxt, alpha, beta)
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    cut = True
                    break
        else:
            best = 100
            cut = False
            for e in moves:
                cap = _capture_count(hm, vm, e)
                nhm, nvm = _play_move(hm, vm, e)
                nxt = player if cap else -player
                val = -cap + ab(nhm, nvm, nxt, alpha, beta)
                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if alpha >= beta:
                    cut = True
                    break

        if not cut:
            memo[key] = best
        return best

    best_e = None
    best_val = -100
    alpha = -100
    beta = 100

    for e in _ordered_moves(hm0, vm0):
        if time.perf_counter() > deadline:
            raise _SearchTimeout()

        cap = _capture_count(hm0, vm0, e)
        nhm, nvm = _play_move(hm0, vm0, e)
        nxt = 1 if cap else -1
        val = cap + ab(nhm, nvm, nxt, alpha, beta)

        if best_e is None or val > best_val:
            best_val = val
            best_e = e

        if best_val > alpha:
            alpha = best_val

    return best_e


def _greedy_concession_after_opening(hm: int, vm: int) -> int:
    # Approximate how many boxes the opponent can take after we make a dangerous move.
    # Opponent greedily keeps taking captures until no capture exists.
    taken = 0
    guard = 0

    while guard < 20:
        guard += 1
        caps = []
        for e in _legal_moves(hm, vm):
            c = _capture_count(hm, vm, e)
            if c > 0:
                caps.append((c, e))

        if not caps:
            break

        # Opponent prefers double captures and moves that continue the chain.
        caps.sort(reverse=True)
        c, e = caps[0]
        taken += c
        hm, vm = _play_move(hm, vm, e)

    return taken


def _fallback_move(hm: int, vm: int):
    legal = _legal_moves(hm, vm)
    if not legal:
        return None

    # 1. Take captures.
    captures = [e for e in legal if _capture_count(hm, vm, e) > 0]
    if captures:
        best_e = captures[0]
        best_score = -10**9

        for e in captures:
            cap = _capture_count(hm, vm, e)
            nhm, nvm = _play_move(hm, vm, e)

            future_caps = 0
            for f in _legal_moves(nhm, nvm):
                future_caps = max(future_caps, _capture_count(nhm, nvm, f))

            score = 10000 * cap + 200 * future_caps
            score -= 3 * _count_boxes_with_sides(nhm, nvm, 3)
            score -= _adjacent_side_sum(hm, vm, e)

            if score > best_score:
                best_score = score
                best_e = e

        return best_e

    # 2. Play a safe edge if possible.
    safe = [e for e in legal if _danger_count(hm, vm, e) == 0]
    if safe:
        best_e = safe[0]
        best_score = -10**9

        for e in safe:
            nhm, nvm = _play_move(hm, vm, e)
            safe_after = _count_safe_moves(nhm, nvm)
            twos_after = _count_boxes_with_sides(nhm, nvm, 2)

            # Safe-move parity heuristic:
            # after our move, opponent is to move. If the remaining safe count is even,
            # opponent is more likely to be the player who eventually has to open.
            parity_bonus = 45 if (safe_after % 2 == 0) else -45

            score = parity_bonus
            score -= 2 * safe_after
            score -= 6 * twos_after
            score -= 4 * _adjacent_side_sum(hm, vm, e)
            score -= len(_EDGE_BOXES[e])  # slight preference for boundary edges

            if score > best_score:
                best_score = score
                best_e = e

        return best_e

    # 3. No safe moves: open the smallest-looking chain.
    best_e = legal[0]
    best_score = -10**9

    for e in legal:
        nhm, nvm = _play_move(hm, vm, e)
        conceded = _greedy_concession_after_opening(nhm, nvm)
        threes = _count_boxes_with_sides(nhm, nvm, 3)

        score = -1000 * conceded
        score -= 25 * threes
        score -= 5 * _danger_count(hm, vm, e)
        score -= _adjacent_side_sum(hm, vm, e)

        if score > best_score:
            best_score = score
            best_e = e

    return best_e


def _emergency_legal_from_arrays(horizontal: np.ndarray, vertical: np.ndarray) -> str:
    # Prefer real 4x4-board edges.
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"

    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # If the environment unexpectedly treats the padding cells as legal,
    # this still returns an empty array entry when available.
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                return f"{r},{c},H"

    for r in range(5):
        for c in range(5):
            if vertical[r, c] == 0:
                return f"{r},{c},V"

    # Should only happen after the game is already over.
    return "0,0,H"


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        hm, vm = _masks_from_arrays(horizontal, vertical)
        empty = 40 - _bitcount(hm) - _bitcount(vm)

        legal = _legal_moves(hm, vm)
        if not legal:
            return _emergency_legal_from_arrays(horizontal, vertical)

        cap_available = False
        for e in legal:
            if _capture_count(hm, vm, e) > 0:
                cap_available = True
                break

        safe_available = False
        if not cap_available:
            for e in legal:
                if _danger_count(hm, vm, e) == 0:
                    safe_available = True
                    break

        # Exact search in endgames and tactical/loony positions.
        # The timeout keeps the policy safely under typical arena limits.
        use_exact = (
            empty <= 20 or
            (cap_available and empty <= 26) or
            ((not safe_available) and empty <= 28)
        )

        if use_exact:
            try:
                deadline = time.perf_counter() + 0.82
                e = _exact_best_move(hm, vm, deadline)
                if e is not None:
                    return _MOVE_STRS[e]
            except _SearchTimeout:
                pass
            except Exception:
                pass

        e = _fallback_move(hm, vm)
        if e is not None:
            return _MOVE_STRS[e]

    except Exception:
        pass

    return _emergency_legal_from_arrays(horizontal, vertical)
