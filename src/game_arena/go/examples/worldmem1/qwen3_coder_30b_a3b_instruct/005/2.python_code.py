
import random
import numpy as np
from collections import deque, defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Convert to sets for easier handling
    me_set = set(me)
    opponent_set = set(opponent)
    
    # Initialize board state
    board_size = 19
    board = [[0 for _ in range(board_size)] for _ in range(board_size)]
    
    # Mark stones on board
    for r, c in me_set:
        board[r-1][c-1] = 1  # Own stone
    for r, c in opponent_set:
        board[r-1][c-1] = 2  # Opponent stone
        
    # Function to get adjacent positions
    def get_adjacent(pos):
        r, c = pos
        adjacent = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < board_size and 0 <= nc < board_size:
                adjacent.append((nr, nc))
        return adjacent
    
    # Function to check if position is empty
    def is_empty(pos):
        r, c = pos
        return board[r][c] == 0
    
    # Function to get all liberties of a group
    def get_liberties(group):
        liberties = set()
        for r, c in group:
            for nr, nc in get_adjacent((r, c)):
                if board[nr][nc] == 0:
                    liberties.add((nr, nc))
        return liberties
    
    # Function to find a group of connected stones
    def find_group(pos):
        if board[pos[0]][pos[1]] == 0:
            return set()
        
        queue = deque([pos])
        visited = set([pos])
        group = set([pos])
        color = board[pos[0]][pos[1]]
        
        while queue:
            r, c = queue.popleft()
            for nr, nc in get_adjacent((r, c)):
                if (nr, nc) not in visited and board[nr][nc] == color:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
                    group.add((nr, nc))
        return group
    
    # Function to check if a move is legal
    def is_legal_move(pos, me_set, opponent_set):
        if not is_empty(pos):
            return False
            
        # Check for suicide
        r, c = pos
        board_copy = [row[:] for row in board]
        board_copy[r][c] = 1  # Place our stone
        
        # Check if any of the adjacent opponent groups are captured
        for nr, nc in get_adjacent((r, c)):
            if board_copy[nr][nc] == 2:  # Opponent stone
                group = find_group((nr, nc))
                if not get_liberties(group):
                    # Check if placing stone would capture this group
                    if len(group) == 1:  # Just one stone
                        return True  # Capture
                    # If it's more than one stone, it's valid move, not suicide
        
        # Check if the placed stone has liberties or captures
        own_group = find_group((r, c))
        if own_group:
            if get_liberties(own_group):
                return True
        
        # If the move doesn't immediately capture and doesn't have liberties,
        # it must capture opponent stones to be legal
        temp_me = me_set.copy()
        temp_me.add(pos)
        
        # Check if placing this stone reduces liberties of opponent groups to 0
        for nr, nc in get_adjacent((r, c)):
            if board[nr][nc] == 2:  # Opponent stone
                group = find_group((nr, nc))
                if not get_liberties(group):
                    if len(group) >= 1:  # Capture valid
                        return True
                        
        return True  # All other moves are legal
        
    # Function to count liberties for a group
    def liberties_count(group):
        liberties = set()
        for r, c in group:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < board_size and 0 <= nc < board_size and board[nr][nc] == 0:
                    liberties.add((nr, nc))
        return len(liberties)
    
    # Function to calculate the score for a position
    def evaluate_position(pos):
        r, c = pos
        score = 0
        
        # Prefer corners
        if (r in [0, 18] and c in [0, 18]):
            score += 5
        
        # Prefer sides (but not corners)
        elif (r in [0, 18] or c in [0, 18]):
            score += 3
            
        # Prefer center (but less than edges)
        elif (r in [9, 10] and c in [9, 10]):
            score += 1
            
        # Bonus for nearby friendly stones
        nearby_friend = 0
        for nr, nc in get_adjacent((r, c)):
            if (nr, nc) in me_set:
                nearby_friend += 1
                score += 1
                
        # Penalty for potentially surrounded position
        nearby_opp = 0
        for nr, nc in get_adjacent((r, c)):
            if (nr, nc) in opponent_set:
                nearby_opp += 1
                score -= 0.5
                
        # Bonus for nearby liberties
        liberties = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < board_size and 0 <= nc < board_size and board[nr][nc] == 0:
                liberties += 1
        score += liberties * 0.3
        
        return score
    
    # Check for immediate captures and prevent captures
    # Look around our current stones for positions that could capture
    capture_moves = []
    prevent_capture = []
    
    # Look for captures
    for r, c in me_set:
        for nr, nc in get_adjacent((r, c)):
            # If adjacent empty and opponent stone in the same line, check if we can capture
            if board[nr][nc] == 0:
                # Look at opponent groups that are adjacent to this empty spot
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    orn, onc = nr + dr, nc + dc
                    if 0 <= orn < board_size and 0 <= onc < board_size and board[orn][onc] == 2:
                        group = find_group((orn, onc))
                        liberties = get_liberties(group)
                        if len(liberties) == 1 and list(liberties)[0] == (nr, nc):
                            # This is an atari situation - we can capture
                            capture_moves.append((nr, nc))
    
    # Look for moves to prevent captures
    for r, c in opponent_set:
        for nr, nc in get_adjacent((r, c)):
            if board[nr][nc] == 0:
                # Check if we can block a capture of our group
                # Find our neighboring groups
                our_groups = []
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    orn, onc = nr + dr, nc + dc
                    if 0 <= orn < board_size and 0 <= onc < board_size and board[orn][onc] == 1:
                        group = find_group((orn, onc))
                        liberties = get_liberties(group)
                        if len(liberties) <= 2:  # Can be easily captured
                            prevent_capture.append((nr, nc))
    
    # Prefer moves that prevent capture
    if prevent_capture:
        # Try to pick the best prevent capture move based on eval score
        best_move = max(prevent_capture, key=evaluate_position)
        return (best_move[0]+1, best_move[1]+1), memory
    
    # If capture moves exist, prefer capturing
    if capture_moves:
        # Try to pick capture move that's best
        best_move = max(capture_moves, key=evaluate_position)
        return (best_move[0]+1, best_move[1]+1), memory
    
    # Build all legal moves
    legal_moves = []
    
    # Prioritize center positions
    center_priority = []
    middle_positions = []
    
    for r in range(board_size):
        for c in range(board_size):
            if board[r][c] == 0:  # Empty spot
                if is_legal_move((r, c), me_set, opponent_set):
                    legal_moves.append((r, c))
                    # If it's near center, add to center list
                    if abs(r - 9) <= 2 and abs(c - 9) <= 2:
                        middle_positions.append((r, c))

    # If there are no legal moves, pass
    if not legal_moves:
        return (0, 0), memory
    
    # If very few moves, just pick one
    if len(legal_moves) <= 5:
        return (legal_moves[0][0]+1, legal_moves[0][1]+1), memory
    
    # Prioritize center and corners first
    if middle_positions:
        # Sort by eval score
        sorted_middle = sorted(middle_positions, key=evaluate_position, reverse=True)
        # Try these first
        for pos in sorted_middle:
            if pos in legal_moves:
                return (pos[0]+1, pos[1]+1), memory
    
    # Fallback to evaluation scoring
    best_move = max(legal_moves, key=evaluate_position)
    return (best_move[0]+1, best_move[1]+1), memory
