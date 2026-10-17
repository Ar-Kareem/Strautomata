
import numpy as np
import random

# Directions for Queen-like movement (row, col)
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), 
              (0, -1),           (0, 1), 
              (1, -1),  (1, 0),  (1, 1)]

def get_legal_moves(board, player):
    """
    Generates all legal moves for a given player.
    A move is represented as a tuple (from_r, from_c, to_r, to_c, arrow_r, arrow_c).
    """
    moves = []
    rows, cols = board.shape
    
    # Iterate over all squares to find the player's amazons
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == player:
                # Explore all 8 movement directions
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    # Walk until we hit the edge or an obstruction
                    while 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == 0:
                        to_r, to_c = nr, nc
                        
                        # From the landing square, explore all 8 arrow shot directions
                        for adr, adc in DIRECTIONS:
                            ar, ac = to_r + adr, to_c + adc
                            # Walk until we hit the edge or an obstruction.
                            # Note: The arrow can pass through/land on the vacated square (r, c).
                            while 0 <= ar < rows and 0 <= ac < cols and (board[ar, ac] == 0 or (ar == r and ac == c)):
                                moves.append((r, c, to_r, to_c, ar, ac))
                                ar += adr
                                ac += adc
                        
                        nr += dr
                        nc += dc
    return moves

def count_mobility(board, player):
    """
    Counts the number of legal moves (mobility) for a player on the given board.
    This serves as the evaluation function.
    """
    count = 0
    rows, cols = board.shape
    
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == player:
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == 0:
                        to_r, to_c = nr, nc
                        for adr, adc in DIRECTIONS:
                            ar, ac = to_r + adr, to_c + adc
                            # In the count function, we check the board state as is.
                            # The 'from' square (r,c) is occupied by 'player', so the arrow 
                            # cannot land there unless we simulated a move first.
                            # Since count_mobility is called on a static board, 
                            # we treat standard rules: arrows land on 0.
                            while 0 <= ar < rows and 0 <= ac < cols and board[ar, ac] == 0:
                                count += 1
                                ar += adr
                                ac += adc
                        nr += dr
                        nc += dc
    return count

def policy(board):
    """
    Selects the best move by maximizing the difference in mobility 
    between the agent and the opponent after the move.
    """
    my_player = 1
    opp_player = 2
    
    # Generate all possible moves for the current state
    legal_moves = get_legal_moves(board, my_player)
    
    # Fallback if no moves found (shouldn't happen per prompt, but safe to handle)
    if not legal_moves:
        return "0,0:0,0:0,0"
        
    # Shuffle moves to ensure randomization among equal-scoring moves
    random.shuffle(legal_moves)
    
    best_score = -float('inf')
    best_move = None
    
    # Evaluate each move
    for move in legal_moves:
        fr, fc, tr, tc, ar, ac = move
        
        # Simulate the move on a copy of the board
        next_board = board.copy()
        next_board[fr, fc] = 0        # Vacate original square
        next_board[tr, tc] = my_player # Move amazon
        next_board[ar, ac] = -1       # Place arrow
        
        # Calculate opponent's mobility after this move
        opp_mobility = count_mobility(next_board, opp_player)
        
        # If opponent has no moves, this is a winning move. Take it immediately.
        if opp_mobility == 0:
            return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
        
        # Calculate our mobility after this move
        my_mobility = count_mobility(next_board, my_player)
        
        # Score = (My Mobility) - (Opponent Mobility)
        # We want to maximize our freedom and minimize theirs.
        score = my_mobility - opp_mobility
        
        if score > best_score:
            best_score = score
            best_move = move
            
    # Return the best move formatted as a string
    fr, fc, tr, tc, ar, ac = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
