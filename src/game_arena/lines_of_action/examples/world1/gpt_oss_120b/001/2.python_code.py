
import copy
from collections import deque
from typing import List, Tuple

# 8 possible directions (row change, column change)
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1),  (1, 0), (1, 1)]

def inside(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8

def count_pieces_on_line(board: List[List[int]], r: int, c: int, dr: int, dc: int) -> int:
    """Count both colours on the whole line defined by (dr, dc) passing through (r,c)."""
    cnt = 0
    # forward
    nr, nc = r + dr, c + dc
    while inside(nr, nc):
        if board[nr][nc] != 0:
            cnt += 1
        nr += dr
        nc += dc
    # backward
    nr, nc = r - dr, c - dc
    while inside(nr, nc):
        if board[nr][nc] != 0:
            cnt += 1
        nr -= dr
        nc -= dc
    # include the piece itself
    cnt += 1
    return cnt

def legal_moves(board: List[List[int]]) -> List[Tuple[int, int, int, int, bool]]:
    """Return all legal moves for player 1.
    Each move is (r0, c0, r1, c1, captured) where captured is True if an opponent piece is taken."""
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != 1:
                continue
            for dr, dc in DIRS:
                distance = count_pieces_on_line(board, r, c, dr, dc)
                nr, nc = r + dr * distance, c + dc * distance
                if not inside(nr, nc):
                    continue
                # destination occupied by own piece -> illegal
                if board[nr][nc] == 1:
                    continue
                # cannot jump over opponent pieces
                blocked = False
                for step in range(1, distance):
                    tr, tc = r + dr * step, c + dc * step
                    if board[tr][tc] == -1:
                        blocked = True
                        break
                if blocked:
                    continue
                captured = board[nr][nc] == -1
                moves.append((r, c, nr, nc, captured))
    return moves

def connected_components(board: List[List[int]]) -> int:
    """Count the number of 8‑way connected components of our pieces (value 1)."""
    visited = [[False]*8 for _ in range(8)]
    comp = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1 and not visited[r][c]:
                comp += 1
                dq = deque()
                dq.append((r,c))
                visited[r][c] = True
                while dq:
                    cr, cc = dq.popleft()
                    for dr, dc in DIRS:
                        nr, nc = cr + dr, cc + dc
                        if inside(nr, nc) and board[nr][nc] == 1 and not visited[nr][nc]:
                            visited[nr][nc] = True
                            dq.append((nr, nc))
    return comp

def spread_measure(board: List[List[int]]) -> float:
    """Return a simple spread metric – sum of Manhattan distances to the centroid."""
    pieces = [(r, c) for r in range(8) for c in range(8) if board[r][c] == 1]
    if not pieces:
        return 0.0
    avg_r = sum(p[0] for p in pieces) / len(pieces)
    avg_c = sum(p[1] for p in pieces) / len(pieces)
    total = sum(abs(p[0] - avg_r) + abs(p[1] - avg_c) for p in pieces)
    return total

def evaluate(board: List[List[int]], captured: bool) -> float:
    """Heuristic score for a board position after our move."""
    comps = connected_components(board)
    spread = spread_measure(board)
    score = -1000 * comps - spread
    if captured:
        score += 500
    return score

def apply_move(board: List[List[int]], move: Tuple[int, int, int, int, bool]) -> List[List[int]]:
    r0, c0, r1, c1, _ = move
    new_board = copy.deepcopy(board)
    new_board[r0][c0] = 0
    new_board[r1][c1] = 1
    return new_board

def policy(board: List[List[int]]) -> str:
    """Select the best legal move for the current player (value 1)."""
    moves = legal_moves(board)
    if not moves:
        raise ValueError("No legal moves available")

    best_score = -float('inf')
    best_move = moves[0]

    for mv in moves:
        after = apply_move(board, mv)
        sc = evaluate(after, mv[4])
        if sc > best_score:
            best_score = sc
            best_move = mv

    r0, c0, r1, c1, _ = best_move
    return f"{r0},{c0}:{r1},{c1}"
