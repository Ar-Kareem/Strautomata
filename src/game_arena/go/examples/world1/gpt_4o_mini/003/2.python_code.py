
import numpy as np

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board_size = 19
    board = np.zeros((board_size, board_size), dtype=int)  # 0: empty, 1: me, -1: opponent
    
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = -1

    def is_on_board(row, col):
        return 0 <= row < board_size and 0 <= col < board_size

    def get_liberties(stone_positions):
        liberties = set()
        for r, c in stone_positions:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if abs(dr) != abs(dc):  # Only check horizontal and vertical
                        nr, nc = r + dr, c + dc
                        if is_on_board(nr - 1, nc - 1) and board[nr - 1, nc - 1] == 0:
                            liberties.add((nr, nc))
        return liberties

    def evaluate_move(row, col):
        if board[row - 1, col - 1] != 0:
            return -1  # Invalid move
        # Placeholder for more complex evaluation: safety, connection, etc.
        my_stones = get_liberties(me)
        opponent_stones = get_liberties(opponent)
        move_score = len(my_stones) - len(opponent_stones)
        return move_score

    best_move = (0, 0)
    best_score = float('-inf')  # Start with the worst possible score

    for row in range(1, board_size + 1):
        for col in range(1, board_size + 1):
            score = evaluate_move(row, col)
            if score > best_score:
                best_score = score
                best_move = (row, col)

    return best_move
