
import random

# ------- Utility functions for Pentago (6x6, 3x3 quadrants) -------

N = 6
QSIZE = 3

def _rotate_subgrid(grid, quad, dir_):
    """Return a new 6x6 grid after rotating the chosen 3x3 quadrant.
    dir_ is 'L' (anticlockwise) or 'R' (clockwise).
    This rotates both players' marbles together because it operates on the full board.
    """
    r0 = (quad // 2) * QSIZE           # 0 or 3
    c0 = (quad % 2) * QSIZE            # 0 or 3

    # copy
    newg = [row[:] for row in grid]
    # extract 3x3
    sub = [[grid[r0 + i][c0 + j] for j in range(QSIZE)] for i in range(QSIZE)]

    if dir_ == 'R':  # clockwise: (i,j) -> (j, N-1-i)
        for i in range(QSIZE):
            for j in range(QSIZE):
                newg[r0 + i][c0 + j] = sub[QSIZE - 1 - j][i]
    else:  # 'L' anticlockwise: (i,j) -> (N-1-j, i)
        for i in range(QSIZE):
            for j in range(QSIZE):
                newg[r0 + i][c0 + j] = sub[j][QSIZE - 1 - i]
    return newg

def _apply_move(you, opponent, row, col, quad, dir_):
    """Apply placing your marble at (row,col) (0-indexed), then rotate quadrant.
    Returns (new_you, new_opponent).
    """
    r, c = row, col
    you2 = [rrow[:] for rrow in you]
    opp2 = [rrow[:] for rrow in opponent]
    you2[r][c] = 1

    # Rotation affects both players in the same quadrant
    you2 = _rotate_subgrid(you2, quad, dir_)
    opp2 = _rotate_subgrid(opp2, quad, dir_)
    return you2, opp2

def _has_5_in_a_row(grid):
    """Check if grid has 5 or more consecutive 1s in any row/col/diagonal direction.
    6x6: need at least 5 consecutive.
    Returns True if exists.
    """
    # directions: (0,1), (1,0), (1,1), (1,-1)
    dirs = [(0,1),(1,0),(1,1),(1,-1)]
    for r in range(N):
        for c in range(N):
            if grid[r][c] != 1:
                continue
            for dr, dc in dirs:
                # count consecutive from (r,c)
                k = 0
                rr, cc = r, c
                while 0 <= rr < N and 0 <= cc < N and grid[rr][cc] == 1:
                    k += 1
                    rr += dr
                    cc += dc
                if k >= 5:
                    return True
    return False

def _max_consecutive(grid):
    """Return maximum length of consecutive 1s (any direction) for heuristic."""
    dirs = [(0,1),(1,0),(1,1),(1,-1)]
    best = 0
    for r in range(N):
        for c in range(N):
            if grid[r][c] != 1:
                continue
            for dr, dc in dirs:
                k = 0
                rr, cc = r, c
                while 0 <= rr < N and 0 <= cc < N and grid[rr][cc] == 1:
                    k += 1
                    rr += dr
                    cc += dc
                if k > best:
                    best = k
    return best

def _lines_windows_score(grid, player):
    """Score by counting 'open' windows of length 5 in the four directions.
    A window is usable if it contains no opponent marbles; here we score for current player's grid only,
    but we call with grid already masked as 1/0 for player and opponent separate.
    We'll use grid and assume opponent passed separately in outer function.
    """
    return 0  # not used directly

def _score_position(you, opponent):
    """Heuristic score from your perspective for the *current* position (after your move + rotation).
    - Huge reward for your win.
    - Huge penalty for opponent win.
    - Otherwise: reward longer consecutive runs and more 'potential lines'.
    """
    if _has_5_in_a_row(you):
        return 10_000
    if _has_5_in_a_row(opponent):
        return -10_000

    # Base: longest consecutive run
    you_best = _max_consecutive(you)
    opp_best = _max_consecutive(opponent)
    score = (you_best - opp_best) * 500

    # Additional: count number of length-5 windows that are "good"
    # For each direction, consider all segments of 5 consecutive cells.
    dirs = [(0,1),(1,0),(1,1),(1,-1)]
    good_you = 0
    good_opp = 0

    def window_ok(seg, player_grid):
        # seg is list of coordinates; check whether opponent has any in those coords
        cnt_player = 0
        for rr, cc in seg:
            if player_grid[rr][cc] == 1:
                cnt_player += 1
        return cnt_player

    # We explicitly compute for each 5-segment: for you, segment has no opponent marbles (all opponent cells are 0)
    # and for opponent similarly.
    # Reward higher counts with exponential-ish weighting.
    for r in range(N):
        for c in range(N):
            for dr, dc in dirs:
                end_r = r + dr*4
                end_c = c + dc*4
                if not (0 <= end_r < N and 0 <= end_c < N):
                    continue
                # collect coords
                coords = [(r + dr*i, c + dc*i) for i in range(5)]
                you_cnt = sum(1 for rr, cc in coords if you[rr][cc] == 1)
                opp_cnt = sum(1 for rr, cc in coords if opponent[rr][cc] == 1)

                # If the segment is blocked for you (opponent has any), it can't become a 5-in-row for you
                if opp_cnt == 0 and you_cnt > 0:
                    good_you += you_cnt
                # similarly for opponent
                if you_cnt == 0 and opp_cnt > 0:
                    good_opp += opp_cnt

    # Encourage more pieces in open segments, but keep within reasonable bounds
    score += (good_you - good_opp) * 25

    # Center preference: prefer placing in more central area tends to increase tactical strength
    center_bonus = 0
    for rr in range(N):
        for cc in range(N):
            if you[rr][cc] == 1:
                # Manhattan distance to center (2.5,2.5) approximate
                dist = abs(rr - 2.5) + abs(cc - 2.5)
                center_bonus += (3.5 - dist)
    score += center_bonus * 5

    return score

def _legal_empty_cells(you, opponent):
    empties = []
    for r in range(N):
        for c in range(N):
            if you[r][c] == 0 and opponent[r][c] == 0:
                empties.append((r, c))
    return empties

def policy(you, opponent) -> str:
    # Normalize inputs to plain Python lists of ints
    you = [list(map(int, row)) for row in you]
    opponent = [list(map(int, row)) for row in opponent]

    empties = _legal_empty_cells(you, opponent)

    # If empty list, shouldn't happen per prompt; still handle safely.
    if not empties:
        return "1,1,0,R"

    best_moves = []
    best_score = -10**18

    # Evaluate all moves
    # For speed: randomize action order slightly to break ties and avoid deterministic worst cases.
    action_quads = [0, 1, 2, 3]
    action_dirs = ['L', 'R']
    random.shuffle(action_quads)
    random.shuffle(action_dirs)
    random.shuffle(empties)

    for (r, c) in empties:
        # Quick tactical: try both rotations for each quadrant
        for quad in action_quads:
            for dir_ in action_dirs:
                you2, opp2 = _apply_move(you, opponent, r, c, quad, dir_)

                # Immediate win?
                if _has_5_in_a_row(you2):
                    score = 10_000_000
                elif _has_5_in_a_row(opp2):
                    score = -10_000_000
                else:
                    # Strongly punish if opponent can win immediately on their next move.
                    # Lookahead depth 1: check best opponent response after rotation.
                    # (Still fast enough: at most many empties, but we cap with quick check.)
                    base = _score_position(you2, opp2)

                    # Determine if opponent has any winning move available immediately.
                    # If yes, apply a large penalty.
                    opp_can_win = False
                    # To reduce runtime, we can early-stop once found.
                    opp_empties = _legal_empty_cells(you2, opp2)
                    # Small cap to keep under time: but still we can check fully usually.
                    # We'll do a full scan unless board is extremely sparse (worst near start).
                    # Pentago usually has many pieces; still safe.
                    check_limit = min(len(opp_empties), 18)  # heuristic bound
                    sampled = opp_empties if len(opp_empties) <= check_limit else random.sample(opp_empties, check_limit)

                    for (orow, ocol) in sampled:
                        # opponent places at empty then rotates some quadrant;
                        # check if any yields opponent win.
                        for oquad in [0,1,2,3]:
                            for odir in ['L','R']:
                                new_you3, new_opp3 = _apply_move(you2, opp2, orow, ocol, oquad, odir)
                                if _has_5_in_a_row(new_opp3):
                                    opp_can_win = True
                                    break
                            if opp_can_win:
                                break
                        if opp_can_win:
                            break

                    score = base - (9000 if opp_can_win else 0)

                # Tie-breaking helpers: prefer higher longest run and then centrality
                if score > best_score:
                    best_score = score
                    best_moves = [(r, c, quad, dir_)]
                elif score == best_score:
                    best_moves.append((r, c, quad, dir_))

    # If multiple best, pick deterministically with a secondary heuristic
    def tie_key(m):
        r, c, quad, dir_ = m
        you2, opp2 = _apply_move(you, opponent, r, c, quad, dir_)
        return (_max_consecutive(you2), -_max_consecutive(opp2), -abs(r-2.5)-abs(c-2.5))

    chosen = max(best_moves, key=tie_key)
    r, c, quad, dir_ = chosen

    # Convert to 1-indexed row,col
    return f"{r+1},{c+1},{quad},{dir_}"
