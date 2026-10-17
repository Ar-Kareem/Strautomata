
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Create a list to hold untried shots
    untried_shots = [(row, col) for row in range(10) for col in range(10) if board[row][col] == 0]
    
    # If there are untried shots, select one randomly
    if untried_shots:
        return random.choice(untried_shots)
    
    # If there are no untried shots (theoretically shouldn't happen), return (0, 0)
    return (0, 0)
