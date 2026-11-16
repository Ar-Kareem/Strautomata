
from __future__ import annotations
from typing import List
import sys
import math

# Board dimensions
ROWS, COLS, WIN = 6, 7, 4
MAX_DEPTH = 5  # depth of the minimax search

def policy(board: List[List[int]]) -> int:
    """
    Connect‑4 policy: return the column (0‑6) where the current player (1) will drop a disc.
    Returns the first legal column if none exist (should never happen in a valid game).
    """
    # Find legal columns (non‑full)
    legal_cols = [c for c in range(COLS) if board[ROWS - 1][c] == 0]
    if not legal_cols:
        return legal_cols[0]  # fallback (board should be full)

    # Evaluate each possible move using minimax with alpha‑beta pruning
    best_col = legal_cols[0]
    best_score = -math.inf

    for col in legal_cols:
        new_board = apply_move(board, col, player=1)
        score = minimax(new_board,
                        depth=0,
                        maximizing=False,  # opponent's turn next
                        alpha=-math.inf,
                        beta=math.inf,
                        max_depth=MAX_DEPTH,
                        player=-1)          # opponent's perspective
        if score > best_score:
            best_score = score
            best_col = col
        # If scores are equal we keep the leftmost column (already the first)
    return best_col


def apply_move(board: List[List[int]], col: int, player: int) -> List[List[int]]:
    """Create a new board with the player's disc dropped in the given column."""
    new_board = [row[:] for row in board]  # shallow copy of each row
    # Find the lowest empty row from the bottom
    for row in range(ROWS - 1, -1, -1):
        if new_board[row][col] == 0:
            new_board[row][col] = player
            break
    return new_board


def check_winner(board: List[List[int]], player: int) -> int:
    """Return player if they have a line of WIN discs, otherwise 0."""
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - WIN + 1):
            if sum(board[r][c:c+WIN]) == player * WIN:
                return player
    # Vertical
    for c in range(COLS):
        for r in range(ROWS - WIN + 1):
            if sum(board[r+r_offset][c] for r_offset in range(WIN)) == player * WIN:
                return player
    # Diagonal down‑right (\)
    for r in range(ROWS - WIN + 1):
        for c in range(COLS - WIN + 1):
            if sum(board[r + d][c + d] for d in range(WIN)) == player * WIN:
                return player
    # Diagonal up‑right (/)
    for r in range(WIN - 1, ROWS):
        for c in range(COLS - WIN + 1):
            if sum(board[r - d][c + d] for d in range(WIN)) == player * WIN:
                return player
    return 0


def heuristic(board: List[List[int]], player: int) -> int:
    """Simple heuristic for non‑terminal positions."""
    # Immediate win/loss overrides everything
    if check_winner(board, player) == player:
        return 1000
    if check_winner(board, -player) == -player:
        return -1000

    score = 0

    # Scan every possible line of length WIN
    def evaluate_line(line: List[int]) -> None:
        nonlocal score
        p_cnt = sum(1 for x in line if x == player)
        opp_cnt = sum(1 for x in line if x == -player)
        empty = WIN - p_cnt - opp_cnt

        if p_cnt == WIN:
            score += 1000
        elif opp_cnt == WIN:
            score -= 1000
        elif p_cnt == WIN - 1:
            score += 10
        elif opp_cnt == WIN - 1:
            score -= 10
        elif p_cnt == WIN - 2:
            if empty == 2:
                score += 1
        elif opp_cnt == WIN - 2:
            if empty == 2:
                score -= 1

    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - WIN + 1):
            line = board[r][c:c+WIN]
            evaluate_line(line)

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - WIN + 1):
            line = [board[r + d][c] for d in range(WIN)]
            evaluate_line(line)

    # Diagonal down‑right (\)
    for r in range(ROWS - WIN + 1):
        for c in range(COLS - WIN + 1):
            line = [board[r + d][c + d] for d in range(WIN)]
            evaluate_line(line)

    # Diagonal up‑right (/)
    for r in range(WIN - 1, ROWS):
        for c in range(COLS - WIN + 1):
            line = [board[r - d][c + d] for d in range(WIN)]
            evaluate_line(line)

    return score


def minimax(board: List[List[int]],
           depth: int,
           maximizing: bool,
           alpha: float,
           beta: float,
           max_depth: int,
           player: int) -> int:
    """
    Depth‑limited minimax with α‑β pruning.
    - `maximizing` indicates whether the current side tries to maximize the score.
    - `player` is the side whose turn it is (1 = current, -1 = opponent).
    """
    # No more moves or reached max depth → evaluate position
    if depth == max_depth or not any(board[ROWS - 1][c] == 0 for c in range(COLS)):
        return heuristic(board, player)

    if maximizing:
        value = -math.inf
        for col in range(COLS):
            if board[ROWS - 1][col] != 0:
                continue
            new_board = apply_move(board, col, player)
            value = max(value, minimax(new_board, depth + 1,
                                      maximizing=False,
                                      alpha=alpha, beta=beta,
                                      max_depth=max_depth,
                                      player=-player))
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value
    else:
        value = math.inf
        for col in range(COLS):
            if board[ROWS - 1][col] != 0:
                continue
            new_board = apply_move(board, col, player)
            value = min(value, minimax(new_board, depth + 1,
                                      maximizing=True,
                                      alpha=alpha, beta=beta,
                                      max_depth=max_depth,
                                      player=-player))
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value


# Optional: increase recursion limit for deeper searches (not needed for depth=5)
sys.setrecursionlimit(10000)
