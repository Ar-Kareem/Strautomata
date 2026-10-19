
import numpy as np
import random

def legal_move(board, row, col):
    return (1 <= row <= 19) and (1 <= col <= 19) and (board[row - 1, col - 1] == 0)

def simulate(board, me, opponent):
    # Here we will simply try random moves and see who wins after a fixed number of turns
    for _ in range(100):
        available_moves = [(r, c) for r in range(1, 20) for c in range(1, 20) if legal_move(board, r, c)]
        if not available_moves:
            break

        # Randomly play a move
        move = random.choice(available_moves)
        board[move[0] - 1, move[1] - 1] = 1  # Assume '1' is our stone

        # Check winner (this can be very complex in Go, simplified here)
        # You may need an actual Go game implementation for real winner checks
        # Here, let's just break if both players play 10 moves randomly without capturing
        if len(available_moves) >= 10:  # Simplified game end condition
            break

    return random.choice([True, False])  # Simulate a win/loss

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    board = np.zeros((19, 19), dtype=int)

    # Place my stones (1)
    for (r, c) in me:
        board[r - 1, c - 1] = 1

    # Place opponent's stones (2)
    for (r, c) in opponent:
        board[r - 1, c - 1] = 2

    best_move = (0, 0)
    best_score = -1

    for r in range(1, 20):
        for c in range(1, 20):
            if legal_move(board, r, c):
                board[r - 1, c - 1] = 1  # Play my stone
                win_count = simulate(np.copy(board), me, opponent)
                score = 1 if win_count else 0

                if score > best_score:
                    best_score = score
                    best_move = (r, c)

                board[r - 1, c - 1] = 0  # Undo move

    return best_move, memory
