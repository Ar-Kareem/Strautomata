
import random
import time
from typing import List, Union

# Board Constants
ROWS = 5
COLS = 6
SIZE = ROWS * COLS

# Directions: (row_delta, col_delta, char)
# Used for generating the return string and precomputing neighbors
DIRECTIONS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

# Precompute neighbors for each cell index (0 to 29)
# NEIGHBORS[i] = [j, k, ...] where j, k are indices adjacent to i
NEIGHBORS = [[] for _ in range(SIZE)]
DIR_MAP = {} # Map (from_index, to_index) -> direction_char

for r in range(ROWS):
    for c in range(COLS):
        idx = r * COLS + c
        for dr, dc, dchar in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                nidx = nr * COLS + nc
                NEIGHBORS[idx].append(nidx)
                DIR_MAP[(idx, nidx)] = dchar

def policy(you: List[int], opponent: List[int]) -> str:
    """
    Returns the best move for the Clobber game on a 5x6 grid.
    Input format: list of 30 ints or 5x6 list of lists.
    Output format: "row,col,dir"
    """
    
    # --- Input Normalization ---
    # Handle both flat list (list[int]) and 2D list (list[list[int]]) inputs
    flat_you = []
    flat_opp = []
    
    # Check if the first element is a list (implying 2D structure)
    if len(you) > 0 and isinstance(you[0], list):
        for r in range(ROWS):
            for c in range(COLS):
                flat_you.append(you[r][c])
                flat_opp.append(opponent[r][c])
    else:
        flat_you = you
        flat_opp = opponent

    # --- Internal State Representation ---
    # Board state: 0 = Empty, 1 = My Piece, -1 = Opponent Piece
    board = [0] * SIZE
    for i in range(SIZE):
        if flat_you[i]:
            board[i] = 1
        elif flat_opp[i]:
            board[i] = -1

    # --- Search Parameters ---
    DEPTH = 6  # Sufficient depth for strong play within 1s
    
    # --- Helper Functions ---
    
    def get_moves(b: List[int], player: int) -> List[tuple]:
        """Returns a list of legal moves (from_idx, to_idx) for the given player."""
        moves = []
        target_val = -player
        # Iterate through all cells
        for i in range(SIZE):
            if b[i] == player:
                # Check precomputed neighbors
                for nidx in NEIGHBORS[i]:
                    if b[nidx] == target_val:
                        moves.append((i, nidx))
        return moves

    def evaluate(b: List[int]) -> int:
        """
        Heuristic evaluation function.
        Score = (My Mobility) - (Opponent Mobility)
        """
        my_moves = 0
        opp_moves = 0
        
        # Count mobility
        for i in range(SIZE):
            piece = b[i]
            if piece == 1:
                for nidx in NEIGHBORS[i]:
                    if b[nidx] == -1:
                        my_moves += 1
            elif piece == -1:
                for nidx in NEIGHBORS[i]:
                    if b[nidx] == 1:
                        opp_moves += 1
        
        return my_moves - opp_moves

    # --- Minimax with Alpha-Beta Pruning ---
    
    def minimax(b: List[int], depth: int, alpha: int, beta: int, maximizing: bool) -> int:
        if depth == 0:
            return evaluate(b)
        
        player = 1 if maximizing else -1
        moves = get_moves(b, player)
        
        if not moves:
            # No moves available: current player loses
            return -100000 if maximizing else 100000
            
        if maximizing:
            max_eval = -float('inf')
            for src, dst in moves:
                # Make move
                b[src] = 0
                b[dst] = 1
                
                eval_score = minimax(b, depth - 1, alpha, beta, False)
                
                # Undo move
                b[src] = 1
                b[dst] = -1
                
                if eval_score > max_eval:
                    max_eval = eval_score
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for src, dst in moves:
                # Make move
                b[src] = 0
                b[dst] = -1
                
                eval_score = minimax(b, depth - 1, alpha, beta, True)
                
                # Undo move
                b[src] = -1
                b[dst] = 1
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # --- Root Execution ---
    
    # Get all legal moves for the current state
    root_moves = get_moves(board, 1)
    
    # Safety check: If no moves, return a default (should not happen in valid game)
    if not root_moves:
        return "0,0,U"

    # Shuffle moves to add randomness to tie-breaking and strategy
    random.shuffle(root_moves)

    best_score = -float('inf')
    best_move_src = -1
    best_move_dst = -1

    # Iterate through root moves to find the best one
    for src, dst in root_moves:
        # Make move
        board[src] = 0
        board[dst] = 1
        
        # Recurse
        score = minimax(board, DEPTH - 1, -float('inf'), float('inf'), False)
        
        # Undo move
        board[src] = 1
        board[dst] = -1
        
        if score > best_score:
            best_score = score
            best_move_src = src
            best_move_dst = dst

    # Format output
    r = best_move_src // COLS
    c = best_move_src % COLS
    d = DIR_MAP[(best_move_src, best_move_dst)]
    
    return f"{r},{c},{d}"
