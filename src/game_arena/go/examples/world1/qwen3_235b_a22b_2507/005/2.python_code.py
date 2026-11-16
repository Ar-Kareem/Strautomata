
import numpy as np
from typing import List, Tuple, Set

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Convert lists to sets for faster lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    
    # Create board representation (1-indexed, 19x19)
    board = np.zeros((20, 20), dtype=int)  # 0=empty, 1=me, 2=opponent
    for r, c in my_stones:
        board[r, c] = 1
    for r, c in opp_stones:
        board[r, c] = 2
    
    def get_neighbors(r, c):
        # Returns valid neighbors on the 19x19 board
        neighbors = []
        for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                neighbors.append((nr, nc))
        return neighbors
    
    def get_group(r, c, player_id):
        # Returns the group of stones connected to (r,c) of player_id
        if board[r, c] != player_id:
            return set()
        group = set()
        visited = set()
        stack = [(r, c)]
        while stack:
            pos = stack.pop()
            if pos in visited:
                continue
            visited.add(pos)
            if board[pos[0], pos[1]] == player_id:
                group.add(pos)
                for nb in get_neighbors(*pos):
                    if board[nb[0], nb[1]] == player_id and nb not in visited:
                        stack.append(nb)
        return group
    
    def get_liberties(group):
        # Returns the number of empty adjacent points to the group
        libs = set()
        for r, c in group:
            for nr, nc in get_neighbors(r, c):
                if board[nr, nc] == 0:
                    libs.add((nr, nc))
        return libs
    
    def is_legal_move(r, c):
        # Check if the move is within bounds and empty
        if not (1 <= r <= 19 and 1 <= c <= 19):
            return False
        if board[r, c] != 0:
            return False
        
        # Simulate placing the stone
        board[r, c] = 1
        my_group = get_group(r, c, 1)
        liberties = get_liberties(my_group)
        
        # If the group has no liberties, check if it captures any opponent group
        if len(liberties) == 0:
            # Will this move capture any opponent group?
            captures = 0
            for nr, nc in get_neighbors(r, c):
                if board[nr, nc] == 2:
                    opp_group = get_group(nr, nc, 2)
                    opp_libs = get_liberties(opp_group)
                    if len(opp_libs) == 1 and (r, c) in opp_libs:
                        captures += len(opp_group)
            board[r, c] = 0
            if captures > 0:
                return True  # It's legal because it captures
            else:
                return False  # Suicide move
        else:
            board[r, c] = 0
            return True
    
    def compute_score(r, c):
        # Higher score is better
        score = 0
        
        # Bonus for capturing
        captures = 0
        for nr, nc in get_neighbors(r, c):
            if board[nr, nc] == 2:
                opp_group = get_group(nr, nc, 2)
                opp_libs = get_liberties(opp_group)
                if len(opp_libs) == 1 and (r, c) in opp_libs:
                    captures += len(opp_group) * 10
        score += captures
        
        # Simulate move
        board[r, c] = 1
        my_group = get_group(r, c, 1)
        my_libs = get_liberties(my_group)
        score += len(my_libs) * 0.1  # Small bonus for more liberties
        
        # Remove own liberties if connected to existing groups
        if len(my_group) > 1:
            score += 0.2  # Small bonus for connecting
        
        # Territorial influence - prefer center
        center_score = 10 - np.abs(np.array([r, c]) - 10).sum()
        score += center_score * 0.05
        
        board[r, c] = 0
        return score
    
    # First, check for any immediate captures
    capture_moves = []
    for r in range(1, 20):
        for c in range(1, 20):
            if board[r, c] != 0:
                continue
            for nr, nc in get_neighbors(r, c):
                if board[nr, nc] == 2:
                    opp_group = get_group(nr, nc, 2)
                    opp_libs = get_liberties(opp_group)
                    if len(opp_libs) == 1 and (r, c) in opp_libs:
                        if is_legal_move(r, c):
                            capture_moves.append((r, c))
            if capture_moves:
                break
        if capture_moves:
            break
    
    if capture_moves:
        # Among capture moves, pick the one that captures the most
        best_capture = max(capture_moves, key=lambda move: sum(
            len(get_group(nr, nc, 2)) 
            for nr, nc in get_neighbors(*move) 
            if board[nr, nc] == 2 and len(get_liberties(get_group(nr, nc, 2))) == 1 and (move[0], move[1]) in get_liberties(get_group(nr, nc, 2))
        ))
        return best_capture
    
    # Otherwise, evaluate all legal moves
    legal_moves = []
    for r in range(1, 20):
        for c in range(1, 20):
            if is_legal_move(r, c):
                legal_moves.append((r, c))
    
    # If no legal moves (board full), pass
    if not legal_moves:
        return (0, 0)
    
    # Score all legal moves
    scored_moves = [(move, compute_score(*move)) for move in legal_moves]
    best_move = max(scored_moves, key=lambda x: x[1])[0]
    
    return best_move
