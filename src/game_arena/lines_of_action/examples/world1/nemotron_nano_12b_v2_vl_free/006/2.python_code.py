
import numpy as np

def policy(board):
    """
    Returns a valid move string in the format "from_row,from_col:to_row,to_col".
    Moves are prioritized based on capturing potential and strategic movement.
    """
    moves = []

    # Process all possible moves for each of the player's pieces
    for i in range(8):
        for j in range(8):
            if board[i][j] != 1:
                continue

            # Row-based moves (left and right)
            row_k = sum(1 for y in range(8) if board[i][y] != 0)
            if row_k > 0:
                if j - row_k >= 0:
                    valid = True
                    for step in range(1, row_k + 1):
                        path_col = j - step
                        if board[i][path_col] == -1:
                            valid = False
                            break
                    if valid and board[i][j - row_k] not in (1, 0):
                        moves.append(f"{i},{j}:{i},{j - row_k}")

                new_j = j + row_k
                if new_j < 8:
                    valid = True
                    for step in range(1, row_k + 1):
                        path_col = j + step
                        if path_col >= 8 or board[i][path_col] == -1:
                            valid = False
                            break
                    if valid and board[i][new_j] not in (1, 0):
                        moves.append(f"{i},{j}:{i},{new_j}")

            # Column-based moves (up and down)
            col_k = sum(1 for x in range(8) if board[x][j] != 0)
            if col_k > 0:
                new_i = i - col_k
                if new_i >= 0:
                    valid = True
                    for step in range(1, col_k + 1):
                        path_row = i - step
                        if board[path_row][j] == -1:
                            valid = False
                            break
                    if valid and board[new_i][j] not in (1, 0):
                        moves.append(f"{i},{j}:{new_i},{j}")

                new_i = i + col_k
                if new_i < 8:
                    valid = True
                    for step in range(1, col_k + 1):
                        path_row = i + step
                        if path_row >= 8 or board[path_row][j] == -1:
                            valid = False
                            break
                    if valid and board[new_i][j] not in (1, 0):
                        moves.append(f"{i},{j}:{new_i},{j}")

            # Diagonal 1: top-left to bottom-right
            c = i - j
            diag_k = 0
            for x in range(8):
                y = x - c
                if 0 <= y < 8 and board[x][y] != 0:
                    diag_k += 1
            if diag_k > 0:
                # Up-left direction
                new_i, new_j = i - diag_k, j - diag_k
                if new_i >= 0 and new_j >= 0:
                    valid = True
                    for step in range(1, diag_k + 1):
                        x = i - step
                        y = j - step
                        if board[x][y] == -1:
                            valid = False
                            break
                    if valid and board[new_i][new_j] not in (1, 0):
                        moves.append(f"{i},{j}:{new_i},{new_j}")

                # Down-right direction
                new_i, new_j = i + diag_k, j + diag_k
                if new_i < 8 and new_j < 8:
                    valid = True
                    for step in range(1, diag_k + 1):
                        x = i + step
                        y = j + step
                        if x >= 8 or y >= 8 or board[x][y] == -1:
                            valid = False
                            break
                    if valid and board[new_i][new_j] not in (1, 0):
                        moves.append(f"{i},{j}:{new_i},{new_j}")

            # Diagonal 2: top-right to bottom-left
            t = i + j
            diag_k = 0
            for x in range(8):
                y = t - x
                if 0 <= y < 8 and board[x][y] != 0:
                    diag_k += 1
            if diag_k > 0:
                # Up-right direction
                new_i, new_j = i - diag_k, j + diag_k
                if new_i >= 0 and new_j < 8:
                    valid = True
                    for step in range(1, diag_k + 1):
                        x = i - step
                        y = j + step
                        if board[x][y] == -1:
                            valid = False
                            break
                    if valid and board[new_i][new_j] not in (1, 0):
                        moves.append(f"{i},{j}:{new_i},{new_j}")

                # Down-left direction
                new_i, new_j = i + diag_k, j - diag_k
                if new_i < 8 and new_j >= 0:
                    valid = True
                    for step in range(1, diag_k + 1):
                        x = i + step
                        y = j - step
                        if x >= 8 or y >= 8 or board[x][y] == -1:
                            valid = False
                            break
                    if valid and board[new_i][new_j] not in (1, 0):
                        moves.append(f"{i},{j}:{new_i},{new_j}")

    # Deduplicate moves in case duplicates are generated
    moves = list(set(moves))

    if not moves:
        # Return empty string if no moves are found (should not happen in valid game state)
        return ''

    # Prioritize moves that capture enemy pieces
    capture_moves = [m for m in moves if board[parse_move(m)[3]][parse_move(m)[4]] == -1]

    if capture_moves:
        return np.random.choice(capture_moves)
    else:
        # No captures available, choose randomly from available moves
        return np.random.choice(moves)

def parse_move(move):
    """
    Parses a move string into source and destination coordinates.
    Returns: (src_row, src_col, dest_row, dest_col)
    """
    src, dest = move.split(':')
    src_row, src_col = map(int, src.split(','))
    dest_row, dest_col = map(int, dest.split(','))
    return (src_row, src_col, dest_row, dest_col)
