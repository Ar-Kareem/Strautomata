
import random
import numpy as np

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Convert to sets for faster lookup
    me_set = set(me)
    opponent_set = set(opponent)
    
    # Board boundaries
    BOARD_SIZE = 19
    
    # Directions for adjacent positions (up, down, left, right)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    def get_adjacent(pos):
        row, col = pos
        adjacent = []
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 1 <= new_row <= BOARD_SIZE and 1 <= new_col <= BOARD_SIZE:
                adjacent.append((new_row, new_col))
        return adjacent
    
    def get_group(pos, visited):
        """Get all positions in the same group as pos"""
        group = set()
        queue = [pos]
        while queue:
            current = queue.pop(0)
            if current in visited or current in me_set or current in opponent_set:
                if current not in visited:
                    visited.add(current)
                    group.add(current)
                    for adj in get_adjacent(current):
                        if adj not in visited:
                            if (adj in me_set and current in me_set) or \
                               (adj in opponent_set and current in opponent_set):
                                queue.append(adj)
        return group
    
    def count_liberties(group, visited):
        """Count liberties of a group"""
        liberties = set()
        for pos in group:
            for adj in get_adjacent(pos):
                if adj not in visited and adj not in me_set and adj not in opponent_set:
                    liberties.add(adj)
        return len(liberties)
    
    def is_suicide(move, player_set):
        """Check if a move would be suicide"""
        if move in me_set or move in opponent_set:
            return True
        # Place the stone temporarily
        temp_set = player_set.copy()
        temp_set.add(move)
        
        # Check if any adjacent groups have 0 liberties
        for adj in get_adjacent(move):
            if adj in (me_set if move in me_set else opponent_set):
                adj_group = get_group(adj, set())
                if count_liberties(adj_group, set()) == 0:
                    # This would be a capture, so it's not suicide
                    return False
        
        # Restore the set
        return False
    
    def would_capture(move, opponent_set):
        """Check if a move captures opponent stones"""
        captured = set()
        for adj in get_adjacent(move):
            if adj in opponent_set:
                adj_group = get_group(adj, set())
                if count_liberties(adj_group, set()) == 1:  # Only one liberty
                    # Is this position the only liberty?
                    liberties = set()
                    for pos in adj_group:
                        for adj_pos in get_adjacent(pos):
                            if adj_pos not in opponent_set:
                                liberties.add(adj_pos)
                    if move in liberties:
                        captured.update(adj_group)
        return captured
    
    # Generate all legal moves
    legal_moves = []
    
    # Check center area for strategic value
    center_positions = []
    center_size = 5  # 5x5 center area
    center_start_row = BOARD_SIZE // 2 - center_size // 2
    center_start_col = BOARD_SIZE // 2 - center_size // 2
    
    for row in range(1, BOARD_SIZE + 1):
        for col in range(1, BOARD_SIZE + 1):
            if (row, col) not in me_set and (row, col) not in opponent_set:
                if not is_suicide((row, col), me_set):
                    legal_moves.append((row, col))
                    
                    # Factor in center control
                    if center_start_row <= row <= center_start_row + center_size - 1 and \
                       center_start_col <= col <= center_start_col + center_size - 1:
                        center_positions.append((row, col))
    
    if not legal_moves:
        return (0, 0)  # Pass if no legal moves
    
    # Check for immediate captures or blocks
    capture_moves = []
    block_moves = []
    tactical_moves = []
    
    for move in legal_moves:
        captured = would_capture(move, opponent_set)
        if captured:
            capture_moves.append((move, len(captured)))
    
    # If any captures available, return one of them
    if capture_moves:
        best_capture = max(capture_moves, key=lambda x: x[1])
        return best_capture[0]
    
    # Sort by center position priority
    def score_move(move):
        row, col = move
        # Prefer center positions
        center_score = 0
        if center_start_row <= row <= center_start_row + center_size - 1 and \
           center_start_col <= col <= center_start_col + center_size - 1:
            center_score = 10
            
        # Prefer corner positions slightly
        corner_score = 0
        if (row in [1, BOARD_SIZE] and col in [1, BOARD_SIZE]):
            corner_score = 2
            
        # Prefer sides (except corners)
        side_score = 0
        if (row in [1, BOARD_SIZE] or col in [1, BOARD_SIZE]) and \
           not (row in [1, BOARD_SIZE] and col in [1, BOARD_SIZE]):
            side_score = 1
            
        # Prefer open positions near own stones if close to existing groups
        open_adjacency = 0
        for adj in get_adjacent(move):
            if adj not in me_set and adj not in opponent_set:
                open_adjacency += 1
        
        return center_score + corner_score + side_score + open_adjacency
    
    # Sort by score
    scored_moves = [(move, score_move(move)) for move in legal_moves]
    scored_moves.sort(key=lambda x: x[1], reverse=True)
    
    # Return the highest scoring move (should be legal)
    return scored_moves[0][0]
