
#!/usr/bin/env python3
import sys
from typing import List, Tuple

# Increase recursion limit for safe depth‑limited search
sys.setrecursionlimit(10000)

# -------------------------------------------------
# Helper functions
# -------------------------------------------------
def legal_moves(board: List[List[int]]) -> List[int]:
    """Return all column indices that are not full."""
    return [c for c in range(7) if board[5][c] == 0]

def simulate(board: List[List[int]], col: int, player: int) -> List[List[int]]:
    """Return a new board after dropping `player` (1 or -1) into `col`."""
    new_board = [row[:] for row in board]
    for r in range(5, -1, -1):       # start from bottom row (5)
        if new_board[r][col] == 0:
            new_board[r][col] = player
            break
    return new_board

def has_win(board: List[List[int]]) -> bool:
    """Detect a win for player 1 (the current player)."""
    for r in range(6):
        for c in range(7):
            if board[r][c] != 1:
                continue
            # Horizontal
            if c <= 3 and all(board[r][c + i] == 1 for i in range(4)):
                return True
            # Vertical
            if r <= 2 and all(board[r + i][c] == 1 for i in range(4)):
                return True
            # Diagonal down‑right (NW‑SE)
            if r <= 2 and c <= 3 and all(board[r + i][c + i] == 1 for i in range(4)):
                return True
            # Diagonal down‑left (NE‑SW)
            if r <= 2 and c >= 3 and all(board[r + i][c - i] == 1 for i in range(4)):
                return True
    return False

def find_winning_move(board: List[List[int]]) -> int:
    """Return a column that gives an immediate win, or None."""
    for col in legal_moves(board):
        nb = simulate(board, col, 1)
        if has_win(nb):
            return col
    return None

def find_block_move(board: List[List[int]]) -> int:
    """Return a column that blocks an opponent immediate win, or None."""
    for col in legal_moves(board):
        nb = simulate(board, col, -1)
        if has_win(nb):
            return col
    return None

def run_bonus(board: List[List[int]], player: int) -> int:
    """Count bonus points for runs of at least two `player` discs."""
    bonus = 0
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        for r in range(6):
            for c in range(7):
                # start a run only if previous cell is not the same player
                if dr < 0 or dc < 0:
                    prev_r, prev_c = r - dr, c - dc
                else:
                    prev_r, prev_c = r - dr, c - dc
                if not (0 <= prev_r < 6 and 0 <= prev_c < 7) or board[prev_r][prev_c] != player:
                    run_len = 1
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < 6 and 0 <= nc < 7 and board[nr][nc] == player:
                        run_len += 1
                        nr += dr
                        nc += dc
                    if run_len >= 2:
                        bonus += (run_len - 1) * 5
    return bonus

def evaluate(board: List[List[int]]) -> int:
    """Simple heuristic score based on disc values and line bonuses."""
    # Disc weight: central columns are slightly more valuable
    weights = [10, 10, 12, 12, 12, 10, 10]
    score = 0
    for row in board:
        for col_idx, val in enumerate(row):
            if val == 1:
                score += weights[col_idx]
            elif val == -1:
                score -= weights[col_idx]

    # Positive bonus for our own runs, negative for opponent runs (double weight)
    score += run_bonus(board, 1) * 2
    score -= run_bonus(board, -1) * 2
    return score

# -------------------------------------------------
# Search utilities
# -------------------------------------------------
def max_search_depth(board: List[List[int]]) -> int:
    """Maximum depth we can afford for alpha‑beta (capped at 6)."""
    empty = sum(cell == 0 for row in board for cell in row)
    return min(empty, 6)

def minimax_alpha_beta(board: List[List[int]], depth: int, player: int,
                       alpha: float, beta: float) -> int:
    """Depth‑limited minimax with α‑β pruning.
       Returns the best score for `player` (1 for us, -1 for opponent)."""
    if depth == 0:
        return evaluate(board)

    # Immediate win detection simplifies huge scores
    if has_win(board):
        return float('inf') if player == 1 else -float('inf')

    best = -float('inf')
    moves = legal_moves(board)
    for col in moves:
        new_board = simulate(board, col, player)
        if has_win(new_board):
            cur = float('inf') if player == 1 else -float('inf')
        else:
            cur = -minimax_alpha_beta(new_board, depth - 1, -player,
                                      -beta, -alpha)

        if cur > best:
            best = cur
        if best >= beta:
            break          # prune
        if best > alpha:
            alpha = best

    return best

def best_move_alpha_beta(board: List[List[int]], depth: int) -> int:
    """Select the column with the highest minimax value at the given depth."""
    alpha = -float('inf')
    beta  = float('inf')
    moves = legal_moves(board)
    best_score = -float('inf')
    best_col = None
    best_scores = []            # store columns that achieve best_score

    for col in moves:
        new_board = simulate(board, col, 1)
        # Immediate win wins instantly
        if has_win(new_board):
            score = float('inf')
        else:
            score = -minimax_alpha_beta(new_board, depth - 1, -1,
                                        -beta, -alpha)

        # Update global best
        if score > best_score:
            best_score = score
            best_scores = [col]
        elif score == best_score:
            best_scores.append(col)

    # Tie‑break: prefer column with deepest open slot (more future moves)
    if not best_scores:
        # fallback – first legal column
        return moves[0]

    # Compute “open height” (how many rows are still empty from the bottom up)
    def open_height(col: int) -> int:
        h = 0
        for r in range(5, -1, -1):
            if board[r][col] == 0:
                h += 1
            else:
                break
        return h

    best_col = best_scores[0]
    for cand in best_scores:
        if open_height(cand) > open_height(best_col):
            best_col = cand
        elif open_height(cand) == open_height(best_col):
            # secondary tie‑break: column weight sum (more of our discs)
            our_weight = sum(12 if col in (2,3,4) else 10 for row in board if row[col] == 1)
            their_weight = sum(12 if col in (2,3,4) else 10 for row in board if row[col] == -1)
            # we want columns where we have more weight than opponent in case of equal height
            col_score = our_weight - their_weight
            cand_score = sum(12 if col in (2,3,4) else 10 for row in board if row[col] == 1) \
                        - sum(12 if col in (2,3,4) else 10 for row in board if row[col] == -1)
            if col_score > cand_score:
                best_col = cand
            # final fallback: lowest index
            elif col_score == cand_score:
                if cand < best_col:
                    best_col = cand
    return best_col

# -------------------------------------------------
# Public API
# -------------------------------------------------
def policy(board: List[List[int]]) -> int:
    """
    Returns the column index (0‑6) where we should drop our disc.
    Always a legal column because the input board is guaranteed to have an empty slot.
    """
    # 1. Immediate win
    win_col = find_winning_move(board)
    if win_col is not None:
        return win_col

    # 2. Block opponent immediate win
    block_col = find_block_move(board)
    if block_col is not None:
        return block_col

    # 3. Look‑ahead search with limited depth and heuristic evaluation
    depth = max_search_depth(board)
    col = best_move_alpha_beta(board, depth)
    return col
