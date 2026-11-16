
import numpy as np
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Initialize memory if first call
    if 'board_state_hashes' not in memory:
        memory['board_state_hashes'] = []
        memory['turn'] = 0
        memory['ko_prevention'] = None
        memory['last_move'] = None
    
    # Convert to set for O(1) lookup
    my_set = set(me)
    opp_set = set(opponent)
    all_stones = my_set | opp_set
    
    # Compute turn number
    memory['turn'] += 1
    turn = memory['turn']
    
    # Generate board state hash for ko detection
    # We'll create a simple hash of the stone positions
    current_hash = hash(frozenset(all_stones))
    if len(memory['board_state_hashes']) > 0 and current_hash == memory['board_state_hashes'][-1]:
        # Avoid immediate repetition (likely illegal), reset if needed
        memory['board_state_hashes'] = []  # Reset on error condition
    memory['board_state_hashes'].append(current_hash)
    
    # Extract board dimensions
    board_size = 19
    board = np.zeros((board_size + 2, board_size + 2), dtype=int)  # +2 for border padding
    
    # Mark stones: 1 = me, -1 = opponent, 0 = empty
    for r, c in me:
        board[r + 1, c + 1] = 1
    for r, c in opponent:
        board[r + 1, c + 1] = -1
    
    # Helper: Get neighbors
    def get_neighbors(r, c):
        return [(r + dr, c + dc) for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]]
    
    # Helper: Get liberties of a group
    def get_liberties(group):
        liberties = set()
        for r, c in group:
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in all_stones:
                    liberties.add((nr, nc))
        return liberties
    
    # Helper: Find connected group (DFS)
    def find_group(start_r, start_c, target_player):
        group = set()
        stack = [(start_r, start_c)]
        visited = set()
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            if board[r + 1, c + 1] == target_player:
                group.add((r, c))
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) not in visited and 1 <= nr <= board_size and 1 <= nc <= board_size:
                        if board[nr + 1, nc + 1] == target_player:
                            stack.append((nr, nc))
        return group
    
    # Helper: Check if a move captures any opponent group
    def is_capture_move(r, c):
        # Place stone temporarily
        board[r + 1, c + 1] = 1
        all_stones.add((r, c))
        
        captured = False
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in opp_set:
                group = find_group(nr, nc, -1)
                if len(get_liberties(group)) == 0:
                    captured = True
                    break
        
        # Revert
        board[r + 1, c + 1] = 0
        all_stones.remove((r, c))
        return captured

    # Helper: Check if a move creates an eye (or near-eye)
    def is_eye_like(r, c):
        # Check if placing here blocks opponent from forming two eyes easily
        # We check if the move surrounds an empty space with at least 3 own stones around
        # and opponent stones are not adjacent in critical positions
        own_adjacent = 0
        opp_adjacent = 0
        empty_adjacent = 0
        neighbors = get_neighbors(r, c)
        for nr, nc in neighbors:
            if (nr, nc) in my_set:
                own_adjacent += 1
            elif (nr, nc) in opp_set:
                opp_adjacent += 1
            else:
                empty_adjacent += 1
        
        # Consider eye potential: surrounded by 3+ own stones and 0-1 opponent
        if own_adjacent >= 3 and opp_adjacent <= 1 and empty_adjacent <= 1:
            return True
        
        # Also check if this is a "false eye" - i.e., opponent can't easily remove it
        # A simple heuristic: if all adjacent empty points are surrounded by own stones, it's good
        if empty_adjacent == 0 and own_adjacent >= 4:
            return True
            
        return False
    
    # Helper: Check if move is legal (not suicidal)
    def is_legal_move(r, c):
        if (r, c) in all_stones:
            return False
        # Place stone
        board[r + 1, c + 1] = 1
        all_stones.add((r, c))
        # Check if own group has liberties
        own_group = find_group(r, c, 1)
        if len(get_liberties(own_group)) == 0:
            # Check if it captures opponent group - then it's legal
            captured = False
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in opp_set:
                    group = find_group(nr, nc, -1)
                    if len(get_liberties(group)) == 0:
                        captured = True
                        break
            # If it doesn't capture and has no liberties, it's suicidal
            if not captured:
                board[r + 1, c + 1] = 0
                all_stones.remove((r, c))
                return False
        # Revert
        board[r + 1, c + 1] = 0
        all_stones.remove((r, c))
        return True
    
    # Helper: Compute influence/territory score for a move
    def evaluate_move(r, c):
        # Base values
        score = 0
        
        # Center bias: center of board is more valuable
        center_score = -abs(r - 10) - abs(c - 10)
        score += center_score * 0.3
        
        # Corner bias
        if (r, c) in [(1, 1), (1, 19), (19, 1), (19, 19)]:
            score += 10
        elif (r, c) in [(1, 3), (3, 1), (1, 17), (3, 19), (17, 1), (19, 3), (17, 19), (19, 17)]:
            score += 8
        elif (r, c) in [(1, 10), (10, 1), (19, 10), (10, 19)]:
            score += 6
        
        # Proximity to own stones
        own_adjacent = sum(1 for nr, nc in get_neighbors(r, c) if (nr, nc) in my_set)
        opp_adjacent = sum(1 for nr, nc in get_neighbors(r, c) if (nr, nc) in opp_set)
        
        score += own_adjacent * 2.5
        score -= opp_adjacent * 1.5
        
        # Is this move a capture?
        if is_capture_move(r, c):
            score += 20  # High value for capturing
        
        # Is this move an eye?
        if is_eye_like(r, c):
            score += 15
            
        # Prevent opponent from living
        # Try to see if this move blocks an opponent group from making eyes
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in opp_set:
                group = find_group(nr, nc, -1)
                opp_liberties = get_liberties(group)
                if len(opp_liberties) == 1:
                    # Opponent in atari, placing here might capture
                    pass  # Already handled by is_capture_move
                elif len(opp_liberties) == 2:
                    # Two liberties: placing here reduces to one, which is valuable
                    if (r, c) in opp_liberties:
                        score += 8
        
        # Avoid suicide
        if not is_legal_move(r, c):
            score = -10000  # Invalid
        
        # Try to connect own groups
        connected_groups = 0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in my_set:
                # Check if this connects two separate groups
                # We do a simple check: if two neighbor stones are both own but not connected, this connects them
                # Simple heuristic: if multiple own neighbors that are in different groups, score extra
                pass  # This is complex to compute without full group analysis
        
        # Simple connection bonus
        if own_adjacent >= 2:
            score += 3
        
        return score

    # Generate all empty positions
    empty_positions = []
    for r in range(1, board_size + 1):
        for c in range(1, board_size + 1):
            if (r, c) not in all_stones:
                empty_positions.append((r, c))
    
    # Filter only legal moves
    legal_moves = [pos for pos in empty_positions if is_legal_move(*pos)]
    
    # Check for passes
    # We only pass if no legal moves or it's a forced situation
    # But Go rules: we can pass anytime. But we prefer to play unless completely dead
    if len(legal_moves) == 0:
        return ((0, 0), memory)
    
    # Check if opponent is in atari and we can capture immediately
    for move in legal_moves:
        if is_capture_move(*move):
            return (move, memory)
    
    # Evaluate all legal moves
    move_scores = []
    for move in legal_moves:
        score = evaluate_move(*move)
        move_scores.append((move, score))
    
    # Sort by score descending
    move_scores.sort(key=lambda x: x[1], reverse=True)
    
    # If we're in opening phase, avoid symmetry violations
    if turn < 10:
        # Prefer moves in corners
        corner_moves = [m for m in move_scores if m[0] in [(1,1), (1,19), (19,1), (19,19), (1,3), (3,1), (1,17), (3,19), (17,1), (19,3), (17,19), (19,17)]]
        if corner_moves:
            best_move = corner_moves[0][0]
            return (best_move, memory)
    
    # Pick the highest scoring move
    best_move = move_scores[0][0]
    
    # Simple check for ko: if last move was opponent's and we're trying to recapture, check previous state
    # We don't track full state, so we assume the memory will prevent repeating the exact same board.
    # This is a simplification.

    return (best_move, memory)
