
from typing import List, Tuple, Dict, Set

BOARD_SIZE = 19
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    me_set = set(me)
    opp_set = set(opponent)

    prev_board_key = memory.get("prev_board")
    current_board_key = _board_key(me_set, opp_set)

    candidates = _generate_candidates(me_set, opp_set)

    best_move = None
    best_score = -10**18

    for move in candidates:
        if move in me_set or move in opp_set:
            continue
        legal, new_me, new_opp, captured = _play_move(me_set, opp_set, move, prev_board_key)
        if not legal:
            continue
        score = _score_move(me_set, opp_set, move, new_me, new_opp, captured)
        if score > best_score:
            best_score = score
            best_move = move

    if best_move is None:
        # Full-board fallback: search every point once.
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                move = (r, c)
                if move in me_set or move in opp_set:
                    continue
                legal, new_me, new_opp, captured = _play_move(me_set, opp_set, move, prev_board_key)
                if not legal:
                    continue
                score = _score_move(me_set, opp_set, move, new_me, new_opp, captured)
                if score > best_score:
                    best_score = score
                    best_move = move

    if best_move is None:
        new_memory = {"prev_board": current_board_key}
        return (0, 0), new_memory

    # Store current board as previous board for next call so we can avoid simple ko.
    new_memory = {"prev_board": current_board_key}
    return best_move, new_memory


def _board_key(me_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]]):
    return (tuple(sorted(me_set)), tuple(sorted(opp_set)))


def _on_board(p: Tuple[int, int]) -> bool:
    return 1 <= p[0] <= BOARD_SIZE and 1 <= p[1] <= BOARD_SIZE


def _neighbors(p: Tuple[int, int]):
    r, c = p
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
            yield (nr, nc)


def _get_group_and_liberties(start: Tuple[int, int], stones: Set[Tuple[int, int]], occupied: Set[Tuple[int, int]]):
    stack = [start]
    group = set()
    liberties = set()
    while stack:
        p = stack.pop()
        if p in group:
            continue
        group.add(p)
        for nb in _neighbors(p):
            if nb in stones:
                if nb not in group:
                    stack.append(nb)
            elif nb not in occupied:
                liberties.add(nb)
    return group, liberties


def _play_move(me_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]], move: Tuple[int, int], prev_board_key):
    if move in me_set or move in opp_set:
        return False, None, None, 0

    new_me = set(me_set)
    new_opp = set(opp_set)
    new_me.add(move)

    occupied = new_me | new_opp
    captured = 0

    # Capture adjacent opponent groups with no liberties.
    checked = set()
    for nb in _neighbors(move):
        if nb in new_opp and nb not in checked:
            grp, libs = _get_group_and_liberties(nb, new_opp, occupied)
            checked |= grp
            if len(libs) == 0:
                captured += len(grp)
                new_opp -= grp
                occupied -= grp

    # Check suicide after captures.
    my_group, my_libs = _get_group_and_liberties(move, new_me, new_me | new_opp)
    if len(my_libs) == 0:
        return False, None, None, 0

    # Simple ko avoidance: don't recreate the immediately previous board.
    if prev_board_key is not None:
        new_board_key = _board_key(new_opp, new_me)  # next turn perspective after we move? No.
        # Compare in absolute colors from current player's perspective:
        # Since next call perspective swaps, but ko rule is board-position based.
        # We stored current board from our previous turn as (our stones then, opp stones then),
        # and right now me/opponent are current colors. For immediate ko, compare absolute current orientation:
        new_board_key = _board_key(new_me, new_opp)
        if new_board_key == prev_board_key:
            return False, None, None, 0

    return True, new_me, new_opp, captured


def _generate_candidates(me_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]]):
    occupied = me_set | opp_set
    candidates = set()

    if not occupied:
        # Strong opening points: center + star points.
        openings = [
            (4, 4), (4, 16), (16, 4), (16, 16),
            (10, 10), (4, 10), (10, 4), (10, 16), (16, 10),
            (7, 7), (7, 13), (13, 7), (13, 13),
        ]
        return openings

    # Add empty neighbors and second-ring points around all stones.
    for p in occupied:
        r, c = p
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if abs(dr) + abs(dc) > 3:
                    continue
                q = (r + dr, c + dc)
                if _on_board(q) and q not in occupied:
                    candidates.add(q)

    # Tactical urgency: liberties of groups in atari / near atari.
    for stones, friendly in ((opp_set, False), (me_set, True)):
        seen = set()
        for s in stones:
            if s in seen:
                continue
            grp, libs = _get_group_and_liberties(s, stones, occupied)
            seen |= grp
            if len(libs) <= 2:
                candidates |= libs

    # If still sparse, add some strategic anchor points.
    if len(candidates) < 20:
        strategic = [
            (4, 4), (4, 16), (16, 4), (16, 16),
            (10, 10), (4, 10), (10, 4), (10, 16), (16, 10),
            (7, 7), (7, 13), (13, 7), (13, 13),
        ]
        for p in strategic:
            if p not in occupied:
                candidates.add(p)

    return list(candidates)


def _score_move(old_me: Set[Tuple[int, int]], old_opp: Set[Tuple[int, int]], move: Tuple[int, int],
                new_me: Set[Tuple[int, int]], new_opp: Set[Tuple[int, int]], captured: int) -> float:
    score = 0.0
    occupied_old = old_me | old_opp
    occupied_new = new_me | new_opp

    # 1. Captures are highly valuable.
    score += 1000 * captured

    # 2. If move saves one of our groups that was in atari, reward strongly.
    saved_bonus = 0
    seen = set()
    for s in old_me:
        if s in seen:
            continue
        grp, libs = _get_group_and_liberties(s, old_me, occupied_old)
        seen |= grp
        if len(libs) == 1 and move in libs:
            new_grp, new_libs = _get_group_and_liberties(move, new_me, occupied_new)
            saved_bonus += 300 + 30 * len(new_grp) + 20 * len(new_libs)
    score += saved_bonus

    # 3. Pressure enemy groups adjacent to the move.
    checked = set()
    for nb in _neighbors(move):
        if nb in old_opp and nb not in checked:
            grp, libs = _get_group_and_liberties(nb, old_opp, occupied_old)
            checked |= grp
            if len(libs) == 1 and move in libs:
                score += 500 + 20 * len(grp)
            elif len(libs) == 2 and move in libs:
                score += 120 + 10 * len(grp)

    # 4. Reward liberties of the resulting group.
    my_group, my_libs = _get_group_and_liberties(move, new_me, occupied_new)
    score += 18 * len(my_libs)
    score += 2 * len(my_group)

    # 5. Prefer connection to own stones and contact with weak enemy stones.
    friendly_adj = 0
    enemy_adj = 0
    empty_adj = 0
    for nb in _neighbors(move):
        if nb in old_me:
            friendly_adj += 1
        elif nb in old_opp:
            enemy_adj += 1
        else:
            empty_adj += 1

    score += 14 * friendly_adj
    score += 6 * enemy_adj
    score += 2 * empty_adj

    # 6. Avoid filling our own true eyes approximately.
    if friendly_adj >= 3 and enemy_adj == 0:
        score -= 80

    # 7. Opening / positional preference toward center and star-point geometry.
    r, c = move
    center_dist = abs(r - 10) + abs(c - 10)
    score -= 0.8 * center_dist

    if (r in (4, 10, 16)) and (c in (4, 10, 16)):
        score += 12
    if (r in (7, 13)) and (c in (7, 13)):
        score += 6

    # 8. Small local density heuristic: prefer moves near existing stones, not isolated.
    local = 0
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            if dr == 0 and dc == 0:
                continue
            q = (r + dr, c + dc)
            if not _on_board(q):
                continue
            if q in occupied_old:
                local += 1
    score += 1.5 * local

    return score
