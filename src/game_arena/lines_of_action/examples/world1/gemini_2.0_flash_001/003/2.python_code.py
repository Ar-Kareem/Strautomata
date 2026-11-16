
import numpy as np

def count_pieces(board):
    """Counts the total number of pieces on the board."""
    return np.sum(np.abs(board))

def is_valid_move(board, from_row, from_col, to_row, to_col):
    """Checks if a move is within the board boundaries."""
    return 0 <= to_row < 8 and 0 <= to_col < 8

def check_path(board, from_row, from_col, to_row, to_col):
    """Checks path for pieces."""
    row_diff = to_row - from_row
    col_diff = to_col - from_col
    row_dir = 0 if row_diff == 0 else row_diff // abs(row_diff)
    col_dir = 0 if col_diff == 0 else col_diff // abs(col_diff)

    curr_row, curr_col = from_row + row_dir, from_col + col_dir
    while curr_row != to_row or curr_col != to_col:
        if board[curr_row, curr_col] == -1:  # Enemy piece obstruction
            return False
        if board[curr_row, curr_col] != 0: #piece of any kind
            if board[curr_row, curr_col] == 1:
                pass
            else:
                return False

        curr_row += row_dir
        curr_col += col_dir

    return True

def get_legal_moves(board):
    """Generates all legal moves for the current player."""
    moves = []
    piece_count = count_pieces(board)

    for from_row in range(8):
        for from_col in range(8):
            if board[from_row, from_col] == 1:
                # Check horizontal moves
                for to_col in range(8):
                    to_row = from_row
                    if to_col != from_col and is_valid_move(board, from_row, from_col, to_row, to_col):
                        if abs(to_col - from_col) == piece_count:
                            if check_path(board, from_row, from_col, to_row, to_col):
                                moves.append(f"{from_row},{from_col}:{to_row},{to_col}")

                # Check vertical moves
                for to_row in range(8):
                    to_col = from_col
                    if to_row != from_row and is_valid_move(board, from_row, from_col, to_row, to_col):
                        if abs(to_row - from_row) == piece_count:
                            if check_path(board, from_row, from_col, to_row, to_col):
                                moves.append(f"{from_row},{from_col}:{to_row},{to_col}")

                # Check diagonal moves
                for row_dir in [-1, 1]:
                    for col_dir in [-1, 1]:
                        to_row = from_row + piece_count * row_dir
                        to_col = from_col + piece_count * col_dir

                        if is_valid_move(board, from_row, from_col, to_row, to_col):
                            if check_path(board, from_row, from_col, to_row, to_col):
                                moves.append(f"{from_row},{from_col}:{to_row},{to_col}")

    return moves

def calculate_connected_components(board):
        """Calculates the number of connected components of the player's pieces."""
        visited = np.zeros_like(board, dtype=bool)
        num_components = 0
        player_positions = np.argwhere(board == 1)

        def bfs(row, col):
            q = [(row, col)]
            visited[row, col] = True
            while q:
                r, c = q.pop(0)
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr, nc] == 1 and not visited[nr, nc]:
                            q.append((nr, nc))
                            visited[nr, nc] = True

        for row, col in player_positions:
            if not visited[row, col]:
                bfs(row, col)
                num_components += 1

        return num_components


def evaluate_move(board, move):
    """ оценивает состояние доски после хода """
    from_row, from_col, to_row, to_col = map(int, move.replace(":", ",").split(","))
    new_board = board.copy()

    new_board[to_row, to_col] = 1
    new_board[from_row, from_col] = 0

    return -calculate_connected_components(new_board)

def policy(board):
    """Selects the best move based on the board state."""
    board = np.array(board)

    legal_moves = get_legal_moves(board)

    if not legal_moves:
        return None

    best_move = None
    best_score = float('-inf')

    for move in legal_moves:
        score = evaluate_move(board, move)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move
