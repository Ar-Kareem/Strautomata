
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    empty_cells = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    if not empty_cells:
        return (0, 0)  # Shouldn't happen in valid games

    def is_winning(b, player):
        # Check rows
        for row in b:
            if all(cell == player for cell in row):
                return True
        # Check columns
        for col in range(3):
            if all(b[row][col] == player for row in range(3)):
                return True
        # Check diagonals
        if all(b[i][i] == player for i in range(3)):
            return True
        if all(b[i][2 - i] == player for i in range(3)):
            return True
        return False

    def check_winner(b):
        if is_winning(b, 1):
            return 1
        elif is_winning(b, -1):
            return -1
        else:
            return None

    def is_draw(b):
        return all(cell != 0 for row in b for cell in row)

    memo = {}

    def minimax(b, is_maximizing):
        nonlocal memo
        board_tuple = (tuple(b[0]), tuple(b[1]), tuple(b[2]))
        if board_tuple in memo:
            return memo[board_tuple]

        winner = check_winner(b)
        if winner is not None:
            memo[board_tuple] = 1 if winner == 1 else -1
            return memo[board_tuple]
        if is_draw(b):
            memo[board_tuple] = 0
            return 0

        best_score = float('-inf') if is_maximizing else float('inf')

        for i in range(3):
            for j in range(3):
                if b[i][j] == 0:
                    new_b = [row[:] for row in b]
                    new_b[i][j] = 1 if is_maximizing else -1
                    score = minimax(new_b, not is_maximizing)
                    if is_maximizing:
                        best_score = max(best_score, score)
                    else:
                        best_score = min(best_score, score)
        memo[board_tuple] = best_score
        return best_score

    best_move = empty_cells[0]
    best_score = float('-inf')

    for i, j in empty_cells:
        new_board = [row[:] for row in board]
        new_board[i][j] = 1
        if check_winner(new_board) == 1:
            return (i, j)
        current_score = minimax(new_board, is_maximizing=False)
        if current_score > best_score:
            best_score = current_score
            best_move = (i, j)

    return best_move
