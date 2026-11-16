
import numpy as np
import random
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Initialize memory if empty
    if not memory:
        memory = {
            'move_count': 0,
            'last_moves': [],
            'board_size': 19
        }
    
    board_size = memory['board_size']
    memory['move_count'] += 1
    move_count = memory['move_count']
    
    # Convert positions to sets for faster lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_stones = my_stones.union(opp_stones)
    
    def is_valid_move(row, col):
        # Check if move is on empty space
        if (row, col) in all_stones:
            return False
        
        # Check boundaries
        if row < 1 or row > board_size or col < 1 or col > board_size:
            return False
            
        # For now, skip complicated suicide rule checking
        # (This is a simplification - proper implementation would need group checks)
        return True
    
    # Try to find capturing moves first
    for (r, c) in opponent:
        for (dr, dc) in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            if is_valid_move(nr, nc):
                # Simulate the move and see if we capture
                temp_opp = opp_stones - {(r, c)}
                # Count liberties of opponent stone
                lib_count = 0
                for (or_, oc) in temp_opp:
                    for (odr, odc) in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nor, noc = or_ + odr, oc + odc
                        if (nor, noc) not in all_stones and 1 <= nor <= board_size and 1 <= noc <= board_size:
                            lib_count += 1
                            break
                if lib_count == 0:
                    return ((nr, nc), memory)
    
    # Try to find expansion moves near our existing stones
    if len(my_stones) > 0:
        candidates = set()
        for (r, c) in my_stones:
            for (dr, dc) in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r + dr, c + dc
                if is_valid_move(nr, nc):
                    candidates.add((nr, nc))
        
        if candidates:
            # Prioritize center if early game
            if move_count < 20:
                best_move = None
                best_score = -1
                for (r, c) in candidates:
                    center_dist = abs(r - (board_size+1)/2) + abs(c - (board_size+1)/2)
                    score = (board_size*2) - center_dist  # Higher for more central
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)
                return (best_move, memory)
            else:
                return (random.choice(list(candidates)), memory)
    
    # Fallback: find any valid move, preferring center
    if move_count < 10:
        # Start with standard opening moves for 19x19
        open_positions = [
            (4, 4), (4, 16), (16, 4), (16, 16),  # Corners
            (4, 10), (10, 4), (10, 16), (16, 10),  # Side stars
            (10, 10)  # Center
        ]
        for pos in open_positions:
            if is_valid_move(*pos):
                return (pos, memory)
    
    # Last resort: random valid move
    valid_moves = []
    for r in range(1, board_size+1):
        for c in range(1, board_size+1):
            if is_valid_move(r, c):
                valid_moves.append((r, c))
    
    if valid_moves:
        return (random.choice(valid_moves), memory)
    
    # No valid moves left, pass
    return ((0, 0), memory)
