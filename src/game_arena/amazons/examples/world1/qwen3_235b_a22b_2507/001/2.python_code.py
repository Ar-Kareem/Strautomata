
import numpy as np
from typing import List, Tuple

def policy(board: np.ndarray) -> str:
    # Find all positions of our amazons (1), opponent (2), and blocked (-1)
    def get_directions():
        return [(dr, dc) for dr in (-1,0,1) for dc in (-1,0,1) if not (dr == 0 and dc == 0)]
    
    def in_bounds(r, c):
        return 0 <= r < 6 and 0 <= c < 6

    def is_empty(r, c, brd):
        return in_bounds(r, c) and brd[r, c] == 0

    def ray_from(r, c, dr, dc, brd):
        """Yield all (r, c) along direction (dr,dc) until out of bounds or blocked"""
        r, c = r + dr, c + dc
        while in_bounds(r, c) and brd[r, c] == 0:
            yield (r, c)
            r, c = r + dr, c + dc

    def count_legal_moves(brd, player):
        """Count total number of (move + arrow) combinations for player"""
        amazon_val = 1 if player == 1 else 2
        count = 0
        dirs = get_directions()
        for r in range(6):
            for c in range(6):
                if brd[r, c] == amazon_val:
                    for dr, dc in dirs:
                        for tr, tc in ray_from(r, c, dr, dc, brd):
                            # Now from (tr,tc), shoot arrow
                            for adr, adc in dirs:
                                for ar, ac in ray_from(tr, tc, adr, adc, brd):
                                    count += 1
        return count

    # Get all legal moves for us
    moves = []  # List of (from, to, arrow) as ((fr,fc), (tr,tc), (ar,ac))
    dirs = get_directions()
    for fr in range(6):
        for fc in range(6):
            if board[fr, fc] == 1:
                for dr, dc in dirs:
                    for tr, tc in ray_from(fr, fc, dr, dc, board):
                        # Amazon moves to (tr,tc): simulate arrow from there
                        # Create temporary board with amazon moved
                        temp_board = board.copy()
                        temp_board[fr, fc] = 0
                        temp_board[tr, tc] = 1
                        for adr, adc in dirs:
                            for ar, ac in ray_from(tr, tc, adr, adc, temp_board):
                                # This arrow is valid
                                moves.append(((fr,fc), (tr,tc), (ar,ac)))

    # If no moves, this shouldn't happen, but return anything legal
    if not moves:
        # Fallback: try to return any possible
        for fr in range(6):
            for fc in range(6):
                if board[fr, fc] == 1:
                    return f"{fr},{fc}:{fr},{fc}:0,0"  # illegal but needed for fallback
        return "0,0:0,0:0,0"

    # Evaluate each move: we prefer moves that minimize opponent's next moves
    best_move = None
    min_opponent_moves = float('inf')
    our_avg_mobility = 0
    
    for move in moves:
        (fr, fc), (tr, tc), (ar, ac) = move
        # Apply move to new board
        new_board = board.copy()
        new_board[fr, fc] = 0
        new_board[tr, tc] = 1
        new_board[ar, ac] = -1  # place arrow
        
        # Count opponent's legal moves after this
        opp_moves = count_legal_moves(new_board, 2)
        
        # Break ties by our future mobility
        our_moves_after = count_legal_moves(new_board, 1)
        
        # Prefer minimizing opponent moves
        if opp_moves < min_opponent_moves:
            min_opponent_moves = opp_moves
            best_move = move
            our_avg_mobility = our_moves_after
        elif opp_moves == min_opponent_moves and our_moves_after > our_avg_mobility:
            best_move = move
            our_avg_mobility = our_moves_after

    # Return best move as string
    (fr, fc), (tr, tc), (ar, ac) = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
