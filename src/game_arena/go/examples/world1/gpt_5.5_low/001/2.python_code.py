
from collections import deque
from typing import List, Tuple, Set

BOARD_SIZE = 19
Move = Tuple[int, int]


def policy(me: List[Move], opponent: List[Move]) -> Move:
    my = set(me)
    opp = set(opponent)
    occupied = my | opp

    def on_board(r: int, c: int) -> bool:
        return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE

    def neighbors(p: Move):
        r, c = p
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if on_board(nr, nc):
                yield (nr, nc)

    def group_and_liberties(start: Move, stones: Set[Move], enemy: Set[Move]):
        group = set()
        liberties = set()
        q = deque([start])
        group.add(start)

        while q:
            p = q.popleft()
            for nb in neighbors(p):
                if nb in stones and nb not in group:
                    group.add(nb)
                    q.append(nb)
                elif nb not in stones and nb not in enemy:
                    liberties.add(nb)

        return group, liberties

    group_cache_my = {}
    group_cache_opp = {}

    def get_group(p: Move, stones: Set[Move], enemy: Set[Move], cache: dict):
        if p in cache:
            return cache[p]
        g, libs = group_and_liberties(p, stones, enemy)
        result = (g, libs)
        for s in g:
            cache[s] = result
        return result

    def legal_and_features(move: Move):
        if move in occupied:
            return False, None

        adjacent_empty = 0
        adjacent_my_groups = []
        adjacent_opp_groups = []
        captured = set()
        save_stones = 0
        attack_stones = 0

        seen_my = set()
        seen_opp = set()

        for nb in neighbors(move):
            if nb not in occupied:
                adjacent_empty += 1
            elif nb in my:
                g, libs = get_group(nb, my, opp, group_cache_my)
                key = next(iter(g))
                if key not in seen_my:
                    seen_my.add(key)
                    adjacent_my_groups.append((g, libs))
                    if libs == {move}:
                        save_stones += len(g)
            elif nb in opp:
                g, libs = get_group(nb, opp, my, group_cache_opp)
                key = next(iter(g))
                if key not in seen_opp:
                    seen_opp.add(key)
                    adjacent_opp_groups.append((g, libs))
                    if libs == {move}:
                        captured |= g
                    elif move in libs and len(libs) == 2:
                        attack_stones += len(g)

        capture_count = len(captured)

        # Suicide check.
        legal = False
        if capture_count > 0 or adjacent_empty > 0:
            legal = True
        else:
            for g, libs in adjacent_my_groups:
                if len(libs - {move}) > 0:
                    legal = True
                    break

        if not legal:
            return False, None

        # Estimate liberties after move.
        new_libs = set()
        for nb in neighbors(move):
            if nb not in occupied:
                new_libs.add(nb)

        for g, libs in adjacent_my_groups:
            new_libs |= (libs - {move})

        # Captured stones become liberties.
        new_libs |= captured

        features = {
            "capture": capture_count,
            "save": save_stones,
            "attack": attack_stones,
            "new_libs": len(new_libs),
            "adj_empty": adjacent_empty,
            "adj_my": len(adjacent_my_groups),
            "adj_opp": len(adjacent_opp_groups),
        }
        return True, features

    def positional_score(move: Move) -> float:
        r, c = move

        # Prefer normal Go opening shape: corners, sides, then center.
        star_points = {
            (4, 4), (4, 10), (4, 16),
            (10, 4), (10, 10), (10, 16),
            (16, 4), (16, 10), (16, 16),
        }

        score = 0.0

        if move in star_points:
            score += 55.0

        # Good distance from edge: avoid first line unless tactical.
        edge_dist = min(r, c, BOARD_SIZE + 1 - r, BOARD_SIZE + 1 - c)
        if edge_dist == 4:
            score += 35.0
        elif edge_dist == 3:
            score += 28.0
        elif edge_dist == 5:
            score += 18.0
        elif edge_dist == 2:
            score += 5.0
        elif edge_dist == 1:
            score -= 25.0

        # Mild center preference.
        center_dist = abs(r - 10) + abs(c - 10)
        score += max(0, 18 - center_dist) * 1.2

        # Corners are very valuable early.
        corner_targets = [(4, 4), (4, 16), (16, 4), (16, 16)]
        for cr, cc in corner_targets:
            d = abs(r - cr) + abs(c - cc)
            if d == 0:
                score += 25.0
            elif d <= 2:
                score += 10.0

        return score

    def influence_score(move: Move) -> float:
        r, c = move
        score = 0.0

        # Encourage playing near own stones, but not too clustered.
        for s in my:
            d = abs(r - s[0]) + abs(c - s[1])
            if d == 2:
                score += 10.0
            elif d == 3:
                score += 8.0
            elif d == 4:
                score += 5.0
            elif d == 1:
                score += 2.0

        # Encourage pressure near opponent stones.
        for s in opp:
            d = abs(r - s[0]) + abs(c - s[1])
            if d == 1:
                score += 8.0
            elif d == 2:
                score += 7.0
            elif d == 3:
                score += 4.0

        return score

    total_stones = len(my) + len(opp)

    # Candidate generation.
    candidates = set()

    # Strong opening book.
    opening_points = [
        (4, 4), (16, 16), (4, 16), (16, 4),
        (10, 10),
        (4, 10), (16, 10), (10, 4), (10, 16),
        (10, 3), (10, 17), (3, 10), (17, 10),
    ]
    for p in opening_points:
        if p not in occupied:
            candidates.add(p)

    # Tactical candidates: near existing stones.
    for s in occupied:
        sr, sc = s
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if abs(dr) + abs(dc) <= 4:
                    p = (sr + dr, sc + dc)
                    if on_board(*p) and p not in occupied:
                        candidates.add(p)

    # If board is sparse or candidate set somehow empty, include all empties.
    if not candidates or total_stones < 6:
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                if (r, c) not in occupied:
                    candidates.add((r, c))

    best_move = None
    best_score = -10**18

    for mv in candidates:
        legal, f = legal_and_features(mv)
        if not legal:
            continue

        score = 0.0

        # Tactics dominate.
        score += f["capture"] * 1200.0
        score += f["save"] * 950.0
        score += f["attack"] * 230.0

        # Shape and liberties.
        score += min(f["new_libs"], 8) * 35.0
        score += f["adj_my"] * 12.0
        score -= max(0, f["adj_opp"] - f["adj_my"]) * 4.0

        # Avoid self-atari unless it captures or saves something.
        if f["new_libs"] <= 1 and f["capture"] == 0 and f["save"] == 0:
            score -= 700.0
        elif f["new_libs"] == 2 and f["capture"] == 0:
            score -= 80.0

        # Positional priorities.
        if total_stones < 30:
            score += positional_score(mv) * 2.0
        else:
            score += positional_score(mv) * 0.7

        score += influence_score(mv)

        # Small deterministic tie-breaker favoring central board.
        score -= (abs(mv[0] - 10) + abs(mv[1] - 10)) * 0.01

        if score > best_score:
            best_score = score
            best_move = mv

    if best_move is not None:
        return best_move

    # Absolute safety fallback: scan every point for any legal move.
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            mv = (r, c)
            legal, _ = legal_and_features(mv)
            if legal:
                return mv

    # If no legal moves exist, pass.
    return (0, 0)
