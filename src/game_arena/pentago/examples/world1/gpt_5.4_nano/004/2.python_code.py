
import numpy as np
from itertools import product

# ----------------- Helpers: Board / Move mechanics -----------------

def _get_board(you, opponent):
    you = np.array(you, dtype=np.int8)
    opponent = np.array(opponent, dtype=np.int8)
    board = np.zeros((6, 6), dtype=np.int8)
    board[you == 1] = 1
    board[opponent == 1] = -1
    return board

def _rotate_quadrant(board, quad, dir):
    # quad mapping to ranges: each quadrant is 3x3
    r0 = 0 if quad < 2 else 3
    c0 = 0 if quad in (0, 2) else 3
    sub = board[r0:r0+3, c0:c0+3].copy()
    if dir == 'L':
        # anticlockwise: transpose then flip left-right
        sub = np.rot90(sub, 1)
    else:  # 'R'
        sub = np.rot90(sub, -1)
    out = board.copy()
    out[r0:r0+3, c0:c0+3] = sub
    return out

def _apply_move(board, r, c, quad, dir_char):
    # place at (r,c) (0-index) for current player (assumed you)
    out = board.copy()
    out[r, c] = 1
    out = _rotate_quadrant(out, quad, dir_char)
    return out

def _has_five(board, player):
    # player = 1 for you, -1 for opponent
    # Check all lines: horizontal, vertical, diag down-right, diag down-left
    b = (board == player).astype(np.int8)

    # horizontal
    for i in range(6):
        for j in range(6 - 4):
            if b[i, j:j+5].sum() == 5 and b[i, j:j+5].all():
                return True
    # vertical
    for j in range(6):
        for i in range(6 - 4):
            if b[i:i+5, j].sum() == 5 and b[i:i+5, j].all():
                return True

    # diag down-right
    for i in range(6 - 4):
        for j in range(6 - 4):
            if all(b[i+k, j+k] for k in range(5)):
                return True
    # diag down-left
    for i in range(6 - 4):
        for j in range(4, 6):
            if all(b[i+k, j-k] for k in range(5)):
                return True
    return False

def _count_fives_in_any_line(board, player):
    # Count sequences of length 5 that are fully player-filled (only exact 5-window),
    # used for tie-breaking. Also detect >=5 by existence.
    b = (board == player).astype(np.int8)
    cnt = 0
    # horizontal
    for i in range(6):
        for j in range(6 - 4):
            if b[i, j:j+5].sum() == 5:
                cnt += 1
    # vertical
    for j in range(6):
        for i in range(6 - 4):
            if b[i:i+5, j].sum() == 5:
                cnt += 1
    # diag down-right
    for i in range(6 - 4):
        for j in range(6 - 4):
            if sum(b[i+k, j+k] for k in range(5)) == 5:
                cnt += 1
    # diag down-left
    for i in range(6 - 4):
        for j in range(4, 6):
            if sum(b[i+k, j-k] for k in range(5)) == 5:
                cnt += 1
    return cnt

def _legal_moves(board):
    # Generate all legal moves for current player (place on empty then rotate one quadrant)
    empties = np.argwhere(board == 0)
    moves = []
    for r, c in empties:
        for quad in range(4):
            for dir_char in ('L', 'R'):
                moves.append((int(r), int(c), quad, dir_char))
    return moves

# ----------------- Heuristic evaluation -----------------

# Precompute all 5-length windows
WINDOWS = []
# horizontal
for i in range(6):
    for j in range(6 - 4):
        WINDOWS.append([(i, j+k) for k in range(5)])
# vertical
for j in range(6):
    for i in range(6 - 4):
        WINDOWS.append([(i+k, j) for k in range(5)])
# diag down-right
for i in range(6 - 4):
    for j in range(6 - 4):
        WINDOWS.append([(i+k, j+k) for k in range(5)])
# diag down-left
for i in range(6 - 4):
    for j in range(4, 6):
        WINDOWS.append([(i+k, j-k) for k in range(5)])

def _line_potential_score(board, player):
    # For each 5-window, score based on how many player's marbles and no opponent marbles present
    opp = -player
    total = 0.0
    b = board
    for win in WINDOWS:
        vals = [b[r, c] for r, c in win]
        if opp in vals:
            continue
        cnt = vals.count(player)
        # cnt can be 1..5
        if cnt == 0:
            continue
        # Strongly reward 5, then 4, then 3; slight for 1-2
        if cnt == 5:
            total += 100000.0
        elif cnt == 4:
            total += 4000.0
        elif cnt == 3:
            total += 450.0
        elif cnt == 2:
            total += 60.0
        elif cnt == 1:
            total += 10.0
    return total

def _board_central_bonus(board, player):
    # Prefer center-ish placements and keep your pieces closer to center
    # Center coordinates (2.5,2.5) weighted
    coords = np.argwhere(board == player)
    if coords.size == 0:
        return 0.0
    bonus = 0.0
    for r, c in coords:
        dr = abs(r - 2.5)
        dc = abs(c - 2.5)
        bonus += (3.0 - (dr + dc))  # higher when closer to center
    return bonus * 3.0

def _evaluate(board):
    # Higher is better for you (player = 1)
    you_score = _line_potential_score(board, 1) + _board_central_bonus(board, 1)
    opp_score = _line_potential_score(board, -1) + _board_central_bonus(board, -1)
    return you_score - 1.05 * opp_score

# ----------------- Policy: tactical 1-ply win + defensive block + heuristic -----------------

def policy(you, opponent) -> str:
    board = _get_board(you, opponent)
    moves = _legal_moves(board)

    # 1) Immediate winning move
    for r, c, quad, d in moves:
        nb = _apply_move(board, r, c, quad, d)
        if _has_five(nb, 1):
            return f"{r+1},{c+1},{quad},{d}"

    # 2) Prevent opponent immediate win:
    # If after our move, opponent has ANY winning move, block it.
    # We'll compute the best defensive candidate by checking opponent's possible replies.
    best_move = None
    best_val = -1e18

    # Precompute opponent moves for each resulting position on the fly (fast enough with pruning).
    for r, c, quad, d in moves:
        nb = _apply_move(board, r, c, quad, d)

        # If we allow opponent to win immediately, heavily penalize.
        opp_can_win = False
        # Generate opponent legal moves: opponent places - not represented as separate state;
        # after our move, opponent's placement is any empty cell and rotation.
        empties = np.argwhere(nb == 0)
        for (er, ec) in empties:
            for q2 in range(4):
                for d2 in ('L', 'R'):
                    nb2 = nb.copy()
                    nb2[er, ec] = -1
                    nb2 = _rotate_quadrant(nb2, q2, d2)
                    if _has_five(nb2, -1):
                        opp_can_win = True
                        break
                if opp_can_win:
                    break
            if opp_can_win:
                break

        if opp_can_win:
            val = -1e12  # essentially avoid losing moves
        else:
            # 3) Evaluate position heuristically
            val = _evaluate(nb)

            # Bonus if we create multiple near-wins (count 5-windows not necessary but helps)
            val += 2.0 * _count_fives_in_any_line(nb, 1)

            # Mildly prefer moves that also deny opponent potential
            val -= 0.15 * _line_potential_score(nb, -1)

        # Choose best; if equal, keep deterministic ordering by tuple string sort later
        if val > best_val:
            best_val = val
            best_move = (r, c, quad, d)

    # Fallback (should not happen): pick first legal move
    if best_move is None:
        r, c, quad, d = moves[0]
    else:
        r, c, quad, d = best_move

    return f"{r+1},{c+1},{quad},{d}"
