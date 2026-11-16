
import random

def policy(board: list[list[int]], legal_moves: list[int]) -> tuple[int, int]:
    """
    Phantom Tic Tac Toe Policy.
    board: 3x3 list. 1 = mine, 0 = unknown (empty or opponent).
    legal_moves: list of flat indices (0-8) currently allowed to be attempted.
    """
    
    # Convert flat index to 2D
    def to_rc(idx):
        return idx // 3, idx % 3

    # Check for potential winning moves (where we have two '1's in a line)
    # Even though we don't know if the 3rd spot is empty, it's the best spot to try.
    lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8], # Cols
        [0, 4, 8], [2, 4, 6]             # Diags
    ]
    
    # Priority 1: Complete a line of our own colors
    for line in lines:
        marks = [board[to_rc(i)[0]][to_rc(i)[1]] for i in line]
        if sum(marks) == 2:
            for i in line:
                if i in legal_moves and board[to_rc(i)[0]][to_rc(i)[1]] == 0:
                    return to_rc(i)

    # Priority 2: Strategic Positioning Weights
    # Center is strongest, then corners, then edges
    weights = {
        4: 10,  # Center
        0: 5, 2: 5, 6: 5, 8: 5, # Corners
        1: 2, 3: 2, 5: 2, 7: 2  # Edges
    }
    
    # Filter legal moves that we haven't already captured
    candidates = [m for m in legal_moves if board[to_rc(m)[0]][to_rc(m)[1]] == 0]
    
    if not candidates:
        # Fallback to any legal move if logic fails
        return to_rc(random.choice(legal_moves))
    
    # Sort candidates by weights
    candidates.sort(key=lambda x: weights.get(x, 0), reverse=True)
    
    # Return the highest weight move (or random of the highest weights)
    best_weight = weights.get(candidates[0], 0)
    best_moves = [m for m in candidates if weights.get(m, 0) == best_weight]
    
    return to_rc(random.choice(best_moves))
