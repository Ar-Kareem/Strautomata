
from typing import List, Tuple, Dict

SIZE = 19
N = SIZE * SIZE

# Precompute board geometry
RC = [(i // SIZE, i % SIZE) for i in range(N)]
NEI = [[] for _ in range(N)]
DIAG = [[] for _ in range(N)]
NEAR2 = [[] for _ in range(N)]

for i in range(N):
    r, c = RC[i]
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE:
            NEI[i].append(nr * SIZE + nc)
    for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE:
            DIAG[i].append(nr * SIZE + nc)
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            if dr == 0 and dc == 0:
                continue
            if max(abs(dr), abs(dc)) <= 2:
                nr, nc = r + dr, c + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE:
                    NEAR2[i].append(nr * SIZE + nc)

def _idx_from_pos(pos: Tuple[int, int]) -> int:
    r, c = pos
    return (r - 1) * SIZE + (c - 1)

def _pos_from_idx(i: int) -> Tuple[int, int]:
    return (i // SIZE + 1, i % SIZE + 1)

def _encode_state(me_set, opp_set):
    return (tuple(sorted(me_set)), tuple(sorted(opp_set)))

def _build_board(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]):
    board = [0] * N
    me_set = set()
    opp_set = set()

    for p in me:
        i = _idx_from_pos(p)
        if 0 <= i < N:
            board[i] = 1
            me_set.add(i)

    for p in opponent:
        i = _idx_from_pos(p)
        if 0 <= i < N and board[i] == 0:
            board[i] = -1
            opp_set.add(i)

    return board, me_set, opp_set

def _analyze_groups(board):
    seen = [False] * N
    gid_of = [-1] * N
    groups = []  # each: (color, stones_list, liberties_set)

    for i, color in enumerate(board):
        if color == 0 or seen[i]:
            continue
        gid = len(groups)
        stack = [i]
        seen[i] = True
        stones = []
        libs = set()

        while stack:
            x = stack.pop()
            gid_of[x] = gid
            stones.append(x)
            for nb in NEI[x]:
                v = board[nb]
                if v == 0:
                    libs.add(nb)
                elif v == color and not seen[nb]:
                    seen[nb] = True
                    stack.append(nb)

        groups.append((color, stones, libs))
    return groups, gid_of

CORNER_STAR = {
    3 * SIZE + 3, 3 * SIZE + 15,
    15 * SIZE + 3, 15 * SIZE + 15
}
SIDE_STAR = {
    3 * SIZE + 9, 9 * SIZE + 3,
    9 * SIZE + 15, 15 * SIZE + 9
}
CENTER_POINT = 9 * SIZE + 9

APPROACH_POINTS = {
    2 * SIZE + 2, 2 * SIZE + 3, 3 * SIZE + 2,
    2 * SIZE + 15, 2 * SIZE + 16, 3 * SIZE + 16,
    15 * SIZE + 2, 16 * SIZE + 2, 16 * SIZE + 3,
    15 * SIZE + 16, 16 * SIZE + 15, 16 * SIZE + 16
}

OPENING_POINTS = CORNER_STAR | SIDE_STAR | {CENTER_POINT} | APPROACH_POINTS

def _opening_bonus(idx: int, total_stones: int, tactical: bool) -> int:
    r, c = RC[idx]
    bonus = 0

    if total_stones < 10:
        if idx in CORNER_STAR:
            bonus += 140
        elif idx in SIDE_STAR:
            bonus += 85
        elif idx == CENTER_POINT:
            bonus += 30
        elif idx in APPROACH_POINTS:
            bonus += 60

        if not tactical:
            if r in (0, 18) or c in (0, 18):
                bonus -= 45
            elif r in (1, 17) or c in (1, 17):
                bonus -= 15

    elif total_stones < 30:
        if idx in CORNER_STAR:
            bonus += 40
        elif idx in SIDE_STAR:
            bonus += 18
        elif idx in APPROACH_POINTS:
            bonus += 15

    if not tactical:
        dist_center = abs(r - 9) + abs(c - 9)
        bonus += max(0, 8 - dist_center // 2)

    return bonus

def _eye_fill_penalty(idx: int, board) -> int:
    # Approximate: all orthogonal neighbors are ours, and enough diagonals are ours too.
    for nb in NEI[idx]:
        if board[nb] != 1:
            return 0

    friendly_diags = sum(1 for d in DIAG[idx] if board[d] == 1)
    r, c = RC[idx]
    edge_contacts = int(r == 0) + int(r == 18) + int(c == 0) + int(c == 18)

    if edge_contacts == 0:
        need = 3
    elif edge_contacts == 1:
        need = 2
    else:
        need = 1

    return 250 if friendly_diags >= need else 80

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    if memory is None or not isinstance(memory, dict):
        memory = {}

    board, me_set, opp_set = _build_board(me, opponent)
    total_stones = len(me_set) + len(opp_set)
    prev_board = memory.get("prev_board", None)

    groups, gid_of = _analyze_groups(board)

    # Opening shortcut on empty board.
    if total_stones == 0:
        move = (4, 4)
        new_me = set(me_set)
        new_me.add(_idx_from_pos(move))
        return move, {"prev_board": _encode_state(new_me, opp_set)}

    # Candidate generation: tactical liberties + local neighborhood + opening points.
    candidates = set()

    occupied = list(me_set | opp_set)
    for i in occupied:
        for j in NEAR2[i]:
            if board[j] == 0:
                candidates.add(j)

    for color, stones, libs in groups:
        if len(libs) <= 2:
            candidates.update(libs)

    for p in OPENING_POINTS:
        if board[p] == 0:
            candidates.add(p)

    if len(candidates) < 8:
        for i in range(N):
            if board[i] == 0:
                candidates.add(i)

    best_idx = None
    best_score = None
    best_tie = None
    best_captured = None

    def evaluate(idx: int):
        if board[idx] != 0:
            return None

        adj_own = set()
        adj_opp = set()
        empty_neighbors = set()

        for nb in NEI[idx]:
            v = board[nb]
            if v == 0:
                empty_neighbors.add(nb)
            elif v == 1:
                adj_own.add(gid_of[nb])
            else:
                adj_opp.add(gid_of[nb])

        captured = []
        capture_count = 0

        for gid in adj_opp:
            libs = groups[gid][2]
            if len(libs) == 1 and idx in libs:
                stones = groups[gid][1]
                captured.extend(stones)
                capture_count += len(stones)

        new_libs = set(empty_neighbors)
        for gid in adj_own:
            new_libs.update(groups[gid][2])
        new_libs.discard(idx)
        if captured:
            new_libs.update(captured)

        own_libs = len(new_libs)

        # Suicide check
        if capture_count == 0 and own_libs == 0:
            return None

        # Simple ko check: only relevant when a capture occurs.
        if prev_board is not None and capture_count > 0:
            new_me = set(me_set)
            new_me.add(idx)
            new_opp = opp_set.difference(captured)
            if _encode_state(new_me, new_opp) == prev_board:
                return None

        saved = 0
        defend = 0
        connect_size = 0

        for gid in adj_own:
            stones = groups[gid][1]
            libs = groups[gid][2]
            sz = len(stones)
            connect_size += sz
            if idx in libs:
                if len(libs) == 1:
                    saved += sz
                elif len(libs) == 2:
                    defend += 70 * sz
                elif len(libs) == 3:
                    defend += 15 * sz

        pressure = 0
        for gid in adj_opp:
            libs = groups[gid][2]
            if len(libs) == 1 and idx in libs:
                continue
            sz = len(groups[gid][1])
            new_l = len(libs) - (1 if idx in libs else 0)
            if new_l == 1:
                pressure += 120 * sz
            elif new_l == 2:
                pressure += 35 * sz
            elif new_l == 3:
                pressure += 8 * sz

        support = 0
        enemy_near = 0
        for j in NEAR2[idx]:
            if board[j] == 1:
                support += 1
            elif board[j] == -1:
                enemy_near += 1

        tactical = (capture_count > 0 or saved > 0 or pressure >= 100 or defend >= 100)

        score = 0
        score += 10000 * capture_count
        score += 7000 * saved
        score += defend
        score += pressure
        score += 45 * max(0, len(adj_own) - 1)
        score += 6 * min(connect_size, 20)
        score += 30 * min(own_libs, 6)
        score += 2 * support + enemy_near
        score += _opening_bonus(idx, total_stones, tactical)

        if support == 0 and enemy_near == 0:
            score -= 25

        # First/second-line penalty if not tactical
        r, c = RC[idx]
        if not tactical:
            if r in (0, 18) or c in (0, 18):
                score -= 18
            elif r in (1, 17) or c in (1, 17):
                score -= 6

        # Avoid obvious eye-filling unless tactical
        if not tactical:
            score -= _eye_fill_penalty(idx, board)

        # Avoid self-atari
        if own_libs == 1:
            score -= 3500 if capture_count == 0 else 400
        elif own_libs == 2 and not tactical:
            score -= 80

        # Mild preference to stay reasonably central if otherwise equal
        tie = - (abs(r - 9) + abs(c - 9))

        return score, tie, captured

    for idx in candidates:
        res = evaluate(idx)
        if res is None:
            continue
        score, tie, captured = res
        if (best_score is None or score > best_score or
            (score == best_score and tie > best_tie) or
            (score == best_score and tie == best_tie and idx < best_idx)):
            best_idx = idx
            best_score = score
            best_tie = tie
            best_captured = captured

    # Full fallback scan if needed.
    if best_idx is None:
        for idx in range(N):
            if board[idx] != 0:
                continue
            res = evaluate(idx)
            if res is None:
                continue
            score, tie, captured = res
            if (best_score is None or score > best_score or
                (score == best_score and tie > best_tie) or
                (score == best_score and tie == best_tie and idx < best_idx)):
                best_idx = idx
                best_score = score
                best_tie = tie
                best_captured = captured

    if best_idx is None:
        # No legal move besides pass.
        return (0, 0), {"prev_board": _encode_state(me_set, opp_set)}

    move = _pos_from_idx(best_idx)

    new_me = set(me_set)
    new_me.add(best_idx)
    if best_captured:
        new_opp = opp_set.difference(best_captured)
    else:
        new_opp = set(opp_set)

    return move, {"prev_board": _encode_state(new_me, new_opp)}
