
import numpy as np
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Initialize board state
    board = np.zeros((21, 21))  # 1-indexed with padding
    for r, c in me:
        board[r, c] = 1
    for r, c in opponent:
        board[r, c] = 2
    
    # Helper functions
    def get_neighbors(r, c):
        return [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
    
    def is_on_board(r, c):
        return 1 <= r <= 19 and 1 <= c <= 19
    
    def has_liberties(r, c, player_board):
        # Simple liberty check
        for nr, nc in get_neighbors(r, c):
            if is_on_board(nr, nc) and player_board[nr, nc] == 0:
                return True
        return False
    
    def would_be_capture(r, c):
        # Check if playing here captures opponent stones
        if not is_on_board(r, c) or board[r, c] != 0:
            return False
            
        # Temporarily place our stone
        board[r, c] = 1
        captured = False
        
        # Check opponent neighbors
        for nr, nc in get_neighbors(r, c):
            if is_on_board(nr, nc) and board[nr, nc] == 2:
                if not has_liberties(nr, nc, board):
                    captured = True
                    break
                    
        board[r, c] = 0  # Undo placement
        return captured
    
    def is_legal(r, c):
        # Basic legality checks
        if not is_on_board(r, c):
            return False
        if board[r, c] != 0:
            return False
        
        # Would be capture is always legal
        if would_be_capture(r, c):
            return True
            
        # Not a capture - check if we'd have liberties
        board[r, c] = 1
        has_our_libs = has_liberties(r, c, board)
        board[r, c] = 0
        
        return has_our_libs
    
    def evaluate_position(r, c):
        # Simple heuristic evaluation
        if not is_legal(r, c):
            return -1000
            
        score = 0
        
        # Prefer positions closer to corners initially
        dist_to_corners = min([
            abs(r-4) + abs(c-4),
            abs(r-4) + abs(c-16),
            abs(r-16) + abs(c-4),
            abs(r-16) + abs(c-16)
        ])
        score += max(0, 10 - dist_to_corners)
        
        # Bonus for positions that create influence
        neighbor_count = 0
        for nr, nc in get_neighbors(r, c):
            if is_on_board(nr, nc):
                if board[nr, nc] == 1:  # Our stone
                    neighbor_count += 2
                elif board[nr, nc] == 2:  # Opponent stone
                    neighbor_count -= 1
                    
        score += neighbor_count * 3
        
        # Bonus for capturing moves
        if would_be_capture(r, c):
            score += 15
            
        # Prefer central control in middle game
        center_dist = abs(r-10) + abs(c-10)
        score += max(0, 5 - center_dist//3)
        
        return score
    
    # Generate candidate moves
    best_move = (0, 0)  # Pass by default
    best_score = -10000
    
    # First check if any opponent group is in atari - prioritize captures
    for r, c in opponent:
        if board[r, c] == 2:  # For each opponent stone
            # Check its liberties
            liberties = []
            for nr, nc in get_neighbors(r, c):
                if is_on_board(nr, nc) and board[nr, nc] == 0:
                    liberties.append((nr, nc))
            
            # If exactly one liberty, we might be able to capture
            if len(liberties) == 1:
                lr, lc = liberties[0]
                if is_legal(lr, lc):
                    return ((lr, lc), memory)
    
    # Evaluate positions in priority order:
    # 1. Corner enclosures
    corners = [(4, 4), (4, 16), (16, 4), (16, 16)]
    for r, c in corners:
        if board[r, c] == 0 and is_legal(r, c):
            score = evaluate_position(r, c) + 20  # Bonus for corners
            if score > best_score:
                best_score = score
                best_move = (r, c)
    
    # 2. Star points extension
    star_points = [(4, 10), (10, 4), (10, 16), (16, 10), (10, 10)]
    for r, c in star_points:
        if board[r, c] == 0 and is_legal(r, c):
            score = evaluate_position(r, c) + 15  # Bonus for star points
            if score > best_score:
                best_score = score
                best_move = (r, c)
    
    # 3. Strategic areas around our stones
    explored = set()
    for r, c in me:
        # Check local area around our stones
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                nr, nc = r + dr, c + dc
                if (nr, nc) not in explored and is_on_board(nr, nc):
                    explored.add((nr, nc))
                    score = evaluate_position(nr, nc)
                    if score > best_score:
                        best_score = score
                        best_move = (nr, nc)
    
    # 4. Fallback to wider search if no good moves found
    if best_score < 0:
        for r in range(3, 18):
            for c in range(3, 18):
                if board[r, c] == 0:
                    score = evaluate_position(r, c)
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)
    
    return (best_move, memory)
