
import random
from copy import deepcopy
from typing import List, Tuple, Optional

def is_winner(board: List[List[int]], player: int) -> bool:
    """Return True if the given player has three in a row."""
    # rows and columns
    for i in range(3):
        if all(board[i][j] == player for j in range(3)):
            return True
        if all(board[j][i] == player for j in range(3)):
            return True
    # diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i] == player for i in range(3)):
        return True
    return False

def get_available_moves(board: List[List[int]]) -> List[Tuple[int, int]]:
    """Return list of empty cell coordinates."""
    moves = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                moves.append((r, c))
    return moves

def minimax(board: List[List[int]], player: int) -> Tuple[int, Optional[Tuple[int, int]]]:
    """
    Minimax search.
    Returns (score, best_move) from the perspective of player=1 (the AI).
    Score: 1 = AI win, -1 = opponent win, 0 = draw.
    """
    # Terminal check
    if is_winner(board, 1):
        return 1, None
    if is_winner(board, -1):
        return -1, None

    empty = get_available_moves(board)
    if not empty:
        return 0, None  # draw

    # Initialize best values
    if player == 1:
        best_score = -float('inf')
    else:
        best_score = float('inf')
    best_moves: List[Tuple[int, int]] = []

    for move in empty:
        r, c = move
        new_board = deepcopy(board)
        new_board[r][c] = player
        score, _ = minimax(new_board, -player)

        if player == 1:
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        else:
            if score < best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

    chosen_move = random.choice(best_moves) if best_moves else None
    return best_score, chosen_move

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Return the AI's next move as (row, col) for a 3x3 Tic‑Tac‑Toe board.
    The board contains 0 (empty), 1 (AI), -1 (opponent).
    """
    _, move = minimax(board, 1)
    if move is None:
        # Should not happen unless the board is full; fallback to first empty cell.
        empties = get_available_moves(board)
        if not empties:
            raise ValueError("No moves left on a full board")
        return empties[0]
    return move
