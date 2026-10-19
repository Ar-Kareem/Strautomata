
import numpy as np
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Initialize board state
    board = np.zeros((19, 19), dtype=int)
    
    # Mark stones on board
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = 2
    
    # Helper to get neighboring positions
    def neighbors(r, c):
        return [(r+dr, c+dc) for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)] 
                if 0 <= r+dr < 19 and 0 <= c+dc < 19]
    
    # Helper to get liberties of a group
    def liberties(group):
        lib = set()
        for r, c in group:
            for nr, nc in neighbors(r, c):
                if board[nr, nc] == 0:
                    lib.add((nr, nc))
        return lib
    
    # Helper to find connected groups
    def find_groups():
        visited = set()
        groups = []
        
        for r in range(19):
            for c in range(19):
                if board[r, c] != 0 and (r, c) not in visited:
                    color = board[r, c]
                    stack = [(r, c)]
                    group = []
                    
                    while stack:
                        cr, cc = stack.pop()
                        if (cr, cc) in visited:
                            continue
                        visited.add((cr, cc))
                        group.append((cr, cc))
                        
                        for nr, nc in neighbors(cr, cc):
                            if board[nr, nc] == color and (nr, nc) not in visited:
                                stack.append((nr, nc))
                    
                    groups.append((color, group))
        
        return groups
    
    # Helper to evaluate move score
    def evaluate_move(r, c):
        if board[r, c] != 0:
            return -1000  # Invalid move
        
        # Check if move captures opponent stones
        capture_score = 0
        for nr, nc in neighbors(r, c):
            if board[nr, nc] == 2:  # Opponent stone
                # Check if this stone is part of a group with only one liberty
                stack = [(nr, nc)]
                visited = set()
                group = []
                
                while stack:
                    cr, cc = stack.pop()
                    if (cr, cc) in visited:
                        continue
                    visited.add((cr, cc))
                    group.append((cr, cc))
                    
                    for nnr, nnc in neighbors(cr, cc):
                        if board[nnr, nnc] == 2 and (nnr, nnc) not in visited:
                            stack.append((nnr, nnc))
                
                # Check liberties of this group
                libs = liberties(group)
                if len(libs) == 1:  # Only one liberty left
                    capture_score += len(group) * 10
        
        # Check if move saves own stones
        save_score = 0
        for nr, nc in neighbors(r, c):
            if board[nr, nc] == 1:  # Own stone
                stack = [(nr, nc)]
                visited = set()
                group = []
                
                while stack:
                    cr, cc = stack.pop()
                    if (cr, cc) in visited:
                        continue
                    visited.add((cr, cc))
                    group.append((cr, cc))
                    
                    for nnr, nnc in neighbors(cr, cc):
                        if board[nnr, nnc] == 1 and (nnr, nnc) not in visited:
                            stack.append((nnr, nnc))
                
                libs = liberties(group)
                if len(libs) == 1:
                    save_score += len(group) * 5
        
        # Check if move creates eye or territory
        eye_score = 0
        own_neighbors = sum(1 for nr, nc in neighbors(r, c) if board[nr, nc] == 1)
        if own_neighbors >= 2:
            eye_score += 3
        
        # Check if move is at strategic points (corners, sides)
        strategic_score = 0
        if (r in [0, 18] or c in [0, 18]):
            strategic_score += 1
        if (r in [3, 15] or c in [3, 15]):
            strategic_score += 2
        
        return capture_score + save_score + eye_score + strategic_score
    
    # Find the best move
    best_score = -1000
    best_move = (0, 0)
    
    # Try all possible moves
    for r in range(19):
        for c in range(19):
            score = evaluate_move(r, c)
            if score > best_score:
                best_score = score
                best_move = (r+1, c+1)  # Convert to 1-based indexing
    
    return best_move, memory
