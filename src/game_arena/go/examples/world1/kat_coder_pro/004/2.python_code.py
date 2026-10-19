
import copy
import random
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    A simple rule-based policy for Go.
    """
    # Convert lists to sets for faster lookups
    me_set = set(me)
    opponent_set = set(opponent)
    all_stones = me_set | opponent_set
    
    # Define board size
    N = 19
    
    # Helper to check if a position is on the board
    def is_on_board(r, c):
        return 1 <= r <= N and 1 <= c <= N
    
    # Helper to get neighbors
    def get_neighbors(r, c):
        return [(r+1, c), (r-1, c), (r, c+1), (r, c-1)]
    
    # Helper to get liberties of a group
    def get_liberties(group, board):
        liberties = set()
        for r, c in group:
            for nr, nc in get_neighbors(r, c):
                if is_on_board(nr, nc) and (nr, nc) not in board:
                    liberties.add((nr, nc))
        return liberties
    
    # Helper to find a group containing stone
    def find_group(r, c, board):
        color = (r, c) in me_set
        if not color and (r, c) not in opponent_set:
            return set()
        
        stack = [(r, c)]
        group = set()
        visited = set()
        
        while stack:
            curr = stack.pop()
            if curr in visited:
                continue
            visited.add(curr)
            
            # Only add stones of the same color
            if color and curr in me_set:
                group.add(curr)
                for nr, nc in get_neighbors(*curr):
                    if is_on_board(nr, nc) and (nr, nc) in me_set and (nr, nc) not in visited:
                        stack.append((nr, nc))
            elif not color and curr in opponent_set:
                group.add(curr)
                for nr, nc in get_neighbors(*curr):
                    if is_on_board(nr, nc) and (nr, nc) in opponent_set and (nr, nc) not in visited:
                        stack.append((nr, nc))
        return group
    
    # Helper to check if a move is legal (no suicide rule enforced)
    def is_legal(r, c, board):
        if not is_on_board(r, c) or (r, c) in board:
            return False
        
        # Temporarily add the stone
        temp_board = board.copy()
        temp_board.add((r, c))
        
        # Check for suicide
        liberties = get_liberties([(r, c)], temp_board)
        if not liberties:
            # Check if we capture any opponent stones
            opponent_neighbors = []
            for nr, nc in get_neighbors(r, c):
                if is_on_board(nr, nc) and (nr, nc) in opponent_set:
                    opponent_neighbors.append((nr, nc))
            
            captures = 0
            for nr, nc in opponent_neighbors:
                group = find_group(nr, nc, temp_board)
                if group and not get_liberties(group, temp_board):
                    captures += len(group)
            
            if captures == 0:
                return False  # Suicide
        
        return True
    
    # List of all legal moves
    legal_moves = []
    for r in range(1, N+1):
        for c in range(1, N+1):
            if is_legal(r, c, all_stones):
                legal_moves.append((r, c))
    
    if not legal_moves:
        return (0, 0)  # Pass
    
    # Strategy:
    # 1. Try to capture opponent stones
    # 2. Try to connect to your own stones
    # 3. Try to play on the edge or center
    # 4. Random fallback
    
    scores = defaultdict(float)
    
    for move in legal_moves:
        r, c = move
        
        # Check captures
        temp_board = all_stones.copy()
        temp_board.add((r, c))
        captures = 0
        for nr, nc in get_neighbors(r, c):
            if is_on_board(nr, nc) and (nr, nc) in opponent_set:
                group = find_group(nr, nc, temp_board)
                if group and not get_liberties(group, temp_board):
                    captures += len(group)
        scores[move] += captures * 10
        
        # Check connectivity to own stones
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in me_set:
                scores[move] += 1
        
        # Prefer center and edges
        dist_to_center = abs(r - 10) + abs(c - 10)
        scores[move] += max(0, (9 - dist_to_center) * 0.1)
    
    # Pick the best move
    best_moves = [move for move in legal_moves if scores[move] == max(scores.values())]
    return random.choice(best_moves)
