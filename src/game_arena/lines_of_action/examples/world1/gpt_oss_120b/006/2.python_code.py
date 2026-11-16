
import itertools
from collections import deque
from copy import deepcopy

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1),  (1, 0), (1, 1)]

def in_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def count_pieces_line(board, r, c, dr, dc):
    """Count all pieces (both colours) on the infinite line that passes through (r,c)
       in direction (dr,dc), i.e. the whole row/col/diag."""
    cnt = 0
    # go forward
    nr, nc = r + dr, c + dc
    while in_board(nr, nc):
        if board[nr][nc] != 0:
            cnt += 1
        nr += dr
        nc += dc
    # go backward
    nr, nc = r - dr, c - dc
    while in_board(nr, nc):
        if board[nr][nc] != 0:
            cnt += 1
        nr -= dr
        nc -= dc
    # include the piece itself
    cnt += 1
    return cnt

def generate_moves(board):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != 1:  # not our piece
                continue
            for dr, dc in DIRS:
                length = count_pieces_line(board, r, c, dr, dc)
                tr, tc = r + dr * length, c + dc * length
                if not in_board(tr, tc):
                    continue
                if board[tr][tc] == 1:   # cannot land on own piece
                    continue
                # check squares we jump over (exclude destination)
                blocked = False
                for step in range(1, length):
                    ir, ic = r + dr * step, c + dc * step
                    if board[ir][ic] == -1:   # cannot jump over opponent
                        blocked = True
                        break
                if blocked:
                    continue
                # legal move found
                moves.append(((r, c), (tr, tc)))
    return moves

def apply_move(board, frm, to):
    nb = deepcopy(board)
    fr, fc = frm
    tr, tc = to
    nb[fr][fc] = 0
    nb[tr][tc] = 1            # capture handled by overwriting opponent
    return nb

def components_and_distance(board):
    """Return (num_components, total_manhattan_distance_to_centroid) for our pieces."""
    # collect our pieces
    pieces = [(r, c) for r in range(8) for c in range(8) if board[r][c] == 1]
    if not pieces:
        return 0, 0
    # connectivity (8‑direction)
    visited = set()
    comps = 0
    for p in pieces:
        if p in visited:
            continue
        comps += 1
        q = deque([p])
        visited.add(p)
        while q:
            cr, cc = q.popleft()
            for dr, dc in DIRS:
                nr, nc = cr + dr, cc + dc
                if in_board(nr, nc) and board[nr][nc] == 1 and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
    # centroid
    avg_r = sum(r for r, _ in pieces) / len(pieces)
    avg_c = sum(c for _, c in pieces) / len(pieces)
    total_dist = sum(abs(r - avg_r) + abs(c - avg_c) for r, c in pieces)
    return comps, total_dist

def heuristic(board):
    comps, dist = components_and_distance(board)
    # heavily weight component count
    return comps * 1000 + dist

def policy(board) -> str:
    """
    Returns a legal LoA move for the player (encoded as 1) in the form
    "from_row,from_col:to_row,to_col".
    """
    moves = generate_moves(board)
    if not moves:  # safety fallback – move first piece north if possible
        for r in range(8):
            for c in range(8):
                if board[r][c] == 1 and r > 0 and board[r-1][c] != 1:
                    return f"{r},{c}:{r-1},{c}"
        # should never reach here
        raise RuntimeError("No legal move found")
    best_move = None
    best_score = float('inf')
    for frm, to in moves:
        new_board = apply_move(board, frm, to)
        score = heuristic(new_board)
        if score < best_score:
            best_score = score
            best_move = (frm, to)
    fr, fc = best_move[0]
    tr, tc = best_move[1]
    return f"{fr},{fc}:{tr},{tc}"
