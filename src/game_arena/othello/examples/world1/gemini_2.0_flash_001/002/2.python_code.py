
import numpy as np
import random

def get_legal_moves(you: np.ndarray, opponent: np.ndarray):
    """Finds all legal moves for the current player."""
    board_size = 8
    legal_moves = []
    for r in range(board_size):
        for c in range(board_size):
            if you[r][c] == 0 and opponent[r][c] == 0:
                if is_legal_move(you, opponent, r, c):
                    legal_moves.append((r, c))
    return legal_moves

def is_legal_move(you: np.ndarray, opponent: np.ndarray, row: int, col: int):
    """Checks if a move is legal by checking if it flips any opponent pieces."""
    board_size = 8
    if you[row][col] == 1 or opponent[row][col] == 1:
        return False

    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue

            r, c = row + dr, col + dc
            if 0 <= r < board_size and 0 <= c < board_size and opponent[r][c] == 1:
                while 0 <= r < board_size and 0 <= c < board_size and opponent[r][c] == 1:
                    r += dr
                    c += dc
                if 0 <= r < board_size and 0 <= c < board_size and you[r][c] == 1:
                    return True

    return False

def flip_discs(you: np.ndarray, opponent: np.ndarray, row: int, col: int):
    """Flips the opponent's discs when a valid move is made."""
    board_size = 8
    flipped_discs = []
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue

            r, c = row + dr, col + dc
            discs_to_flip = []
            while 0 <= r < board_size and 0 <= c < board_size and opponent[r][c] == 1:
                discs_to_flip.append((r, c))
                r += dr
                c += dc
            if 0 <= r < board_size and 0 <= c < board_size and you[r][c] == 1:
                flipped_discs.extend(discs_to_flip)

    return flipped_discs

def calculate_mobility(you: np.ndarray, opponent: np.ndarray):
    """Calculates the mobility (number of legal moves) for the given player."""
    return len(get_legal_moves(you, opponent))

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    A smart Othello policy.
    """
    board_size = 8
    legal_moves = get_legal_moves(you, opponent)

    if not legal_moves:
        return "pass"

    # Prioritize corners
    for move in legal_moves:
        if (move[0] == 0 or move[0] == board_size - 1) and \
           (move[1] == 0 or move[1] == board_size - 1):
            return chr(move[1] + ord('a')) + str(move[0] + 1)

    # Prioritize edges
    for move in legal_moves:
        if move[0] == 0 or move[0] == board_size - 1 or \
           move[1] == 0 or move[1] == board_size - 1:
             return chr(move[1] + ord('a')) + str(move[0] + 1)

    # Evaluate moves based on mobility and flipped discs
    best_move = None
    best_score = -float('inf')

    location_significance = {
        (0, 0): 100, (0, 7): 100, (7, 0): 100, (7, 7): 100,  # Corners
        (0, 1): -10, (0, 6): -10, (1, 0): -10, (1, 1):-10, (1, 6): -10, (1,7):-10,  # Near corners
        (6, 0): -10, (6, 1): -10, (6, 6): -10, (6,7):-10, (7, 1): -10, (7, 6): -10,
        (1, 1): -20, (1, 6): -20, (6, 1): -20, (6, 6): -20,
        (0, 2): 5, (0, 3): 5, (0, 4): 5, (0, 5): 5,  # Edges
        (2, 0): 5, (3, 0): 5, (4, 0): 5, (5, 0): 5,
        (7, 2): 5, (7, 3): 5, (7, 4): 5, (7, 5): 5,
        (2, 7): 5, (3, 7): 5, (4, 7): 5, (5, 7): 5,
        (1,2):3, (1,3):3, (1,4):3, (1,5):3, (2,1):3, (3,1):3, (4,1):3, (5,1):3,
        (6,2):3, (6,3):3, (6,4):3, (6,5):3, (2,6):3, (3,6):3, (4,6):3, (5,6):3,
    }

    for move in legal_moves:
        r, c = move
        temp_you = you.copy()
        temp_opponent = opponent.copy()

        # Simulate the move
        temp_you[r][c] = 1
        flipped = flip_discs(temp_you, temp_opponent, r, c)
        for fr, fc in flipped:
            temp_you[fr][fc] = 1
            temp_opponent[fr][fc] = 0


        score = len(flipped) # Base score: number of flipped discs
        if (r,c) in location_significance:
            score += location_significance[(r,c)]
            
        # Add a small amount of randomization
        score += random.uniform(0, 0.1)
            
        if score > best_score:
            best_score = score
            best_move = move

    return chr(best_move[1] + ord('a')) + str(best_move[0] + 1)
