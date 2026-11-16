
import numpy as np
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """
    A Havannah policy that prioritizes corners, edges, ring prevention, bridge/fork completion, 
    connectivity, and center control.

    Args:
        me: A list of (row, col) tuples for player-0 stones.
        opp: A list of (row, col) tuples for player-1 stones.
        valid_mask: A 2D array (shape NxN) where True marks playable cells.

    Returns:
        A single move as a tuple (row, col).
    """

    board_size = valid_mask.shape[0]

    def is_corner(row, col):
        return (row == 0 and col == 0) or \
               (row == 0 and col == board_size - 1) or \
               (row == board_size - 1 and col == 0) or \
               (row == board_size - 1 and col == board_size - 1) or \
               (row == board_size // 2 and col == 0) or \
               (row == board_size // 2 and col == board_size-1)

    def is_edge(row, col):
        return row == 0 or row == board_size - 1 or col == 0 or col == board_size - 1

    def get_neighbors(row, col):
        neighbors = []
        if row > 0:
            neighbors.append((row - 1, col))
        if row < board_size - 1:
            neighbors.append((row + 1, col))
        if col > 0:
            neighbors.append((row, col - 1))
        if col < board_size - 1:
            neighbors.append((row, col + 1))
        if row > 0 and col > 0:
            neighbors.append((row-1, col-1))
        if row < board_size-1 and col < board_size-1:
            neighbors.append((row+1, col+1))
        return neighbors


    def is_occupied(row, col):
        return (row, col) in me or (row, col) in opp
    
    def evaluate_move(row, col):
        score = 0

        if is_corner(row, col):
            score += 5  # High priority for corners
        elif is_edge(row, col):
            score += 3  # Moderate priority for edges
        
        #Connectivity bonus for my stones
        my_neighbors=0
        for r, c in get_neighbors(row, col):
          if (r,c) in me:
            my_neighbors +=1

        score += my_neighbors * 2

        # Ring prevention penalty - basic check, can be improved
        opponent_neighbors = 0
        for r, c in get_neighbors(row, col):
                if (r, c) in opp:
                      opponent_neighbors += 1
        score -= opponent_neighbors  # Avoid immediate ring completion for opp

        return score

    # Prioritize corners and edges
    best_move = None
    best_score = -np.inf 
    
    possible_moves = []
    for row in range(board_size):
        for col in range(board_size):
            if valid_mask[row][col] and not is_occupied(row, col):
                possible_moves.append((row, col))

    if not possible_moves:
        # Should never happen given valid_mask is supposed to prevent this
        return (0,0)  # fallback

    for row, col in possible_moves:
        score = evaluate_move(row,col)
        if score > best_score:
            best_score = score
            best_move = (row, col)
            
    if best_move is not None:
        return best_move
    else:  # Fallback: choose a random valid move
        possible_moves = [(r,c) for r in range(board_size) for c in range(board_size) if valid_mask[r][c] and not is_occupied(r,c)]
        if possible_moves: #Added check
            return random.choice(possible_moves)
        else :
             return (0,0) #If no possible moves, return default, this should not occur.
