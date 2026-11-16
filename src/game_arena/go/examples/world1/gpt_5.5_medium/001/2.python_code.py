
from typing import List, Tuple, Dict, Set

BOARD_SIZE = 19
EMPTY = 0
ME = 1
OPP = 2


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    for r, c in me:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = ME

    for r, c in opponent:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = OPP

    total_stones = len(me) + len(opponent)

    groups, gid_grid = _build_groups(board)

    # Empty-board opening.
    if total_stones == 0:
        return (4, 4)

    best_move = None
    best_score = -10**18

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                continue
            pos = (r, c)
            if not _is_legal(pos, board, groups, gid_grid):
                continue

            score = _score_move(pos, board, groups, gid_grid, me, opponent, total_stones)

            # Tiny deterministic tie-breaker to avoid always choosing upper-left
            # in exact ties while remaining fully reproducible.
            score += ((r * 37 + c * 17 + total_stones * 13) % 23) / 1000.0

            if score > best_score:
                best_score = score
                best_move = pos

    if best_move is None:
        return (0, 0)

    return (best_move[0] + 1, best_move[1] + 1)


def _neighbors(r: int, c: int):
    if r > 0:
        yield r - 1, c
    if r < BOARD_SIZE - 1:
        yield r + 1, c
    if c > 0:
        yield r, c - 1
    if c < BOARD_SIZE - 1:
        yield r, c + 1


def _build_groups(board):
    gid_grid = [[-1 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    groups: Dict[int, dict] = {}
    gid = 0

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            color = board[r][c]
            if color == EMPTY or gid_grid[r][c] != -1:
                continue

            stack = [(r, c)]
            gid_grid[r][c] = gid
            stones = []
            libs = set()

            while stack:
                x, y = stack.pop()
                stones.append((x, y))

                for nx, ny in _neighbors(x, y):
                    if board[nx][ny] == EMPTY:
                        libs.add((nx, ny))
                    elif board[nx][ny] == color and gid_grid[nx][ny] == -1:
                        gid_grid[nx][ny] = gid
                        stack.append((nx, ny))

            groups[gid] = {
                "color": color,
                "stones": stones,
                "libs": libs,
                "size": len(stones),
            }
            gid += 1

    return groups, gid_grid


def _is_legal(pos, board, groups, gid_grid) -> bool:
    r, c = pos
    if board[r][c] != EMPTY:
        return False

    adjacent_friend = set()
    adjacent_enemy = set()

    for nr, nc in _neighbors(r, c):
        val = board[nr][nc]
        if val == EMPTY:
            return True
        gid = gid_grid[nr][nc]
        if val == ME:
            adjacent_friend.add(gid)
        elif val == OPP:
            adjacent_enemy.add(gid)

    # Capturing an adjacent opponent group is legal.
    for gid in adjacent_enemy:
        if len(groups[gid]["libs"]) == 1:
            return True

    # Connecting to a friendly group with an outside liberty is legal.
    for gid in adjacent_friend:
        if len(groups[gid]["libs"]) > 1:
            return True

    return False


def _score_move(pos, board, groups, gid_grid, me, opponent, total_stones) -> float:
    r, c = pos
    score = 0.0

    adjacent_friend = set()
    adjacent_enemy = set()
    empty_neighbors = 0

    for nr, nc in _neighbors(r, c):
        val = board[nr][nc]
        if val == EMPTY:
            empty_neighbors += 1
        elif val == ME:
            adjacent_friend.add(gid_grid[nr][nc])
        elif val == OPP:
            adjacent_enemy.add(gid_grid[nr][nc])

    capture_score = 0.0
    attack_score = 0.0
    defense_score = 0.0

    # Tactical attack/capture.
    for gid in adjacent_enemy:
        g = groups[gid]
        libs = len(g["libs"])
        size = g["size"]

        if pos in g["libs"]:
            if libs == 1:
                capture_score += 10000 + 260 * size
            elif libs == 2:
                attack_score += 1800 + 100 * size
            elif libs == 3:
                attack_score += 250 + 25 * size
            else:
                attack_score += 25 + 3 * size

    # Tactical defense.
    for gid in adjacent_friend:
        g = groups[gid]
        libs = len(g["libs"])
        size = g["size"]

        if pos in g["libs"]:
            if libs == 1:
                defense_score += 7600 + 190 * size
            elif libs == 2:
                defense_score += 950 + 55 * size
            elif libs == 3:
                defense_score += 150 + 18 * size

    score += capture_score + attack_score + defense_score

    # Estimate liberties after the move.
    result_libs = set()
    for nr, nc in _neighbors(r, c):
        val = board[nr][nc]
        if val == EMPTY:
            result_libs.add((nr, nc))
        elif val == ME:
            gid = gid_grid[nr][nc]
            result_libs.update(groups[gid]["libs"])
        elif val == OPP:
            gid = gid_grid[nr][nc]
            if len(groups[gid]["libs"]) == 1:
                # Approximation: captured stones become liberties.
                result_libs.update(groups[gid]["stones"])

    result_libs.discard(pos)
    estimated_liberties = len(result_libs)

    score += 18 * estimated_liberties
    score += 8 * empty_neighbors

    # Connections and cuts.
    if len(adjacent_friend) >= 2:
        score += 350 + 90 * (len(adjacent_friend) - 2)
    elif len(adjacent_friend) == 1:
        score += 35

    if len(adjacent_enemy) >= 2:
        score += 230 + 60 * (len(adjacent_enemy) - 2)

    # Avoid self-atari unless the move has strong tactical purpose.
    tactical_value = capture_score + defense_score
    if tactical_value < 1000:
        if estimated_liberties <= 1:
            score -= 1400
        elif estimated_liberties == 2:
            score -= 180

    # Positional/opening value.
    score += _positional_score(r, c, total_stones)

    # Opening: prefer large points, star points, and spreading out.
    if total_stones < 40:
        score += _opening_bonus(r, c, board, me, opponent, total_stones)

    # Local influence: prefer meaningful contact/proximity without clumping too much.
    score += _influence_score(r, c, me, opponent)

    # Avoid filling clear own eyes when not tactically necessary.
    if tactical_value < 1000 and _looks_like_own_eye(r, c, board):
        score -= 2500

    # Discourage useless first-line play outside tactics.
    edge_dist = min(r, c, BOARD_SIZE - 1 - r, BOARD_SIZE - 1 - c)
    if edge_dist == 0 and tactical_value < 1000:
        score -= 250
    if edge_dist == 1 and tactical_value < 500 and total_stones < 180:
        score -= 80

    return score


def _positional_score(r: int, c: int, total_stones: int) -> float:
    # Distance from nearest edge, zero-indexed.
    edge = min(r, c, BOARD_SIZE - 1 - r, BOARD_SIZE - 1 - c)
    score = 0.0

    if edge == 0:
        score -= 120
    elif edge == 1:
        score -= 25 if total_stones < 220 else 0
    elif edge == 2:
        score += 28
    elif edge == 3:
        score += 48
    elif edge == 4:
        score += 22
    else:
        score += 6

    rr = r + 1
    cc = c + 1

    # Star-point and key opening coordinates.
    star = {4, 10, 16}
    if rr in star and cc in star:
        score += 55

    # Corner framework points.
    corner_points = {
        (4, 4), (4, 16), (16, 4), (16, 16),
        (3, 4), (4, 3), (3, 16), (4, 17),
        (16, 3), (17, 4), (16, 17), (17, 16),
    }
    if (rr, cc) in corner_points:
        score += 75

    # Side extensions.
    if (rr in {4, 16} and cc in {7, 10, 13}) or (cc in {4, 16} and rr in {7, 10, 13}):
        score += 30

    return score


def _opening_bonus(r: int, c: int, board, me, opponent, total_stones: int) -> float:
    rr = r + 1
    cc = c + 1

    preferred = [
        (4, 4), (16, 16), (4, 16), (16, 4),
        (10, 4), (10, 16), (4, 10), (16, 10),
        (10, 10),
        (4, 7), (7, 4), (4, 13), (7, 16),
        (13, 4), (16, 7), (13, 16), (16, 13),
    ]

    score = 0.0
    if (rr, cc) in preferred:
        score += 260 - 4 * preferred.index((rr, cc))

    stones = [(x - 1, y - 1) for x, y in me + opponent]

    if stones:
        nearest = min(abs(r - x) + abs(c - y) for x, y in stones)
        # In the opening, avoid playing too close to existing stones unless tactical.
        if nearest <= 1:
            score -= 140
        elif nearest == 2:
            score -= 45
        elif 4 <= nearest <= 9:
            score += 45
        elif nearest >= 12:
            score += 20

    # If opponent has occupied nearby corner, approach/enclose points can be useful.
    opp0 = [(x - 1, y - 1) for x, y in opponent]
    for ox, oy in opp0:
        d = abs(r - ox) + abs(c - oy)
        if 3 <= d <= 6:
            # Approach distance.
            if min(ox, oy, BOARD_SIZE - 1 - ox, BOARD_SIZE - 1 - oy) <= 4:
                score += 18

    return score


def _influence_score(r: int, c: int, me, opponent) -> float:
    score = 0.0

    for sr, sc in me:
        x = sr - 1
        y = sc - 1
        d = abs(r - x) + abs(c - y)
        if d == 0:
            continue
        if d <= 4:
            score += (5 - d) * 6
        elif d <= 7:
            score += 4

    for sr, sc in opponent:
        x = sr - 1
        y = sc - 1
        d = abs(r - x) + abs(c - y)
        if d == 0:
            continue
        if d <= 2:
            score += (3 - d) * 10
        elif d <= 5:
            score += (6 - d) * 3

    return score


def _looks_like_own_eye(r: int, c: int, board) -> bool:
    # A simple own-eye detector: all orthogonal neighbors are our stones or edge.
    # This avoids wasting moves filling secure eyes unless tactical scoring overrides it.
    for nr, nc in _neighbors(r, c):
        if board[nr][nc] != ME:
            return False

    diagonals = []
    for dr in (-1, 1):
        for dc in (-1, 1):
            nr = r + dr
            nc = c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                diagonals.append(board[nr][nc])
            else:
                diagonals.append(ME)

    bad = sum(1 for v in diagonals if v == OPP)
    return bad <= 1
