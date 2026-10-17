
import numpy as np
from collections import deque

def policy(board) -> str:
    # Generate all legal moves
    legal_moves = get_legal_moves(board)

    if not legal_moves:
        raise ValueError("No legal moves available")

    # Evaluate each move and select the best one
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        # Create a copy of the board to simulate the move
        new_board = [row[:] for row in board]
        from_row, from_col, to_row, to_col = parse_move(move)

        # Execute the move
        piece = new_board[from_row][from_col]
        new_board[from_row][from_col] = 0
        new_board[to_row][to_col] = piece

        # Evaluate the resulting position
        score = evaluate_position(new_board)

        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def get_legal_moves(board):
    moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0), (1, 1)]

    for i in range(8):
        for j in range(8):
            if board[i][j] == 1:  # Current player's piece
                for dx, dy in directions:
                    # Calculate pieces in this line
                    pieces_in_line = count_pieces_in_line(board, i, j, dx, dy)

                    if pieces_in_line == 0:
                        continue

                    # Check possible landing positions
                    for step in range(1, 9):
                        ni, nj = i + step * dx, j + step * dy

                        # Check if within bounds
                        if ni < 0 or ni >= 8 or nj < 0 or nj >= 8:
                            break

                        # Check if we can land here
                        if step == pieces_in_line:
                            # Check if path is clear (no enemy pieces jumped)
                            if is_path_clear(board, i, j, ni, nj, dx, dy):
                                moves.append(f"{i},{j}:{ni},{nj}")
                            break
                        elif board[ni][nj] == -1:  # Enemy piece in path
                            break

    return moves

def count_pieces_in_line(board, i, j, dx, dy):
    count = 0
    for step in range(1, 9):
        ni, nj = i + step * dx, j + step * dy
        if ni < 0 or ni >= 8 or nj < 0 or nj >= 8:
            break
        if board[ni][nj] != 0:
            count += 1
    return count

def is_path_clear(board, i, j, ni, nj, dx, dy):
    steps = max(abs(ni - i), abs(nj - j))
    for step in range(1, steps):
        x, y = i + step * dx, j + step * dy
        if board[x][y] == -1:  # Enemy piece in path
            return False
    return True

def parse_move(move_str):
    from_part, to_part = move_str.split(':')
    from_row, from_col = map(int, from_part.split(','))
    to_row, to_col = map(int, to_part.split(','))
    return from_row, from_col, to_row, to_col

def evaluate_position(board):
    # Count connected components for current player
    player_components = count_connected_components(board, 1)

    # Count connected components for opponent
    opponent_components = count_connected_components(board, -1)

    # Count pieces
    player_pieces = sum(row.count(1) for row in board)
    opponent_pieces = sum(row.count(-1) for row in board)

    # Calculate center control (distance from center)
    center_control = 0
    for i in range(8):
        for j in range(8):
            if board[i][j] == 1:
                # Distance from center (3.5, 3.5)
                dist = abs(i - 3.5) + abs(j - 3.5)
                center_control += (7 - dist)  # Higher for closer to center

    # Evaluation weights (tuned for performance)
    score = 0
    score += -player_components * 100  # Fewer components is better
    score += opponent_components * 50   # More opponent components is better
    score += (opponent_pieces - player_pieces) * -20  # More pieces is better
    score += center_control * 5        # Center control is good

    return score

def count_connected_components(board, player):
    visited = [[False for _ in range(8)] for _ in range(8)]
    components = 0

    for i in range(8):
        for j in range(8):
            if board[i][j] == player and not visited[i][j]:
                components += 1
                # BFS to mark all connected pieces
                queue = deque([(i, j)])
                visited[i][j] = True

                while queue:
                    x, y = queue.popleft()
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < 8 and 0 <= ny < 8:
                                if board[nx][ny] == player and not visited[nx][ny]:
                                    visited[nx][ny] = True
                                    queue.append((nx, ny))

    return components
