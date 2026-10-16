
import time
import math
from collections import deque

# Directions: 8-neighborhood
DIRS8 = [(-1, -1), (-1, 0), (-1, 1),
         (0, -1),           (0, 1),
         (1, -1),  (1, 0),  (1, 1)]


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def format_move(mv):
    fr, fc, tr, tc = mv
    return f"{fr},{fc}:{tr},{tc}"


def get_pieces(board, player):
    ps = []
    for r in range(8):
        row = board[r]
        for c in range(8):
            if row[c] == player:
                ps.append((r, c))
    return ps


def line_piece_count(board, r, c, dr, dc):
    """
    Count ALL pieces (both colors) on the full line passing through (r,c)
    in direction (dr,dc), i.e., the LOA movement-distance count.
    """
    # Go to one end of the line
    rr, cc = r, c
    while in_bounds(rr - dr, cc - dc):
        rr -= dr
        cc -= dc

    cnt = 0
    # Traverse to the other end
    while in_bounds(rr, cc):
        if board[rr][cc] != 0:
            cnt += 1
        rr += dr
        cc += dc
    return cnt


def is_legal_move(board, player, fr, fc, tr, tc):
    if not in_bounds(fr, fc) or not in_bounds(tr, tc):
        return False
    if board[fr][fc] != player:
        return False
    if board[tr][tc] == player:
        return False

    dr = tr - fr
    dc = tc - fc

    # Must be straight or diagonal
    if dr == 0 and dc == 0:
        return False
    if dr != 0 and dc != 0 and abs(dr) != abs(dc):
        return False

    sdr = 0 if dr == 0 else (1 if dr > 0 else -1)
    sdc = 0 if dc == 0 else (1 if dc > 0 else -1)

    dist = max(abs(dr), abs(dc))
    needed = line_piece_count(board, fr, fc, sdr, sdc)
    if dist != needed:
        return False

    # Path squares: cannot jump over enemy pieces; friendly pieces are allowed
    rr, cc = fr + sdr, fc + sdc
    while (rr, cc) != (tr, tc):
        if board[rr][cc] == -player:
            return False
        rr += sdr
        cc += sdc

    # Destination can be empty or enemy (capture)
    return True


def legal_moves(board, player):
    moves = []
    for fr, fc in get_pieces(board, player):
        for dr, dc in DIRS8:
            cnt = line_piece_count(board, fr, fc, dr, dc)
            tr = fr + dr * cnt
            tc = fc + dc * cnt
            if not in_bounds(tr, tc):
                continue
            if board[tr][tc] == player:
                continue
            if is_legal_move(board, player, fr, fc, tr, tc):
                moves.append((fr, fc, tr, tc))
    return moves


def apply_move(board, mv, player):
    fr, fc, tr, tc = mv
    nb = [row[:] for row in board]
    nb[fr][fc] = 0
    nb[tr][tc] = player  # overwrites enemy if capture
    return nb


def component_sizes(board, player):
    seen = [[False] * 8 for _ in range(8)]
    sizes = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != player or seen[r][c]:
                continue
            q = deque()
            q.append((r, c))
            seen[r][c] = True
            sz = 0
            while q:
                rr, cc = q.popleft()
                sz += 1
                for dr, dc in DIRS8:
                    nr, nc = rr + dr, cc + dc
                    if in_bounds(nr, nc) and not seen[nr][nc] and board[nr][nc] == player:
                        seen[nr][nc] = True
                        q.append((nr, nc))
            sizes.append(sz)
    return sizes


def is_connected(board, player):
    sizes = component_sizes(board, player)
    if not sizes:
        return False
    return len(sizes) == 1


def dispersion(board, player):
    ps = get_pieces(board, player)
    n = len(ps)
    if n <= 1:
        return 0.0
    mr = sum(r for r, _ in ps) / n
    mc = sum(c for _, c in ps) / n
    # Chebyshev distance to centroid (encourages clumping in 8-connectivity sense)
    return sum(max(abs(r - mr), abs(c - mc)) for r, c in ps)


def eval_board(board):
    """
    Higher is better for player=1 (the current policy's player).
    """
    own_sizes = component_sizes(board, 1)
    opp_sizes = component_sizes(board, -1)

    if own_sizes and len(own_sizes) == 1:
        return 1e9
    if opp_sizes and len(opp_sizes) == 1:
        return -1e9

    own_n = sum(own_sizes)
    opp_n = sum(opp_sizes)

    own_comp = len(own_sizes) if own_sizes else 99
    opp_comp = len(opp_sizes) if opp_sizes else 99

    own_big = max(own_sizes) if own_sizes else 0
    opp_big = max(opp_sizes) if opp_sizes else 0

    own_disp = dispersion(board, 1)
    opp_disp = dispersion(board, -1)

    # Core: component differential dominates
    score = 0.0
    score += 220.0 * (opp_comp - own_comp)

    # Encourage having a large main cluster (and opponent not)
    if own_n > 0:
        score += 80.0 * (own_big / own_n)
    if opp_n > 0:
        score -= 80.0 * (opp_big / opp_n)

    # Encourage clumping / discourage opponent clumping
    score += 2.5 * (opp_disp - own_disp)

    return score


def move_order_heuristic(board, mv, player):
    """
    Cheap ordering: captures first, and moves toward own centroid.
    """
    fr, fc, tr, tc = mv
    cap = 1 if board[tr][tc] == -player else 0

    ps = get_pieces(board, player)
    if ps:
        mr = sum(r for r, _ in ps) / len(ps)
        mc = sum(c for _, c in ps) / len(ps)
        before = max(abs(fr - mr), abs(fc - mc))
        after = max(abs(tr - mr), abs(tc - mc))
        toward = before - after
    else:
        toward = 0.0

    # Captures are valuable, but not at the expense of connectivity goals (handled in eval)
    return 10.0 * cap + 1.5 * toward


def policy(board) -> str:
    """
    Returns a legal move string: "from_row,from_col:to_row,to_col"
    Assumes board is an 8x8 grid of ints: 0 empty, 1 us, -1 opponent.
    """
    start = time.time()
    time_limit = 0.95  # seconds

    # Ensure we can index quickly
    b = [list(row) for row in board]

    moves = legal_moves(b, 1)
    if not moves:
        # Extremely unlikely in valid LOA positions; fallback (may be illegal if truly none).
        return "0,0:0,0"

    # If any immediate winning move exists, play it
    # (Do quick check with ordered candidates first.)
    moves.sort(key=lambda mv: move_order_heuristic(b, mv, 1), reverse=True)

    # Limit branching for speed; expand if few moves.
    K = 24 if len(moves) > 24 else len(moves)
    top_moves = moves[:K]

    best_mv = top_moves[0]
    best_score = -1e18

    alpha = -1e18

    for mv in top_moves:
        if time.time() - start > time_limit:
            break

        b1 = apply_move(b, mv, 1)

        if is_connected(b1, 1):
            return format_move(mv)

        opp_moves = legal_moves(b1, -1)
        if not opp_moves:
            # If opponent has no legal moves, treat as very good.
            score = eval_board(b1) + 1e6
        else:
            # Order opponent replies: they try to minimize our eval.
            opp_moves.sort(key=lambda om: move_order_heuristic(b1, om, -1), reverse=True)
            K2 = 14 if len(opp_moves) > 14 else len(opp_moves)
            opp_moves = opp_moves[:K2]

            worst = 1e18
            beta = 1e18

            for om in opp_moves:
                if time.time() - start > time_limit:
                    break
                b2 = apply_move(b1, om, -1)
                sc = eval_board(b2)
                if sc < worst:
                    worst = sc
                if worst < beta:
                    beta = worst
                if beta <= alpha:
                    break

            score = worst

        if score > best_score:
            best_score = score
            best_mv = mv
            if score > alpha:
                alpha = score

    # Safety: best_mv is always from legal move list.
    return format_move(best_mv)
