
import numpy as np
from typing import Optional, Tuple

def is_winning_move(board: list[list[int]], player: int) -> bool:
    """Check if the specified player has a winning move on the board."""
    # Convert the board to a numpy array for easier manipulation
    board_np = np.array(board)

    # Check rows and columns
    for i in range(3):
        if np.all(board_np[i, :] == player) or np.all(board_np[:, i] == player):
            return True

    # Check diagonals
    if np.all(np.diag(board_np) == player) or np.all(np.diag(np.fliplr(board_np)) == player):
        return True

    return False

def get_empty_cells(board: list[list[int]]) -> list[Tuple[int, int]]:
    """Return a list of all empty cells on the board as (row, column) tuples."""
    empty_cells = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                empty_cells.append((i, j))
    return empty_cells

def evaluate_board(board: list[list[int]], player: int) -> int:
    """Evaluate the board for the current player. Returns:
    - 10 if current player wins,
    - -10 if opponent wins,
    - 0 if it's a draw,
    - otherwise, a heuristic value (e.g., based on potential winning lines).
    """
    board_np = np.array(board)
    opponent = -1 if player == 1 else 1

    if is_winning_move(board_np, player):
        return 10
    elif is_winning_move(board_np, opponent):
        return -10
    else:
        # Check if the board is full (draw)
        if np.all(board_np != 0):
            return 0

        # Heuristic: count potential winning lines for the player and opponent
        player_lines = 0
        opponent_lines = 0

        # Check rows
        for i in range(3):
            row = board_np[i, :]
            if row[0] == row[1] == row[2] == player:
                pass  # already handled by is_winning_move
            elif row[0] == row[1] == row[2] == 0:
                pass  # no potential winning line
            else:
                player_lines += row.tolist().count(player)
                opponent_lines += row.tolist().count(opponent)

        # Check columns
        for j in range(3):
            col = board_np[:, j]
            if col[0] == col[1] == col[2] == player:
                pass
            elif col[0] == col[1] == col[2] == 0:
                pass
            else:
                player_lines += col.tolist().count(player)
                opponent_lines += col.tolist().count(opponent)

        # Check diagonals
        diag1 = np.diag(board_np)
        if diag1[0] == diag1[1] == diag1[2] == player:
            pass
        elif diag1[0] == diag1[1] == diag1[2] == 0:
            pass
        else:
            player_lines += diag1.tolist().count(player)
            opponent_lines += diag1.tolist().count(opponent)

        diag2 = np.diag(np.fliplr(board_np))
        if diag2[0] == diag2[1] == diag2[2] == player:
            pass
        elif diag2[0] == diag2[1] == diag2[2] == 0:
            pass
        else:
            player_lines += diag2.tolist().count(player)
            opponent_lines += diag2.tolist().count(opponent)

        # Score based on potential lines (more lines for player is better)
        return player_lines - opponent_lines

def minimax(board: list[list[int]], depth: int, is_maximizing: bool, alpha: Optional[float] = None, beta: Optional[float] = None) -> Tuple[int, int]:
    """Minimax algorithm with alpha-beta pruning to find the best move."""
    if alpha is None:
        alpha = -float('inf')
    if beta is None:
        beta = float('inf')

    # Base case: check if the current board state is a win or draw
    board_np = np.array(board)
    player = 1 if is_maximizing else -1
    opponent = -1 if player == 1 else 1

    if is_winning_move(board_np, player):
        return (0, 0)  # dummy move, actual move is already winning
    elif is_winning_move(board_np, opponent):
        return (-1, -1)  # dummy move, opponent already won

    # Check if the board is full (draw)
    if np.all(board_np != 0):
        return (-1, -1)  # dummy move, draw

    if depth == 0:
        return evaluate_board(board_np, player), (0, 0)  # dummy move, return heuristic value

    empty_cells = get_empty_cells(board_np)
    if not empty_cells:
        return 0, (0, 0)  # dummy move, no moves left

    best_move = (0, 0)
    if is_maximizing:
        best_value = -float('inf')
        for move in empty_cells:
            new_board = [row.copy() for row in board_np]
            new_board[move[0]][move[1]] = player
            value, _ = minimax(new_board, depth - 1, False, alpha, beta)
            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, best_value)
            if beta <= alpha:
                break  # alpha-beta pruning
        return best_value, best_move
    else:
        best_value = float('inf')
        for move in empty_cells:
            new_board = [row.copy() for row in board_np]
            new_board[move[0]][move[1]] = opponent
            value, _ = minimax(new_board, depth - 1, True, alpha, beta)
            if value < best_value:
                best_value = value
                best_move = move
            beta = min(beta, best_value)
            if beta <= alpha:
                break  # alpha-beta pruning
        return best_value, best_move

def policy(board: list[list[int]]) -> tuple[int, int]:
    """Determine the next move for the current player using minimax with alpha-beta pruning."""
    # Convert the board to a numpy array for easier manipulation
    board_np = np.array(board)

    # Check if the current player can win immediately
    empty_cells = get_empty_cells(board_np)
    for move in empty_cells:
        new_board = [row.copy() for row in board_np]
        new_board[move[0]][move[1]] = 1
        if is_winning_move(new_board, 1):
            return move

    # Check if the opponent can win immediately and block
    opponent = -1
    for move in empty_cells:
        new_board = [row.copy() for row in board_np]
        new_board[move[0]][move[1]] = opponent
        if is_winning_move(new_board, opponent):
            return move

    # If no immediate win or block, use minimax to find the best move
    # We use a depth of 9 (max possible moves in Tic Tac Toe)
    # But in practice, depth of 5-6 is sufficient for optimal play
    depth = 9
    _, best_move = minimax(board_np.tolist(), depth, True)
    return best_move
