
from typing import List, Tuple, Dict
import math

BOARD_SIZE = 19
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    try:
        board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        for r, c in me:
            if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
                board[r - 1][c - 1] = 1
        for r, c in opponent:
            if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
                board[r - 1][c - 1] = 2

        move = choose_move(board, memory if isinstance(memory, dict) else {})
        if move is None:
            move = first_legal_move(board)
        if move is None:
            move = (0, 0)
        return move, (memory if isinstance(memory, dict) else {})
    except Exception:
        # Guaranteed legal fallback
        try:
            board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
            for r, c in me:
                if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
                    board[r - 1][c - 1] = 1
            for r, c in opponent:
                if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
                    board[r - 1][c - 1] = 2
            mv = first_legal_move(board)
            if mv is None:
                return (0, 0), {}
            return mv, {}
        except Exception:
            return (0, 0), {}


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def neighbors(r: int, c: int):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc):
            yield nr, nc


def group_and_liberties(board, r, c):
    color = board[r][c]
    if color == 0:
        return set(), set()
    stack = [(r, c)]
    seen = {(r, c)}
    group = set()
    libs = set()
    while stack:
        x, y = stack.pop()
        group.add((x, y))
        for nx, ny in neighbors(x, y):
            v = board[nx][ny]
            if v == 0:
                libs.add((nx, ny))
            elif v == color and (nx, ny) not in seen:
                seen.add((nx, ny))
                stack.append((nx, ny))
    return group, libs


def play_move(board, move, color):
    # Returns new_board if legal, else None
    if move == (0, 0):
        return [row[:] for row in board]
    r, c = move[0] - 1, move[1] - 1
    if not in_bounds(r, c):
        return None
    if board[r][c] != 0:
        return None

    opp = 3 - color
    nb = [row[:] for row in board]
    nb[r][c] = color

    # Capture adjacent opponent groups with no liberties
    checked = set()
    for nr, nc in neighbors(r, c):
        if nb[nr][nc] == opp and (nr, nc) not in checked:
            grp, libs = group_and_liberties(nb, nr, nc)
            checked |= grp
            if len(libs) == 0:
                for gx, gy in grp:
                    nb[gx][gy] = 0

    # Suicide check on placed stone's group
    grp, libs = group_and_liberties(nb, r, c)
    if len(libs) == 0:
        return None

    return nb


def legal_moves(board, color=1):
    moves = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r - 1][c - 1] == 0 and play_move(board, (r, c), color) is not None:
                moves.append((r, c))
    if not moves:
        moves.append((0, 0))
    return moves


def first_legal_move(board, color=1):
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r - 1][c - 1] == 0 and play_move(board, (r, c), color) is not None:
                return (r, c)
    return (0, 0)


def count_captured(prev_board, new_board, opp_color):
    prev = 0
    new = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if prev_board[r][c] == opp_color:
                prev += 1
            if new_board[r][c] == opp_color:
                new += 1
    return prev - new


def local_density(board, r, c, color, dist=2):
    score = 0
    for i in range(max(0, r - dist), min(BOARD_SIZE, r + dist + 1)):
        for j in range(max(0, c - dist), min(BOARD_SIZE, c + dist + 1)):
            d = abs(i - r) + abs(j - c)
            if d == 0 or d > dist:
                continue
            if board[i][j] == color:
                score += 1.0 / d
            elif board[i][j] == 3 - color:
                score -= 0.8 / d
    return score


def center_bias(r, c):
    cr = 9
    cc = 9
    return -0.12 * (abs(r - cr) + abs(c - cc))


def star_point_bonus(r, c, stones_played):
    # Encourage sensible openings on 4-4 / 3-4 / center-ish
    pts = {(3, 3), (3, 9), (3, 15),
           (9, 3), (9, 9), (9, 15),
           (15, 3), (15, 9), (15, 15),
           (3, 15), (15, 15), (15, 3), (3, 3),
           (3, 9), (9, 3), (9, 15), (15, 9),
           (3, 4), (4, 3), (3, 15), (4, 15), (15, 3), (15, 4), (15, 15), (15, 16),
           (4, 4), (4, 10), (4, 16), (10, 4), (10, 10), (10, 16), (16, 4), (16, 10), (16, 16)}
    if stones_played <= 8:
        rr, cc = r + 1, c + 1
        if (rr - 1, cc - 1) in pts or (rr, cc) in pts:
            return 1.5
        if 3 <= rr <= 15 and 3 <= cc <= 15:
            return 0.4
    return 0.0


def adjacent_info(board, r, c, color):
    empty_n = 0
    my_n = 0
    opp_n = 0
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == 0:
            empty_n += 1
        elif board[nr][nc] == color:
            my_n += 1
        else:
            opp_n += 1
    return empty_n, my_n, opp_n


def tactical_scores(board, move, color=1):
    if move == (0, 0):
        return -1000.0

    r, c = move[0] - 1, move[1] - 1
    nb = play_move(board, move, color)
    if nb is None:
        return -10**9

    opp = 3 - color
    score = 0.0

    # Captures
    captured = count_captured(board, nb, opp)
    score += 30.0 * captured

    # New group's liberties
    grp, libs = group_and_liberties(nb, r, c)
    nlibs = len(libs)
    if nlibs == 1:
        score -= 18.0
    elif nlibs == 2:
        score += 1.5
    else:
        score += 3.0 + 1.0 * min(nlibs, 6)

    # Connections to own stones / avoiding isolation
    empty_n, my_n, opp_n = adjacent_info(board, r, c, color)
    score += 2.8 * my_n
    score += 1.3 * opp_n
    if my_n == 0 and opp_n == 0:
        score -= 3.5

    # Save own adjacent atari groups
    seen = set()
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == color and (nr, nc) not in seen:
            grp0, libs0 = group_and_liberties(board, nr, nc)
            seen |= grp0
            if len(libs0) == 1 and (r, c) in libs0:
                # Strong rescue incentive
                grp1, libs1 = group_and_liberties(nb, r, c)
                score += 22.0 + 2.0 * min(len(libs1), 5)

    # Attack opponent adjacent weak groups
    seen = set()
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == opp and (nr, nc) not in seen:
            grp0, libs0 = group_and_liberties(board, nr, nc)
            seen |= grp0
            if len(libs0) == 1 and (r, c) in libs0:
                score += 25.0 + 5.0 * len(grp0)
            elif len(libs0) == 2 and (r, c) in libs0:
                score += 7.0 + 0.8 * len(grp0)

    # Shape/locality
    score += local_density(board, r, c, color, dist=2)
    score += center_bias(r, c)

    # Opening preference
    stones_played = sum(1 for rr in range(BOARD_SIZE) for cc in range(BOARD_SIZE) if board[rr][cc] != 0)
    score += star_point_bonus(r, c, stones_played)

    # Edge/corner slight penalties unless tactical
    if r in (0, BOARD_SIZE - 1):
        score -= 0.7
    if c in (0, BOARD_SIZE - 1):
        score -= 0.7
    if r in (1, BOARD_SIZE - 2):
        score -= 0.2
    if c in (1, BOARD_SIZE - 2):
        score -= 0.2

    return score


def choose_move(board, memory):
    moves = legal_moves(board, 1)
    if moves == [(0, 0)]:
        return (0, 0)

    best_move = None
    best_score = -10**18

    # Candidate filtering: prioritize local moves if board not empty, but keep all tactical moves
    stones = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] != 0]
    if stones:
        near = set()
        for r, c in stones:
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and board[nr][nc] == 0:
                        near.add((nr + 1, nc + 1))
        candidate_moves = []
        for mv in moves:
            if mv in near:
                candidate_moves.append(mv)
            else:
                # keep tactical moves with immediate effect
                nb = play_move(board, mv, 1)
                if nb is not None:
                    if count_captured(board, nb, 2) > 0:
                        candidate_moves.append(mv)
                        continue
                    r, c = mv[0] - 1, mv[1] - 1
                    tactical = False
                    for nr, nc in neighbors(r, c):
                        if board[nr][nc] != 0:
                            tactical = True
                            break
                    if tactical:
                        candidate_moves.append(mv)
        if not candidate_moves:
            candidate_moves = moves
    else:
        candidate_moves = moves

    for mv in candidate_moves:
        s = tactical_scores(board, mv, 1)
        # deterministic tie-breaker: prefer closer to center, then lower row/col
        if mv != (0, 0):
            r, c = mv[0] - 1, mv[1] - 1
            tie = -0.001 * (abs(r - 9) + abs(c - 9)) - 0.000001 * (r * 19 + c)
        else:
            tie = -999
        s += tie
        if s > best_score:
            best_score = s
            best_move = mv

    if best_move is not None and play_move(board, best_move, 1) is not None:
        return best_move

    return first_legal_move(board, 1)
