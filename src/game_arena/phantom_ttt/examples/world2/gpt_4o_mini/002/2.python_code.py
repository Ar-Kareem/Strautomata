
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    available_moves = []
    
    # Collect available moves
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:  # Cell is not confirmed to be placed
                available_moves.append((row, col))
    
    # If no available moves, return an invalid one (this shouldn't happen in a valid state)
    if not available_moves:
        return (random.randint(0, 2), random.randint(0, 2))  # This line is just a fallback
    
    # Prioritize center and corners
    priority_moves = [
        (1, 1),  # center
        (0, 0), (0, 2), (2, 0), (2, 2)  # corners
    ]
    
    # Create lists for prioritized available moves
    prioritized_available_moves = [move for move in priority_moves if move in available_moves]

    # If we have prioritized moves, return one of them
    if prioritized_available_moves:
        return random.choice(prioritized_available_moves)
    
    # Otherwise select randomly from available moves
    return random.choice(available_moves)
