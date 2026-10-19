
from typing import Dict, List, Optional, Set, Tuple

BOARD_SIZE = 19
AREA = BOARD_SIZE * BOARD_SIZE
ME = 1
OPP = 2
PASS_MOVE = (0, 0)


def _rc_to_i(r: int, c: int) -> int:
    return (r - 1) * BOARD_SIZE + (c - 1)


def _i_to_rc(i: int) -> Tuple[int, int]:
    return (i // BOARD_SIZE + 1, i % BOARD_SIZE + 1)


def _build_adjacency():
    neighbors = [[] for _ in range(AREA)]
    diagonals = [[] for _ in range(AREA)]
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            i = r * BOARD_SIZE + c
            if r > 0:
                neighbors[i].append((r - 1) * BOARD_SIZE + c)
            if r + 1 < BOARD_SIZE:
                neighbors[i].append((r + 1) * BOARD_SIZE + c)
            if c > 0:
                neighbors[i].append(r * BOARD_SIZE + (c - 1))
            if c + 1 < BOARD_SIZE:
                neighbors[i].append(r * BOARD_SIZE + (c + 1))

            for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE:
                    diagonals[i].append(rr * BOARD_SIZE + cc)
    return neighbors, diagonals


NEIGHBORS, DIAGONALS = _build_adjacency()

OPENING_ORDER = [
    (4, 4), (4, 16), (16, 4), (16, 16),
    (4, 10), (10, 4), (10, 16), (16, 10),
    (10, 10),
    (3, 4), (4, 3), (3, 16), (4, 17),
    (16, 3), (17, 4), (16, 17), (17, 16),
    (3, 3), (3, 17), (17, 3), (17, 17),
]

OPENING_WEIGHTS = {
    (4, 4): 80, (4, 16): 80, (16, 4): 80, (16, 16): 80,
    (4, 10): 58, (10, 4): 58, (10, 16): 58, (16, 10): 58,
    (10, 10): 34,
    (3, 4): 64, (4, 3): 64, (3, 16): 64, (4, 17): 64,
    (16, 3): 64, (17, 4): 64, (16, 17): 64, (17, 16): 64,
    (3, 3): 42, (3, 17): 42, (17, 3): 42, (17, 17): 42,
}

CORNER_PREFS = {
    "tl": {(4, 4), (4, 3), (3, 4), (3, 3)},
    "tr": {(4, 16), (4, 17), (3, 16), (3, 17)},
    "bl": {(16, 4), (17, 4), (16, 3), (17, 3)},
    "br": {(16, 16), (16, 17), (17, 16), (17, 17)},
}

CORNER_POINT_TO_ZONE = {}
for zone_name, pts in CORNER_PREFS.items():
    for pt in pts:
        CORNER_POINT_TO_ZONE[pt] = zone_name

CORNER_ZONES = {
    "tl": [_rc_to_i(r, c) for r in range(1, 7) for c in range(1, 7)],
    "tr": [_rc_to_i(r, c) for r in range(1, 7) for c in range(14, 20)],
    "bl": [_rc_to_i(r, c) for r in range(14, 20) for c in range(1, 7)],
    "br": [_rc_to_i(r, c) for r in range(14, 20) for c in range(14, 20)],
}


def _build_board(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> bytearray:
    board = bytearray(AREA)
    for r, c in me:
        if 1 <= r <= 19 and 1 <= c <= 19:
            board[_rc_to_i(r, c)] = ME
    for r, c in opponent:
        if 1 <= r <= 19 and 1 <= c <= 19:
            i = _rc_to_i(r, c)
            if board[i] == 0:
                board[i] = OPP
    return board


def _collect_group(board: bytearray, start: int) -> Tuple[List[int], Set[int]]:
    color = board[start]
    stones = []
    liberties: Set[int] = set()
    stack = [start]
    seen = {start}

    while stack:
        p = stack.pop()
        stones.append(p)
        for n in NEIGHBORS[p]:
            v = board[n]
            if v == 0:
                liberties.add(n)
            elif v == color and n not in seen:
                seen.add(n)
                stack.append(n)
    return stones, liberties


def _analyze_board(board: bytearray):
    group_id = [-1] * AREA
    groups = []

    for i in range(AREA):
        if board[i] == 0 or group_id[i] != -1:
            continue

        color = board[i]
        gid = len(groups)
        stones = []
        liberties: Set[int] = set()
        stack = [i]
        group_id[i] = gid

        while stack:
            p = stack.pop()
            stones.append(p)
            for n in NEIGHBORS[p]:
                v = board[n]
                if v == 0:
                    liberties.add(n)
                elif v == color and group_id[n] == -1:
                    group_id[n] = gid
                    stack.append(n)

        groups.append({
            "color": color,
            "stones": stones,
            "libs": liberties,
            "size": len(stones),
        })

    return group_id, groups


def _simulate_move(
    board: bytearray,
    pos: int,
    seen_hashes: Set[bytes],
) -> Optional[Tuple[bytearray, int, List[int], Set[int], bytes]]:
    if board[pos] != 0:
        return None

    b = bytearray(board)
    b[pos] = ME

    checked_enemy: Set[int] = set()
    capture_groups: List[List[int]] = []

    # Determine captures on the post-placement board before removing anything.
    for n in NEIGHBORS[pos]:
        if b[n] == OPP and n not in checked_enemy:
            stones, libs = _collect_group(b, n)
            for s in stones:
                checked_enemy.add(s)
            if not libs:
                capture_groups.append(stones)

    captured = 0
    for stones in capture_groups:
        captured += len(stones)
        for s in stones:
            b[s] = 0

    own_group, own_libs = _collect_group(b, pos)
    if not own_libs:
        return None  # suicide

    new_hash = bytes(b)
    if new_hash in seen_hashes:
        return None  # conservative ko/superko safety

    return b, captured, own_group, own_libs, new_hash


def _likely_own_eye(board: bytearray, pos: int) -> bool:
    adj = NEIGHBORS[pos]
    if not adj:
        return False

    # If any adjacent opponent stone exists, it is unlikely to be a true eye.
    for n in adj:
        if board[n] == OPP:
            return False

    # If any adjacent empty exists, this is not a filled eye shape yet.
    for n in adj:
        if board[n] == 0:
            return False

    # All adjacent points are our stones. Check diagonals.
    enemy_diagonals = 0
    for d in DIAGONALS[pos]:
        if board[d] == OPP:
            enemy_diagonals += 1

    # Heuristic true-eye test.
    if len(adj) == 4:
        return enemy_diagonals <= 1
    if len(adj) == 3:
        return enemy_diagonals == 0
    return True


def _compute_corner_empties(board: bytearray) -> Dict[str, bool]:
    out = {}
    for name, zone in CORNER_ZONES.items():
        empty = True
        for i in zone:
            if board[i] != 0:
                empty = False
                break
        out[name] = empty
    return out


def _opening_bonus(
    pos: int,
    occupied: List[int],
    total_stones: int,
    turn_no: int,
    corner_empties: Dict[str, bool],
) -> float:
    # Use opening logic only early in the game.
    if turn_no >= 8 or total_stones > 30:
        return 0.0

    r = pos // BOARD_SIZE + 1
    c = pos % BOARD_SIZE + 1
    pt = (r, c)

    bonus = float(OPENING_WEIGHTS.get(pt, 0))

    zone = CORNER_POINT_TO_ZONE.get(pt)
    if zone is not None and corner_empties.get(zone, False):
        bonus += 28.0

    if occupied:
        pr = pos // BOARD_SIZE
        pc = pos % BOARD_SIZE
        dmin = min(abs(pr - (q // BOARD_SIZE)) + abs(pc - (q % BOARD_SIZE)) for q in occupied)
        bonus += 2.0 * min(dmin, 8)

    # Mild penalty for random center wandering very early, except tengen.
    if turn_no < 5 and 7 <= r <= 13 and 7 <= c <= 13 and pt != (10, 10):
        bonus -= 22.0

    return bonus


def _generate_candidates(board: bytearray, groups, total_stones: int, turn_no: int) -> List[int]:
    occupied = [i for i, v in enumerate(board) if v != 0]
    cands: Set[int] = set()

    # Early opening points.
    if turn_no < 8 and total_stones < 30:
        for r, c in OPENING_ORDER:
            i = _rc_to_i(r, c)
            if board[i] == 0:
                cands.add(i)

    # Tactical liberties around weak groups.
    for g in groups:
        libn = len(g["libs"])
        size = g["size"]
        if libn <= 2:
            cands.update(g["libs"])
        elif libn == 3 and size >= 5:
            cands.update(g["libs"])

    # Local area around existing stones.
    for p in occupied:
        r = p // BOARD_SIZE
        c = p % BOARD_SIZE
        for dr in (-2, -1, 0, 1, 2):
            rr = r + dr
            if not (0 <= rr < BOARD_SIZE):
                continue
            for dc in (-2, -1, 0, 1, 2):
                cc = c + dc
                if not (0 <= cc < BOARD_SIZE):
                    continue
                q = rr * BOARD_SIZE + cc
                if board[q] == 0:
                    cands.add(q)

    if not occupied:
        return [_rc_to_i(r, c) for r, c in OPENING_ORDER[:5]]

    return list(cands)


def _evaluate_move(
    pos: int,
    board: bytearray,
    new_board: bytearray,
    captured: int,
    own_group: List[int],
    own_libs: Set[int],
    group_id: List[int],
    groups,
    occupied: List[int],
    total_stones: int,
    turn_no: int,
    corner_empties: Dict[str, bool],
    global_own_atari_total: int,
    global_opp_atari_total: int,
) -> float:
    score = 0.0

    adj_own_ids: Set[int] = set()
    adj_opp_ids: Set[int] = set()

    for n in NEIGHBORS[pos]:
        gid = group_id[n]
        if gid == -1:
            continue
        if groups[gid]["color"] == ME:
            adj_own_ids.add(gid)
        else:
            adj_opp_ids.add(gid)

    save_size = 0
    reinforce_size = 0
    attack_pre = 0
    connect_size = 0

    for gid in adj_own_ids:
        g = groups[gid]
        if pos in g["libs"]:
            libn = len(g["libs"])
            if libn == 1:
                save_size += g["size"]
            elif libn == 2:
                reinforce_size += g["size"]

    for gid in adj_opp_ids:
        g = groups[gid]
        if pos in g["libs"] and len(g["libs"]) == 2:
            attack_pre += g["size"]

    if len(adj_own_ids) >= 2:
        connect_size = sum(groups[gid]["size"] for gid in adj_own_ids)

    atari_created_size = 0
    seen_enemy_after: Set[int] = set()
    for n in NEIGHBORS[pos]:
        if new_board[n] == OPP and n not in seen_enemy_after:
            stones, libs = _collect_group(new_board, n)
            for s in stones:
                seen_enemy_after.add(s)
            if len(libs) == 1:
                atari_created_size += len(stones)

    own_lib_n = len(own_libs)
    own_size = len(own_group)
    empty_neighbors = sum(1 for n in NEIGHBORS[pos] if new_board[n] == 0)

    # Main tactical terms.
    score += 520.0 * captured
    score += 460.0 * save_size
    score += 80.0 * attack_pre
    score += 28.0 * reinforce_size
    score += 18.0 * connect_size
    score += 22.0 * max(0, len(adj_own_ids) - 1)
    score += 70.0 * atari_created_size

    # Shape / local health.
    score += 14.0 * min(own_lib_n, 6)
    score += 2.5 * own_size
    score += 8.0 * empty_neighbors
    score += 12.0 * len(adj_opp_ids)
    score += 8.0 * len(adj_own_ids)

    if len(adj_opp_ids) >= 2:
        score += 18.0 * (len(adj_opp_ids) - 1)

    # Avoid obvious self-atari.
    if own_lib_n == 1:
        score -= 260.0 + 35.0 * own_size
        if captured > 0:
            score += 60.0
    elif own_lib_n == 2 and own_size <= 2 and captured == 0:
        score -= 18.0

    # Respond to urgent own atari groups.
    remaining_own_atari = max(0, global_own_atari_total - save_size)
    if remaining_own_atari > 0:
        score -= 240.0 + 45.0 * remaining_own_atari
    elif global_own_atari_total > 0:
        score += 90.0

    # Mild preference to actually take opponent stones in atari if nothing more urgent exists.
    if global_opp_atari_total > 0 and captured == 0 and remaining_own_atari == 0:
        score -= 50.0

    # Avoid filling our own true eyes unless there is a tactical reason.
    if _likely_own_eye(board, pos) and captured == 0 and attack_pre == 0 and save_size == 0:
        score -= 140.0

    # Avoid random isolated moves once the board has some shape.
    if not adj_own_ids and not adj_opp_ids and total_stones > 8:
        score -= 55.0

    # Opening heuristics.
    score += _opening_bonus(pos, occupied, total_stones, turn_no, corner_empties)

    # Slight preference for 3rd/4th-line play in the early middle game.
    r = pos // BOARD_SIZE + 1
    c = pos % BOARD_SIZE + 1
    dist_edge = min(r - 1, c - 1, BOARD_SIZE - r, BOARD_SIZE - c)
    if 8 <= turn_no <= 25 and dist_edge in (1, 2, 3):
        score += 6.0

    return score


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    if not isinstance(memory, dict):
        memory = {}

    total_stones = len(me) + len(opponent)

    # Reset history at the start of a fresh game.
    if total_stones == 0:
        memory = {}

    turn_no = memory.get("_turn", 0)
    if not isinstance(turn_no, int):
        turn_no = 0

    seen_hashes = memory.get("_seen", set())
    if not isinstance(seen_hashes, set):
        try:
            seen_hashes = set(seen_hashes)
        except Exception:
            seen_hashes = set()

    board = _build_board(me, opponent)
    current_hash = bytes(board)
    seen_hashes.add(current_hash)

    occupied = [i for i, v in enumerate(board) if v != 0]
    group_id, groups = _analyze_board(board)
    corner_empties = _compute_corner_empties(board)

    global_own_atari_total = 0
    global_opp_atari_total = 0
    for g in groups:
        if len(g["libs"]) == 1:
            if g["color"] == ME:
                global_own_atari_total += g["size"]
            else:
                global_opp_atari_total += g["size"]

    candidates = _generate_candidates(board, groups, total_stones, turn_no)

    best_move = None
    best_hash = None
    best_score = -10**30

    for pos in sorted(candidates):
        sim = _simulate_move(board, pos, seen_hashes)
        if sim is None:
            continue

        new_board, captured, own_group, own_libs, new_hash = sim
        score = _evaluate_move(
            pos=pos,
            board=board,
            new_board=new_board,
            captured=captured,
            own_group=own_group,
            own_libs=own_libs,
            group_id=group_id,
            groups=groups,
            occupied=occupied,
            total_stones=total_stones,
            turn_no=turn_no,
            corner_empties=corner_empties,
            global_own_atari_total=global_own_atari_total,
            global_opp_atari_total=global_opp_atari_total,
        )

        if score > best_score:
            best_score = score
            best_move = pos
            best_hash = new_hash

    # Safety fallback: search the whole board for any legal move.
    if best_move is None:
        for pos in range(AREA):
            if board[pos] != 0:
                continue
            sim = _simulate_move(board, pos, seen_hashes)
            if sim is not None:
                best_move = pos
                best_hash = sim[4]
                break

    # Final safety fallback: pass is always legal.
    if best_move is None:
        memory["_seen"] = seen_hashes
        memory["_turn"] = turn_no + 1
        return PASS_MOVE, memory

    seen_hashes.add(best_hash)
    memory["_seen"] = seen_hashes
    memory["_turn"] = turn_no + 1
    return _i_to_rc(best_move), memory
