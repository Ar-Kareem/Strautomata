
import numpy as np
from collections import deque
import random

def policy(board):
    def get_legal_moves(board):
        moves = []
        for i in range(8):
            for j in range(8):
                if board[i][j] != 1:
                    continue
                directions = [(-1, -1), (-1, 0), (-1, 1),
                              (0, -1),          (0, 1),
                              (1, -1),  (1, 0), (1, 1)]
                for dr, dc in directions:
                    line_count = 0
                    if dr == 0:
                        line_count = sum(1 for c in range(8) if board[i][c] != 0)
                    elif dc == 0:
                        line_count = sum(1 for r in range(8) if board[r][j] != 0)
                    else:
                        if dr == -1 and dc == -1 or dr == 1 and dc == 1:
                            const = i - j
                            line_count = sum(1 for r in range(8) for c in range(8) if r - c == const and board[r][c] != 0)
                        else:
                            const = i + j
                            line_count = sum(1 for r in range(8) for c in range(8) if r + c == const and board[r][c] != 0)
                    if line_count == 0:
                        continue
                    new_i = i + dr * line_count
                    new_j = j + dc * line_count
                    if new_i < 0 or new_i >= 8 or new_j < 0 or new_j >= 8:
                        continue
                    blocked = False
                    for step in range(1, line_count):
                        r = i + dr * step
                        c = j + dc * step
                        if board[r][c] == -1:
                            blocked = True
                            break
                    if not blocked:
                        moves.append(f"{i},{j}:{new_i},{new_j}")
        return moves

    def apply_move(original_board, move_str):
        new_board = [row.copy() for row in original_board]
        from_part, to_part = move_str.split(':')
        from_row, from_col = map(int, from_part.split(','))
        to_row, to_col = map(int, to_part.split(','))
        new_board[from_row][from_col] = 0
        new_board[to_row][to_col] = 1
        return new_board

    def is_win(board_state):
        visited = set()
        start = None
        for i in range(8):
            for j in range(8):
                if board_state[i][j] == 1:
                    start = (i, j)
                    break
            if start:
                break
        if not start:
            return False
        q = deque([start])
        visited.add(start)
        while q:
            r, c = q.popleft()
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in visited and board_state[nr][nc] == 1:
                        visited.add((nr, nc))
                        q.append((nr, nc))
        return all(board_state[i][j] != 1 or (i, j) in visited for i in range(8) for j in range(8))

    def count_groups(board_state):
        visited = set()
        groups = 0
        for i in range(8):
            for j in range(8):
                if board_state[i][j] == 1 and (i, j) not in visited:
                    groups += 1
                    q = deque([(i, j)])
                    visited.add((i, j))
                    while q:
                        r, c = q.popleft()
                        for dr in [-1, 0, 1]:
                            for dc in [-1, 0, 1]:
                                if dr == 0 and dc == 0:
                                    continue
                                nr, nc = r + dr, c + dc
                                if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in visited and board_state[nr][nc] == 1:
                                    visited.add((nr, nc))
                                    q.append((nr, nc))
        return groups

    def evaluate(board_state):
        groups = count_groups(board_state)
        score = 1000 - groups * 100
        center = 3.5
        total_distance = 0
        count = 0
        for i in range(8):
            for j in range(8):
                if board_state[i][j] == 1:
                    distance = np.sqrt((i - center)**2 + (j - center)**2)
                    total_distance += distance
                    count += 1
        if count > 0:
            avg_distance = total_distance / count
            score -= avg_distance * 10
        return score

    legal_moves = get_legal_moves(board)
    if not legal_moves:
        return None

    random.shuffle(legal_moves)

    winning_move = None
    best_score = -float('inf')
    best_move = legal_moves[0]

    for move in legal_moves:
        new_board = apply_move(board, move)
        if is_win(new_board):
            winning_move = move
            break
        to_part = move.split(':')[1]
        to_row, to_col = map(int, to_part.split(','))
        is_capture = board[to_row][to_col] == -1
        current_score = evaluate(new_board)
        if is_capture:
            current_score += 100
        if current_score > best_score:
            best_score = current_score
            best_move = move

    if winning_move:
        return winning_move
    return best_move
