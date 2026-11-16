
import numpy as np

def policy(board):
    """
    Selects a move for the Lines of Action game based on maximizing connectivity.
    """

    my_pieces = np.argwhere(board == 1)
    best_move = None
    best_score = float('inf')  # Lower is better (fewer connected components)

    for from_row, from_col in my_pieces:
        for to_row in range(8):
            for to_col in range(8):
                move = f"{from_row},{from_col}:{to_row},{to_col}"
                if is_legal_move(board, from_row, from_col, to_row, to_col):
                    new_board = make_move(board, from_row, from_col, to_row, to_col)
                    score = count_connected_components(new_board, 1)

                    if score < best_score:
                        best_score = score
                        best_move = move

    return best_move

def is_legal_move(board, from_row, from_col, to_row, to_col):
    """
    Checks if a move is legal according to Lines of Action rules.
    """
    if from_row == to_row and from_col == to_col:
        return False

    if not (0 <= to_row < 8 and 0 <= to_col < 8):
        return False

    if board[from_row, from_col] != 1:
        return False

    row_diff = to_row - from_row
    col_diff = to_col - from_col

    if row_diff == 0 and col_diff == 0:
        return False

    if row_diff != 0 and col_diff != 0 and abs(row_diff) != abs(col_diff):
        return False

    # Calculate move distance.
    distance = max(abs(row_diff), abs(col_diff))

    # Count pieces in the line of movement.
    if row_diff == 0:  # Horizontal
        line = board[from_row, :]
    elif col_diff == 0:  # Vertical
        line = board[:, from_col]
    else:  # Diagonal
        if row_diff > 0 and col_diff > 0:  # Down-Right
            if not is_valid_diagonal(from_row, from_col, 1, 1):
                return False
            line = np.diag(board[from_row:, from_col:])
        elif row_diff > 0 and col_diff < 0:  # Down-Left
            if not is_valid_diagonal(from_row, from_col, 1, -1):
                return False
            line = np.diag(np.fliplr(board[from_row:, :from_col + 1]))
        elif row_diff < 0 and col_diff > 0:  # Up-Right
            if not is_valid_diagonal(from_row, from_col, -1, 1):
                return False
            line = np.diag(np.flipud(board[:from_row + 1, from_col:]))
        else:  # Up-Left
            if not is_valid_diagonal(from_row, from_col, -1, -1):
                return False
            line = np.diag(np.fliplr(np.flipud(board[:from_row + 1, :from_col + 1])))

    num_pieces = np.count_nonzero(line)

    if distance != num_pieces:
        return False

    # Check for jumps over enemy pieces
    row_step = np.sign(row_diff)
    col_step = np.sign(col_diff)

    curr_row = from_row + row_step
    curr_col = from_col + col_step

    while curr_row != to_row or curr_col != to_col:
        if not (0 <= curr_row < 8 and 0 <= curr_col < 8):
            return False # Should not happen but be defensive

        if board[curr_row, curr_col] == -1:
            return False  # Jumping over opponent

        curr_row += row_step
        curr_col += col_step

    # Destination can be empty or occupied by an opponent.
    if board[to_row, to_col] == 1:
        return False

    return True

def is_valid_diagonal(from_row, from_col, row_direction, col_direction):
      """Tests if a given cell is a place where a valid diagonal slice can start.
      Handles edge cases using the row_direction and col_direction."""
      if row_direction == 1: # from_row is at the start
          if col_direction == 1: # from_col is at the start
              return True
          elif col_direction == -1:
              return True
          else:
              return False
      elif row_direction == -1:
          if col_direction == 1:
              return True
          elif col_direction == -1:
              return True
          else:
              return False
      else:
          return False

def make_move(board, from_row, from_col, to_row, to_col):
    """
    Applies a move to the board and returns the new board.
    """
    new_board = np.copy(board)
    new_board[to_row, to_col] = 1
    new_board[from_row, from_col] = 0
    return new_board

def count_connected_components(board, player):
    """
    Counts the number of connected components for the given player's pieces.
    """
    pieces = np.argwhere(board == player)
    if len(pieces) == 0:
        return 0 # or float('inf') if no pieces

    visited = set()
    count = 0

    def dfs(row, col):
        if (row, col) in visited:
            return

        if not (0 <= row < 8 and 0 <= col < 8 and board[row, col] == player):
            return

        visited.add((row, col))

        # Explore neighbors (8 directions)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                dfs(row + dr, col + dc)

    for row, col in pieces:
        if (row, col) not in visited:
            dfs(row, col)
            count += 1

    return count
