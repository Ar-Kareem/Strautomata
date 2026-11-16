
import time
import heapq
from typing import List, Tuple, Optional

# ---------------------------
# Pentago policy (6x6 standard)
# ---------------------------

INF = 10**9

# Quadrant index lists (flat 0..35, row-major)
QUAD_IDXS = [
    [0, 1, 2, 6, 7, 8, 12, 13, 14],      # 0 top-left
    [3, 4, 5, 9, 10, 11, 15, 16, 17],    # 1 top-right
    [18, 19, 20, 24, 25, 26, 30, 31, 32],# 2 bottom-left
    [21, 22, 23, 27, 28, 29, 33, 34, 35] # 3 bottom-right
]

# Rotation permutations for the 3x3 quadrant values in the QUAD_IDXS order:
# q = [a,b,c,d,e,f,g,h,i]
# R => [g,d,a,h,e,b,i,f,c]  indices [6,3,0,7,4,1,8,5,2]
# L => [c,f,i,b,e,h,a,d,g]  indices [2,5,8,1,4,7,0,3,6]
ROT_PERM = {
    "R": [6, 3, 0, 7, 4, 1, 8, 5, 2],
    "L": [2, 5, 8, 1, 4, 7, 0, 3, 6],
}

# Precompute all 5-cell "windows" in all directions on 6x6
WINDOWS_5: List[Tuple[int, int, int, int, int]] = []
for r in range(6):
    for c in range(6):
        if c + 4 < 6:  # horiz
            WINDOWS_5.append(tuple((r * 6 + (c + i)) for i in range(5)))
        if r + 4 < 6:  # vert
            WINDOWS_5.append(tuple(((r + i) * 6 + c) for i in range(5)))
        if r + 4 < 6 and c + 4 < 6:  # diag down-right
            WINDOWS_5.append(tuple(((r + i) * 6 + (c + i)) for i in range(5)))
        if r + 4 < 6 and c - 4 >= 0:  # diag down-left
            WINDOWS_5.append(tuple(((r + i) * 6 + (c - i)) for i in range(5)))

# Position weights (favor center); small compared to line threats
POS_W = [0] * 36
for r in range(6):
    for c in range(6):
        # Manhattan distance to nearest center among (2,2),(2,3),(3,2),(3,3) in 0-index
        d = min(abs(r - 2) + abs(c - 2), abs(r - 2) + abs(c - 3),
                abs(r - 3) + abs(c - 2), abs(r - 3) + abs(c - 3))
        # closer => higher
        POS_W[r * 6 + c] = 6 - d  # ranges roughly 2..6

# Threat weights for (1..5) in a 5-window, only when the other player has 0 in that window
# Calibrated so 4-in-row threats matter a lot.
TH_W = [0, 2, 10, 60, 400, 200000]

# Neighbor lists within Chebyshev distance 2 for candidate move filtering
NEIGH2: List[List[int]] = []
for r in range(6):
    for c in range(6):
        idx = r * 6 + c
        neigh = []
        for rr in range(max(0, r - 2), min(6, r + 3)):
            for cc in range(max(0, c - 2), min(6, c + 3)):
                if rr == r and cc == c:
                    continue
                neigh.append(rr * 6 + cc)
        NEIGH2.append(neigh)


def _to_flat_board(you, opponent) -> List[int]:
    """Convert two 6x6 0/1 arrays into a flat int board: 1 (us), -1 (opp), 0 empty."""
    b = [0] * 36
    for r in range(6):
        yr = you[r]
        orr = opponent[r]
        base = r * 6
        for c in range(6):
            if int(yr[c]) == 1:
                b[base + c] = 1
            elif int(orr[c]) == 1:
                b[base + c] = -1
    return b


def _apply_move(board: List[int], pos: int, quad: int, rot_dir: str, player: int) -> List[int]:
    """Place 'player' at pos, then rotate quadrant quad in direction rot_dir ('L'/'R')."""
    b = board[:]  # 36 copy
    b[pos] = player
    idxs = QUAD_IDXS[quad]
    vals = [b[i] for i in idxs]
    perm = ROT_PERM[rot_dir]
    new_vals = [vals[j] for j in perm]
    for k, i in enumerate(idxs):
        b[i] = new_vals[k]
    return b


def _check_winner(board: List[int]) -> Tuple[bool, bool]:
    """Return (us_win, opp_win) after the current position."""
    us = False
    opp = False
    for w in WINDOWS_5:
        s = board[w[0]] + board[w[1]] + board[w[2]] + board[w[3]] + board[w[4]]
        if s == 5:
            us = True
            if opp:
                return True, True
        elif s == -5:
            opp = True
            if us:
                return True, True
    return us, opp


def _evaluate(board: List[int]) -> int:
    """Heuristic evaluation from our perspective."""
    us_win, opp_win = _check_winner(board)
    if us_win and opp_win:
        return 0
    if us_win:
        return INF // 2
    if opp_win:
        return -INF // 2

    score = 0

    # Positional
    # board[i] is 1 for us, -1 for opp -> naturally antisymmetric
    for i, v in enumerate(board):
        if v:
            score += POS_W[i] * v

    # Threat windows
    # Only score "clean" windows (not mixed), and weight opponent threats slightly higher (defense).
    for w in WINDOWS_5:
        a = board[w[0]]
        b = board[w[1]]
        c = board[w[2]]
        d = board[w[3]]
        e = board[w[4]]
        us_cnt = (a == 1) + (b == 1) + (c == 1) + (d == 1) + (e == 1)
        opp_cnt = (a == -1) + (b == -1) + (c == -1) + (d == -1) + (e == -1)
        if opp_cnt == 0 and us_cnt > 0:
            score += TH_W[us_cnt]
        elif us_cnt == 0 and opp_cnt > 0:
            # slightly stronger penalty to prioritize blocks
            score -= int(1.15 * TH_W[opp_cnt])

    return score


def _empty_positions(board: List[int]) -> List[int]:
    return [i for i, v in enumerate(board) if v == 0]


def _candidate_positions(board: List[int]) -> List[int]:
    empties = _empty_positions(board)
    occ = [i for i, v in enumerate(board) if v != 0]
    if not occ:
        return empties

    # If very early, don't over-filter
    if len(occ) <= 2:
        return empties

    cand = []
    for e in empties:
        # near any occupied within Chebyshev dist 2
        neigh = NEIGH2[e]
        for n in neigh:
            if board[n] != 0:
                cand.append(e)
                break
    return cand if cand else empties


def _gen_moves_ordered(
    board: List[int],
    player: int,
    depth: int,
    beam: int,
    start_time: float,
    time_limit: float
) -> List[Tuple[int, int, str]]:
    """Generate moves ordered for alpha-beta; return list of (pos, quad, dir)."""

    # Candidate positions first
    positions = _candidate_positions(board)

    # If time is very tight, reduce positions by positional preference
    if (time.time() - start_time) > time_limit * 0.85 and len(positions) > 10:
        positions.sort(key=lambda p: POS_W[p], reverse=True)
        positions = positions[:10]

    scored = []
    # Score by a quick 1-ply evaluation after applying move (good ordering)
    for pos in positions:
        if board[pos] != 0:
            continue
        for quad in range(4):
            for rot_dir in ("L", "R"):
                nb = _apply_move(board, pos, quad, rot_dir, player)
                # For ordering, store eval from our perspective.
                h = _evaluate(nb)
                scored.append((h, pos, quad, rot_dir))

    if not scored:
        return []

    # For us (player=1): higher eval first. For opponent: lower eval first.
    if player == 1:
        top = heapq.nlargest(beam, scored, key=lambda x: x[0])
        return [(pos, quad, rot_dir) for (_h, pos, quad, rot_dir) in top]
    else:
        top = heapq.nsmallest(beam, scored, key=lambda x: x[0])
        return [(pos, quad, rot_dir) for (_h, pos, quad, rot_dir) in top]


def _negamax(
    board: List[int],
    depth: int,
    alpha: int,
    beta: int,
    player: int,
    start_time: float,
    time_limit: float
) -> int:
    if time.time() - start_time > time_limit:
        return _evaluate(board)

    us_win, opp_win = _check_winner(board)
    if us_win or opp_win:
        # terminal
        if us_win and opp_win:
            return 0
        if us_win:
            return INF // 2
        return -INF // 2

    if depth == 0:
        return _evaluate(board)

    # Beam size by depth to control branching
    if depth >= 3:
        beam = 32
    elif depth == 2:
        beam = 24
    else:
        beam = 40

    moves = _gen_moves_ordered(board, player, depth, beam, start_time, time_limit)
    if not moves:
        return _evaluate(board)

    best = -INF
    for pos, quad, rot_dir in moves:
        if time.time() - start_time > time_limit:
            break
        nb = _apply_move(board, pos, quad, rot_dir, player)
        score = -_negamax(nb, depth - 1, -beta, -alpha, -player, start_time, time_limit)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def _format_move(pos: int, quad: int, rot_dir: str) -> str:
    r = pos // 6 + 1
    c = pos % 6 + 1
    return f"{r},{c},{quad},{rot_dir}"


def policy(you, opponent) -> str:
    board = _to_flat_board(you, opponent)

    # Always ensure we can return something legal
    empties = _empty_positions(board)
    if not empties:
        # Should not happen per prompt; fallback legal-ish format anyway.
        return "1,1,0,L"

    start_time = time.time()
    time_limit = 0.92  # stay safely under 1s

    # 1) Immediate win finder (tactical)
    # Check all moves but using candidate positions first for speed.
    cand_pos = _candidate_positions(board)
    # In case candidate filter misses a win (rare), expand if early.
    if len(cand_pos) < len(empties) and sum(1 for v in board if v != 0) <= 4:
        cand_pos = empties

    best_fallback_move = (empties[0], 0, "L")

    # Prefer center-ish as fallback
    empties_sorted = sorted(empties, key=lambda p: POS_W[p], reverse=True)
    best_fallback_move = (empties_sorted[0], 0, "L")

    for pos in cand_pos:
        if board[pos] != 0:
            continue
        for quad in range(4):
            for rot_dir in ("L", "R"):
                nb = _apply_move(board, pos, quad, rot_dir, 1)
                us_win, opp_win = _check_winner(nb)
                if us_win and not opp_win:
                    return _format_move(pos, quad, rot_dir)
                # Keep a reasonable fallback if time is tight
                if time.time() - start_time > time_limit * 0.6:
                    break

    # 2) Iterative deepening minimax (depth 2 then 3 if time allows)
    best_move: Optional[Tuple[int, int, str]] = None
    best_score = -INF

    for depth in (2, 3):
        if time.time() - start_time > time_limit * 0.78:
            break

        # Root move ordering
        beam_root = 40 if depth == 2 else 36
        root_moves = _gen_moves_ordered(board, 1, depth, beam_root, start_time, time_limit)
        if not root_moves:
            break

        local_best_move = root_moves[0]
        local_best_score = -INF

        alpha = -INF
        beta = INF

        for pos, quad, rot_dir in root_moves:
            if time.time() - start_time > time_limit:
                break
            if board[pos] != 0:
                continue
            nb = _apply_move(board, pos, quad, rot_dir, 1)

            us_win, opp_win = _check_winner(nb)
            if us_win and not opp_win:
                return _format_move(pos, quad, rot_dir)

            score = -_negamax(nb, depth - 1, -beta, -alpha, -1, start_time, time_limit)

            if score > local_best_score:
                local_best_score = score
                local_best_move = (pos, quad, rot_dir)

            if score > alpha:
                alpha = score

        # Accept deeper result if computed
        if local_best_score > best_score or best_move is None:
            best_score = local_best_score
            best_move = local_best_move

    # 3) If search failed/timed out, pick a safe legal move
    if best_move is None:
        pos, quad, rot_dir = best_fallback_move
        # Ensure chosen pos empty; otherwise first empty.
        if board[pos] != 0:
            pos = empties[0]
        return _format_move(pos, quad, rot_dir)

    pos, quad, rot_dir = best_move
    if board[pos] != 0:
        # Safety fallback
        pos = empties_sorted[0]
        if board[pos] != 0:
            pos = empties[0]
        quad, rot_dir = 0, "L"
    return _format_move(pos, quad, rot_dir)
