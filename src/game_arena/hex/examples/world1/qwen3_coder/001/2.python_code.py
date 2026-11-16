
import random
from typing import List, Tuple, Set

def get_neighbors(r: int, c: int) -> List[Tuple[int, int]]:
    """Returns the 6 neighbors of a hex cell (r, c) on an 11x11 board"""
    neighbors = [
        (r-1, c), (r+1, c),    # left and right
        (r, c-1), (r, c+1),    # top-left and bottom-right
        (r-1, c-1), (r+1, c+1) # top-right and bottom-left
    ]
    return [(i, j) for i, j in neighbors if 0 <= i < 11 and 0 <= j < 11]

def is_winning_move(move: Tuple[int, int], player_stones: Set[Tuple[int, int]], color: str) -> bool:
    """Check if a move leads to a win using a simplified path-check"""
    # This is an approximation; a full implementation would use BFS/DFS
    # to determine if a path exists. For efficiency, we only check for immediate win conditions
    # near the move based on color objective
    r, c = move
    
    if color == 'b':  # Black connects top to bottom
        # Check if this move bridges top and bottom sides
        if r == 0 and any((10, j) in player_stones for j in range(11)):
            return True
        if r == 10 and any((0, j) in player_stones for j in range(11)):
            return True
    elif color == 'w':  # White connects left to right
        if c == 0 and any((i, 10) in player_stones for i in range(11)):
            return True
        if c == 10 and any((i, 0) in player_stones for i in range(11)):
            return True
    
    return False

def find_winning_move(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    """Find a winning move if it exists"""
    me_set = set(me)
    opp_set = set(opp)
    all_occupied = me_set | opp_set
    empty_cells = [(i, j) for i in range(11) for j in range(11) if (i, j) not in all_occupied]
    
    for move in empty_cells:
        if is_winning_move(move, me_set, color):
            return move
    return None

def find_blocking_move(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    """Block opponent's potential win"""
    me_set = set(me)
    opp_set = set(opp)
    all_occupied = me_set | opp_set
    empty_cells = [(i, j) for i in range(11) for j in range(11) if (i, j) not in all_occupied]
    
    for move in empty_cells:
        if is_winning_move(move, opp_set, 'b' if color == 'w' else 'w'):
            return move
    return None

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    """Main policy function"""
    me_set = set(me)
    opp_set = set(opp)
    all_occupied = me_set | opp_set
    empty_cells = [(i, j) for i in range(11) for j in range(11) if (i, j) not in all_occupied]
    
    if not empty_cells:
        # Should never happen, but just in case
        return (5, 5)
    
    # 1. Check for winning move
    winning_move = find_winning_move(me, opp, color)
    if winning_move:
        return winning_move
    
    # 2. Block opponent's winning move
    blocking_move = find_blocking_move(me, opp, color)
    if blocking_move:
        return blocking_move
    
    # 3. Try to place a stone that connects to our existing stones
    if me:
        my_last_move = me[-1]
        neighbors_of_mine = get_neighbors(my_last_move[0], my_last_move[1])
        valid_neighbors = [n for n in neighbors_of_mine if n in empty_cells]
        if valid_neighbors:
            return random.choice(valid_neighbors)
    
    # 4. Fallback to a strategic move (e.g., near center)
    center_moves = [(5, 5), (5, 6), (6, 5), (6, 6)]
    for move in center_moves:
        if move in empty_cells:
            return move
    
    # 5. Choose a random empty cell
    return random.choice(empty_cells)
