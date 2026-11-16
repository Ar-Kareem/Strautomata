
import numpy as np
import sys

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Othello Policy using a heuristic-based greedy search.
    Strategy: Maximize disc difference, secure corners, maximize stability,
    and minimize frontier discs. Switches to pure count in the endgame.
    """
    
    # 1. Configuration and Constants
    # ---------------------------------------------------------
    BOARD_SIZE = 8
    # Weights for board positions (Standard Othello strategy tables)
    # Corners are highly stable and valuable. 
    # C-squares and X-squares are often key to corner access.
    # Inner squares are generally bad as they are easily flanked.
    WEIGHTS = np.array([
        [100, -20, 10,  5,  5, 10, -20, 100],
        [-20, -50, -2, -2, -2, -2, -50, -20],
        [ 10,  -2,  1,  1,  1,  1,  -2,  10],
        [  5,  -2,  1,  0,  0,  1,  -2,   5],
        [  5,  -2,  1,  0,  0,  1,  -2,   5],
        [ 10,  -2,  1,  1,  1,  1,  -2,  10],
        [-20, -50, -2, -2, -2, -2, -50, -20],
        [100, -20, 10,  5,  5, 10, -20, 100]
    ], dtype=np.float32)

    # Direction vectors for the 8 neighbors
    DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]

    # 2. Helper Functions
    # ---------------------------------------------------------

    def get_valid_moves(board_me: np.ndarray, board_opp: np.ndarray) -> list:
        """Identifies all legal moves for the current player."""
        moves = []
        # Union of occupied cells to check against
        occupied = board_me | board_opp
        empty_cells = np.argwhere(occupied == 0)
        
        for r, c in empty_cells:
            if is_valid_move(r, c, board_me, board_opp):
                moves.append((r, c))
        return moves

    def is_valid_move(r: int, c: int, board_me: np.ndarray, board_opp: np.ndarray) -> bool:
        """Checks if a specific coordinate is a valid move."""
        if board_me[r][c] == 1 or board_opp[r][c] == 1:
            return False
        
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            # Must be adjacent to opponent
            if 0 <= nr < 8 and 0 <= nc < 8 and board_opp[nr][nc] == 1:
                # Walk the line
                while 0 <= nr < 8 and 0 <= nc < 8 and board_opp[nr][nc] == 1:
                    nr += dr
                    nc += dc
                # Check if the line ends with my disc
                if 0 <= nr < 8 and 0 <= nc < 8 and board_me[nr][nc] == 1:
                    return True
        return False

    def apply_move(r: int, c: int, board_me: np.ndarray, board_opp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Simulates a move and returns the new board states (copies)."""
        new_me = board_me.copy()
        new_opp = board_opp.copy()
        
        new_me[r][c] = 1
        
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            potential_flips = []
            
            # Walk the line
            while 0 <= nr < 8 and 0 <= nc < 8 and new_opp[nr][nc] == 1:
                potential_flips.append((nr, nc))
                nr += dr
                nc += dc
            
            # If the line ends with my disc, flip the opponent discs
            if 0 <= nr < 8 and 0 <= nc < 8 and new_me[nr][nc] == 1:
                for fr, fc in potential_flips:
                    new_me[fr][fc] = 1
                    new_opp[fr][fc] = 0
        
        return new_me, new_opp

    def evaluate_board(board_me: np.ndarray, board_opp: np.ndarray) -> float:
        """Heuristic evaluation of the board state."""
        my_score = np.sum(board_me)
        opp_score = np.sum(board_opp)
        total_discs = my_score + opp_score
        
        # Endgame: Pure count difference
        if total_discs >= 58: # Near full board
            return (my_score - opp_score) * 1000
        
        # Early/Mid Game: Positional Heuristics
        # 1. Positional Advantage (Weighted Sum)
        pos_score = np.sum(board_me * WEIGHTS) - np.sum(board_opp * WEIGHTS)
        
        # 2. Mobility (Encourage moves that limit opponent options)
        # We can approximate this by checking if we take corners or block edges
        # But calculating opponent moves is expensive.
        # We rely heavily on positional weights which implicitly control mobility.
        
        # 3. Frontier Minimization
        # Discs on the edge of the occupied area are bad.
        # A simple approximation: count empty neighbors.
        frontier_penalty = 0
        occupied = board_me | board_opp
        my_frontier = 0
        opp_frontier = 0
        
        # Only check my discs for frontier status to save time
        my_indices = np.argwhere(board_me == 1)
        for r, c in my_indices:
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if occupied[nr][nc] == 0: # Empty neighbor
                        my_frontier += 1
                        break # Count the disc once
        
        opp_indices = np.argwhere(board_opp == 1)
        for r, c in opp_indices:
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if occupied[nr][nc] == 0:
                        opp_frontier += 1
                        break
        
        frontier_score = (opp_frontier - my_frontier) * 2
        
        # Combine scores
        total_score = pos_score + frontier_score
        
        return total_score

    # 3. Main Logic
    # ---------------------------------------------------------
    
    # Get valid moves
    moves = get_valid_moves(you, opponent)
    
    # If no moves, pass
    if not moves:
        return "pass"
    
    # If only one move, take it (optimization)
    if len(moves) == 1:
        r, c = moves[0]
        return chr(ord('a') + c) + str(r + 1)

    # Evaluate each move
    best_score = -float('inf')
    best_move = moves[0]
    
    for r, c in moves:
        # Simulate the move
        sim_you, sim_opp = apply_move(r, c, you, opponent)
        
        # Evaluate the resulting board
        score = evaluate_board(sim_you, sim_opp)
        
        # Update best move
        if score > best_score:
            best_score = score
            best_move = (r, c)
        # Tie-breaker: Prefer corners (a1, h1, a8, h8) if scores are close
        elif score == best_score:
            if (r == 0 or r == 7) and (c == 0 or c == 7):
                 # Check if current best is NOT a corner, then replace
                if not ((best_move[0] == 0 or best_move[0] == 7) and (best_move[1] == 0 or best_move[1] == 7)):
                    best_move = (r, c)

    # Convert (row, col) to algebraic notation (e.g., d3)
    final_r, final_c = best_move
    return chr(ord('a') + final_c) + str(final_r + 1)

