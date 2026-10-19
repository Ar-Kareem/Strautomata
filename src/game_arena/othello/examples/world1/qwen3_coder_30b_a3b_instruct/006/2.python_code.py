
import numpy as np
from collections import deque

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Helper to convert coordinates to algebraic notation
    def pos_to_str(r, c):
        return chr(ord('a') + c) + str(8 - r)
    
    # Helper to convert algebraic notation to coordinates
    def str_to_pos(s):
        c = ord(s[0]) - ord('a')
        r = 8 - int(s[1])
        return (r, c)
    
    # Directions for checking flips (8 directions)
    DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    
    # Position weights (corners are most valuable)
    POSITION_WEIGHTS = np.array([
        [100, -10, 11,  6,  6, 11, -10, 100],
        [-10, -20,  1,  2,  2,  1, -20, -10],
        [ 11,   1,  5,  2,  2,  5,   1,  11],
        [  6,   2,  2,  2,  2,  2,   2,   6],
        [  6,   2,  2,  2,  2,  2,   2,   6],
        [ 11,   1,  5,  2,  2,  5,   1,  11],
        [-10, -20,  1,  2,  2,  1, -20, -10],
        [100, -10, 11,  6,  6, 11, -10, 100]
    ])
    
    def is_valid_position(r, c):
        return 0 <= r < 8 and 0 <= c < 8
    
    def get_flips(r, c, player_board, opponent_board):
        """Get all opponent discs that would be flipped if player places at (r,c)"""
        flips = set()
        
        if player_board[r][c] == 1 or opponent_board[r][c] == 1:
            return flips  # Can't place on occupied square
            
        for dr, dc in DIRECTIONS:
            temp_flips = set()
            nr, nc = r + dr, c + dc
            
            # Look for a player disc in this direction
            while is_valid_position(nr, nc) and opponent_board[nr][nc] == 1:
                temp_flips.add((nr, nc))
                nr += dr
                nc += dc
            
            # If we found a player disc at the end of this direction
            if is_valid_position(nr, nc) and player_board[nr][nc] == 1:
                flips.update(temp_flips)
        
        return flips
    
    def make_move(r, c, player_board, opponent_board, flips):
        """Apply a move and return new boards"""
        new_player = player_board.copy()
        new_opponent = opponent_board.copy()
        
        new_player[r][c] = 1
        for fr, fc in flips:
            new_opponent[fr][fc] = 0
            new_player[fr][fc] = 1
            
        return new_player, new_opponent
    
    def get_all_legal_moves(player_board, opponent_board):
        """Get all legal moves for the current player"""
        moves = []
        for r in range(8):
            for c in range(8):
                flips = get_flips(r, c, player_board, opponent_board)
                if flips:
                    moves.append((r, c, flips))
        return moves
    
    # Get all legal moves
    legal_moves = get_all_legal_moves(you, opponent)
    
    if not legal_moves:
        return "pass"
    
    # Prefer moves that:
    # 1. Flip maximum opponent discs
    # 2. Are in good positions (corners, edges, etc.)
    best_move = None
    best_score = -1
    
    for r, c, flips in legal_moves:
        # Base score: number of flipped discs
        score = len(flips)
        # Add positional value
        score += POSITION_WEIGHTS[r][c]
        
        # Prefer corners
        if (r, c) in [(0,0), (0,7), (7,0), (7,7)]:
            score += 1000
        
        # Avoid moves next to corners if corner is not taken
        if (r, c) in [(0,1), (1,0), (0,6), (1,7), (6,0), (7,1), (6,7), (7,6)]:
            # Check that corner is not open
            corner_open = False
            if (r == 0 or r == 7) and (c == 0 or c == 7):
                corner_r = 0 if r == 0 else 7
                corner_c = 0 if c == 0 else 7
                if you[corner_r][corner_c] == 0 and opponent[corner_r][corner_c] == 0:
                    corner_open = True
            # If corner is likely to be taken, this position is bad
            if not corner_open:
                score -= 500
        
        # Prefer to not be in vulnerable positions (edges without corner protection)
        if r == 0 or r == 7 or c == 0 or c == 7:
            if r in (0,7) and c not in (0,7):
                # Middle of top/bottom edge - risky
                score -= 200
            if c in (0,7) and r not in (0,7):
                # Middle of left/right edge - risky
                score -= 200
        
        # Tie-breaking: prefer moves that avoid giving opponent good moves
        # This is a simple strategy to avoid "bad positions"
        # (in a full implementation, this would use deeper evaluation)
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    # If we didn't find a good move, return the first one
    if best_move is None:
        r, c, _ = legal_moves[0]
        return pos_to_str(r, c)
    
    return pos_to_str(best_move[0], best_move[1])
