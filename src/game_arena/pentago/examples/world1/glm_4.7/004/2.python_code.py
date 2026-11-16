
import numpy as np

# Precompute all possible lines of length 5 on a 6x6 board
# Each line is a list of (row, col) tuples (0-indexed)
LINES = []
# Rows
for r in range(6):
    LINES.append([(r, c) for c in range(5)]) # 0-4
    LINES.append([(r, c) for c in range(1, 6)]) # 1-5
# Columns
for c in range(6):
    LINES.append([(r, c) for r in range(5)])
    LINES.append([(r, c) for r in range(1, 6)])
# Diagonals (Top-left to Bottom-right)
# Starts: (0,0), (0,1), (1,0), (1,1)
LINES.append([(0+i, 0+i) for i in range(5)])
LINES.append([(0+i, 1+i) for i in range(5)])
LINES.append([(1+i, 0+i) for i in range(5)])
LINES.append([(1+i, 1+i) for i in range(5)])
# Diagonals (Top-right to Bottom-left)
# Starts: (0,5), (0,4), (1,5), (1,4)
LINES.append([(0+i, 5-i) for i in range(5)])
LINES.append([(0+i, 4-i) for i in range(5)])
LINES.append([(1+i, 5-i) for i in range(5)])
LINES.append([(1+i, 4-i) for i in range(5)])

def get_quadrant_bounds(quad):
    # Returns (r_start, r_end, c_start, c_end)
    # 0: TL (0-2, 0-2), 1: TR (0-2, 3-5)
    # 2: BL (3-5, 0-2), 3: BR (3-5, 3-5)
    r = 0 if quad < 2 else 3
    c = 0 if quad % 2 == 0 else 3
    return r, r+3, c, c+3

def rotate_board(board, quad, direction):
    new_board = board.copy()
    r1, r2, c1, c2 = get_quadrant_bounds(quad)
    submatrix = new_board[r1:r2, c1:c2]
    
    # Rotate 90 degrees. 
    # np.rot90 default is counter-clockwise (k=1).
    # 'L' is anticlockwise, 'R' is clockwise (k=-1 or 3).
    k = 1 if direction == 'L' else -1
    new_board[r1:r2, c1:c2] = np.rot90(submatrix, k)
    return new_board

def evaluate(board):
    # Score the board from the perspective of the player to move (which is 1 in this context)
    # board: 1 (me), -1 (opp), 0 (empty)
    
    my_win = False
    opp_win = False
    
    score = 0
    
    for line in LINES:
        vals = [board[r, c] for r, c in line]
        s = sum(vals)
        c1 = vals.count(1)
        c_1 = vals.count(-1)
        
        # Check for win/loss conditions on this line
        if c1 == 5:
            my_win = True
        elif c_1 == 5:
            opp_win = True
        
        # Heuristic scoring
        # If a line is mixed (blocked by both), it contributes 0
        if c1 > 0 and c_1 > 0:
            continue
        
        # Scoring weights: encourage longer lines
        # 4 is very good, 3 is okay
        if c1 > 0:
            score += c1 ** 4
        if c_1 > 0:
            score -= c_1 ** 4

    if my_win and opp_win:
        return 0 # Draw
    if my_win:
        return 100000
    if opp_win:
        return -100000
    
    return score

def policy(you, opponent):
    # Convert to internal representation: 1 for me, -1 for opponent
    board = np.zeros((6, 6), dtype=int)
    board[you == 1] = 1
    board[opponent == 1] = -1
    
    best_score = -float('inf')
    best_move_str = ""
    
    # Generate all valid placement coordinates
    valid_moves = []
    for r in range(6):
        for c in range(6):
            if board[r, c] == 0:
                valid_moves.append((r, c))
                
    # Shuffle moves to add variety if scores are equal
    # Not strictly necessary but good for deterministic randomness
    # np.random.shuffle(valid_moves) 
    
    # Iterate all moves (Placement + Rotation)
    for r, c in valid_moves:
        # Place marble
        board[r, c] = 1
        
        for q in range(4):
            for d in ['L', 'R']:
                # Apply rotation
                new_board = rotate_board(board, q, d)
                
                # Check for immediate win
                # If I can win now, I don't need to look deeper (unless it's a draw?)
                # But usually winning immediately is best.
                val = evaluate(new_board)
                if val >= 100000:
                    return f"{r+1},{c+1},{q},{d}"
                
                # Minimax Step: Look ahead to opponent's move
                # Find the opponent's best response
                min_opponent_score = float('inf')
                
                # Get empty cells for opponent
                opp_empty = []
                for rr in range(6):
                    for cc in range(6):
                        if new_board[rr, cc] == 0:
                            opp_empty.append((rr, cc))
                
                # Optimization: Only check a subset or all if time permits.
                # With 144 moves, depth 2 is 20k evals. Python can do ~10-50k ops/ms usually?
                # 20k * 32 lines = 640k integer ops. Very fast.
                
                for rr, cc in opp_empty:
                    new_board[rr, cc] = -1
                    for qq in range(4):
                        for dd in ['L', 'R']:
                            final_board = rotate_board(new_board, qq, dd)
                            opp_val = evaluate(final_board)
                            
                            if opp_val < min_opponent_score:
                                min_opponent_score = opp_val
                                # Pruning: if opponent can force a loss (-100k) or a bad score for me
                                # and this is already worse than my current best (alpha), stop
                                if min_opponent_score < best_score:
                                    break
                        if min_opponent_score < best_score:
                            break
                    new_board[rr, cc] = 0
                    if min_opponent_score < best_score:
                        break
                
                # The value of the current move (r,c,q,d) is what the opponent forces it to be
                # Since evaluate() returns +ve for good for me, and -ve for good for opponent
                # Opponent minimizes the score. So `min_opponent_score` is the result of this branch.
                
                if min_opponent_score > best_score:
                    best_score = min_opponent_score
                    best_move_str = f"{r+1},{c+1},{q},{d}"
        
        # Undo placement
        board[r, c] = 0

    # Fallback (should not happen if board is not full)
    if not best_move_str:
        # Just return first valid move found
        for r, c in valid_moves:
            return f"{r+1},{c+1},0,R"
            
    return best_move_str
