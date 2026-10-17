
import numpy as np
from collections import deque

def policy(board):
    board = np.array(board)
    my_pieces = np.argwhere(board == 1)

    legal_moves = []
    for piece in my_pieces:
        from_row, from_col = piece
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),          (0, 1),
                      (1, -1),  (1, 0), (1, 1)]
        for dr, dc in directions:
            moves = get_legal_moves(board, from_row, from_col, dr, dc)
            legal_moves.extend(moves)

    legal_moves = list(set(legal_moves))

    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        new_board = board.copy()
        from_row, from_col, to_row, to_col = parse_move(move)
        new_board[from_row, from_col] = 0
        new_board[to_row, to_col] = 1
        score = evaluate_board(new_board)
        # Bonus for capturing
        if board[to_row, to_col] == -1:
            score += 10  # High bonus for captures
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def get_legal_moves(board, from_row, from_col, dr, dc):
    moves = []
    n = board.shape[0]
    count = 0
    # Count pieces in the line in both directions
    r, c = from_row + dr, from_col + dc
    while 0 <= r < n and 0 <= c < n and board[r, c] != 0:
        count += 1
        r += dr
        c += dc
    r, c = from_row - dr, from_col - dc
    while 0 <= r < n and 0 <= c < n and board[r, c] != 0:
        count += 1
        r -= dr
        c -= dc
    count -= 1  # Subtract the piece itself

    # Check in the positive direction
    r, c = from_row, from_col
    for step in range(1, count + 1):
        r += dr
        c += dc
        if not (0 <= r < n and 0 <= c < n):
            break
        # Check path for enemy pieces
        path_clear = True
        for i in range(1, step):
            check_r, check_c = from_row + i * dr, from_col + i * dc
            if 0 <= check_r < n and 0 <= check_c < n:
                if board[check_r, check_c] == -1:
                    path_clear = False
                    break
        if path_clear:
            if board[r, c] == -1 or board[r, c] == 0:
                moves.append(f"{from_row},{from_col}:{r},{c}")

    # Check in the negative direction
    r, c = from_row, from_col
    for step in range(1, count + 1):
        r -= dr
        c -= dc
        if not (0 <= r < n and 0 <= c < n):
            break
        # Check path for enemy pieces
        path_clear = True
        for i in range(1, step):
            check_r, check_c = from_row - i * dr, from_col - i * dc
            if 0 <= check_r < n and 0 <= check_c < n:
                if board[check_r, check_c] == -1:
                    path_clear = False
                    break
        if path_clear:
            if board[r, c] == -1 or board[r, c] == 0:
                moves.append(f"{from_row},{from_col}:{r},{c}")

    return moves

def evaluate_board(board):
    # Count contiguous groups of my pieces
    visited = np.zeros_like(board, dtype=bool)
    groups = 0
    for r in range(8):
        for c in range(8):
            if board[r, c] == 1 and not visited[r, c]:
                groups += 1
                queue = deque([(r, c)])
                visited[r, c] = True
                while queue:
                    x, y = queue.popleft()
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < 8 and 0 <= ny < 8:
                                if board[nx, ny] == 1 and not visited[nx, ny]:
                                    visited[nx, ny] = True
                                    queue.append((nx, ny))
    # Score is inversely proportional to the number of groups
    score = -groups
    return score

def parse_move(move_str):
    from_part, to_part = move_str.split(':')
    from_row, from_col = map(int, from_part.split(','))
    to_row, to_col = map(int, to_part.split(','))
    return from_row, from_col, to_row, to_col
