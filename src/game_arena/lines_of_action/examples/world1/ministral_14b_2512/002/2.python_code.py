
import numpy as np
from collections import deque

def policy(board):
    board = np.array(board)
    my_pieces = np.where(board == 1)
    if len(my_pieces[0]) == 0:
        return "0,0:0,0"  # Shouldn't happen per problem statement

    legal_moves = []
    for (i, j) in zip(my_pieces[0], my_pieces[1]):
        moves = generate_legal_moves(board, i, j)
        legal_moves.extend(moves)

    if not legal_moves:
        return "0,0:0,0"  # Shouldn't happen per problem statement

    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        new_board = make_move(board, move)
        score = evaluate_board(new_board)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def generate_legal_moves(board, i, j):
    moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0), (1, 1)]

    for di, dj in directions:
        # Count pieces in the line (including the piece itself)
        line_pieces = count_pieces_in_line(board, i, j, di, dj)
        if line_pieces == 0:
            continue

        # The piece must move exactly line_pieces squares in this direction
        ni, nj = i + di * line_pieces, j + dj * line_pieces
        if not (0 <= ni < 8 and 0 <= nj < 8):
            continue

        # Check if the path is clear (no enemy pieces to jump over)
        if not is_path_clear(board, i, j, di, dj, line_pieces):
            continue

        # Check if landing on friendly piece (unless capturing opponent)
        if board[ni, nj] == 1:
            continue  # Can't land on friendly unless capturing (but capturing is landing on opponent)

        moves.append(f"{i},{j}:{ni},{nj}")

    return moves

def count_pieces_in_line(board, i, j, di, dj):
    count = 0
    # Check in both directions along the line
    for step in range(8):
        ni, nj = i + di * step, j + dj * step
        if 0 <= ni < 8 and 0 <= nj < 8:
            if board[ni, nj] != 0:
                count += 1
        else:
            break

    for step in range(1, 8):
        ni, nj = i - di * step, j - dj * step
        if 0 <= ni < 8 and 0 <= nj < 8:
            if board[ni, nj] != 0:
                count += 1
        else:
            break

    # Include the piece itself
    count += 1
    return count

def is_path_clear(board, i, j, di, dj, distance):
    for step in range(1, distance):
        ni, nj = i + di * step, j + dj * step
        if 0 <= ni < 8 and 0 <= nj < 8:
            if board[ni, nj] == -1:
                return False  # Can't jump over enemy
    return True

def make_move(board, move_str):
    from_part, to_part = move_str.split(':')
    from_row, from_col = map(int, from_part.split(','))
    to_row, to_col = map(int, to_part.split(','))

    new_board = board.copy()
    new_board[from_row, from_col] = 0
    new_board[to_row, to_col] = 1
    return new_board

def evaluate_board(board):
    my_pieces = np.where(board == 1)
    if len(my_pieces[0]) == 0:
        return 0

    visited = set()
    components = 0
    for i, j in zip(my_pieces[0], my_pieces[1]):
        if (i, j) not in visited:
            components += 1
            bfs(board, i, j, visited)

    connectivity_score = -components

    opponent_pieces = np.sum(board == -1)
    opponent_score = -opponent_pieces

    center_score = 0
    for i, j in zip(my_pieces[0], my_pieces[1]):
        center_score += -(abs(i - 3.5) + abs(j - 3.5))

    total_score = connectivity_score * 10 + opponent_score * 5 + center_score * 2
    return total_score

def bfs(board, i, j, visited):
    queue = deque()
    queue.append((i, j))
    visited.add((i, j))
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0), (1, 1)]

    while queue:
        x, y = queue.popleft()
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                if board[nx, ny] == 1 and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
