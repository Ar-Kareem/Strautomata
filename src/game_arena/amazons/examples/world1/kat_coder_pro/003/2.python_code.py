
import numpy as np
from typing import List, Tuple

def policy(board) -> str:
    """
    A move-selection policy for Amazons on a 6x6 board.
    
    Strategy:
    - Find all amazons (player pieces).
    - For each amazon, compute all legal moves and arrow shots.
    - Evaluate moves using a heuristic:
      * Mobility: Score based on how many squares are reachable for the moved amazon.
      * Territory control: Prefer moves that shoot arrows to squares that reduce opponent mobility.
      * Avoid moves that trap our own amazons.
    - Select the move with the highest heuristic score.
    - If multiple moves have the same score, choose the first one found.
    - If no moves are found (should not happen in valid games), return a dummy format.
    """
    # Directions for queen moves: 8 directions
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]
    
    def is_valid_pos(r, c):
        return 0 <= r < 6 and 0 <= c < 6
    
    def get_moves_in_direction(board, r, c, dr, dc):
        """Get all reachable positions in direction (dr, dc) from (r, c)."""
        moves = []
        nr, nc = r + dr, c + dc
        while is_valid_pos(nr, nc) and board[nr, nc] == 0:
            moves.append((nr, nc))
            nr, nc = nr + dr, nc + dc
        return moves
    
    def get_reachable_squares(board, r, c):
        """Get all squares reachable from (r, c) via queen moves."""
        reachable = []
        for dr, dc in directions:
            reachable.extend(get_moves_in_direction(board, r, c, dr, dc))
        return reachable
    
    def simulate_move(board, from_pos, to_pos, arrow_pos):
        """Simulate a move and return the new board."""
        new_board = board.copy()
        new_board[from_pos] = 0
        new_board[to_pos] = 1
        new_board[arrow_pos] = -1
        return new_board
    
    def evaluate_board(board):
        """Heuristic evaluation of the board state."""
        # Count mobility for player vs opponent
        player_mobility = 0
        opponent_mobility = 0
        
        for r in range(6):
            for c in range(6):
                if board[r, c] == 1:  # player amazon
                    player_mobility += len(get_reachable_squares(board, r, c))
                elif board[r, c] == 2:  # opponent amazon
                    opponent_mobility += len(get_reachable_squares(board, r, c))
        
        # Prefer moves that maximize our mobility and minimize opponent mobility
        # Avoid negative scores by adding a base or using ratio
        if opponent_mobility == 0:
            return 10000 if player_mobility > 0 else 0
        return player_mobility - opponent_mobility
    
    # Find all player amazons
    amazons = []
    for r in range(6):
        for c in range(6):
            if board[r, c] == 1:
                amazons.append((r, c))
    
    # Generate all legal moves
    best_score = -float('inf')
    best_move = None
    
    for from_r, from_c in amazons:
        # Get all possible move destinations
        move_destinations = get_reachable_squares(board, from_r, from_c)
        
        for to_r, to_c in move_destinations:
            # Temporarily simulate the amazon move for arrow shots
            temp_board = board.copy()
            temp_board[from_r, from_c] = 0
            temp_board[to_r, to_c] = 1
            
            # Get all possible arrow destinations from the moved amazon
            arrow_destinations = get_reachable_squares(temp_board, to_r, to_c)
            
            for arrow_r, arrow_c in arrow_destinations:
                # Create new board for this move
                new_board = simulate_move(board, (from_r, from_c), (to_r, to_c), (arrow_r, arrow_c))
                
                # Evaluate the resulting position
                score = evaluate_board(new_board)
                
                if score > best_score:
                    best_score = score
                    best_move = (from_r, from_c, to_r, to_c, arrow_r, arrow_c)
    
    # If no moves found (should not happen), return random legal move
    if best_move is None:
        # Fallback: pick first legal move found
        for from_r, from_c in amazons:
            move_destinations = get_reachable_squares(board, from_r, from_c)
            for to_r, to_c in move_destinations:
                temp_board = board.copy()
                temp_board[from_r, from_c] = 0
                temp_board[to_r, to_c] = 1
                arrow_destinations = get_reachable_squares(temp_board, to_r, to_c)
                if arrow_destinations:
                    arrow_r, arrow_c = arrow_destinations[0]
                    best_move = (from_r, from_c, to_r, to_c, arrow_r, arrow_c)
                    break
            if best_move:
                break
    
    if best_move is None:
        # Should not happen in valid games, but return a valid format
        return "0,0:0,0:0,0"
    
    from_r, from_c, to_r, to_c, arrow_r, arrow_c = best_move
    return f"{from_r},{from_c}:{to_r},{to_c}:{arrow_r},{arrow_c}"
