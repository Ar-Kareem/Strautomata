
import numpy as np
from collections import Counter

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    
    # Identify sunk ships by finding contiguous hits
    sunk_lengths = set()
    
    # Check rows for contiguous hits
    for i in range(10):
        j = 0
        while j < 10:
            if board[i, j] == 1:
                start = j
                while j < 10 and board[i, j] == 1:
                    j += 1
                length = j - start
                # Check if it's isolated (sunk ship)
                isolated = True
                k = max(0, start - 1)
                if k < 10 and board[i, k] == 1:
                    isolated = False
                k = j
                if k < 10 and board[i, k] == 1:
                    isolated = False
                if isolated:
                    sunk_lengths.add(length)
            else:
                j += 1
    
    # Check columns for contiguous hits
    for j in range(10):
        i = 0
        while i < 10:
            if board[i, j] == 1:
                start = i
                while i < 10 and board[i, j] == 1:
                    i += 1
                length = i - start
                # Check if it's isolated (sunk ship)
                isolated = True
                k = max(0, start - 1)
                if k < 10 and board[k, j] == 1:
                    isolated = False
                k = i
                if k < 10 and board[k, j] == 1:
                    isolated = False
                if isolated:
                    sunk_lengths.add(length)
            else:
                i += 1
    
    # Remaining ships
    original_lengths = Counter([5, 4, 3, 3, 2])
    sunk = Counter(sunk_lengths)
    remaining = original_lengths - sunk
    
    # Probabilities
    prob = np.zeros((10, 10))
    directions = [('h', 0, 1), ('v', 1, 0)]  # (type, dr, dc)
    
    for length in remaining:
        for dir_name, dr, dc in directions:
            max_start = 10 - length
            for r in range(10):
                for c in range(10):
                    if (dr == 1 and r <= max_start) or (dc == 1 and c <= max_start):
                        positions = [(r + k*dr, c + k*dc) for k in range(length)]
                        # Valid if no misses in positions
                        valid = all(board[pr, pc] != -1 for pr, pc in positions)
                        if valid:
                            for pr, pc in positions:
                                if board[pr, pc] == 0:
                                    prob[pr, pc] += remaining[length]
    
    # Get possible shots
    possible_shots = [(i, j) for i in range(10) for j in range(10) if board[i, j] == 0]
    
    if not possible_shots:
        return (0, 0)  # Fallback, though unlikely
    
    # Best shot by prob, tie by first occurrence
    best_shot = max(possible_shots, key=lambda p: prob[p[0], p[1]])
    
    # If all probs are 0, use hunt mode: even parity
    if prob[best_shot[0], best_shot[1]] == 0:
        for shot in possible_shots:
            if sum(shot) % 2 == 0:
                return shot
        return possible_shots[0]  # All odd, pick first
    
    return best_shot
