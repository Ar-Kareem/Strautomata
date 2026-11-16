
import numpy as np
import itertools
import time

# Precompute all possible 5-in-a-row lines (indices in 6x6 grid)
ALL_LINES = []
# Horizontal lines
for r in range(6):
    for c in range(2):
        line = [(r, c + i) for i in range(5)]
        ALL_LINES.append(line)
# Vertical lines
for c in range(6):
    for r in range(2):
        line = [(r + i, c) for i in range(5)]
        ALL_LINES.append(line)
# Diagonals (top-left to bottom-right)
for r in range(2):
    for c in range(2):
        line = [(r + i, c + i) for i in range(5)]
        ALL_LINES.append(line)
# Diagonals (top-right to bottom-left)
for r in range(2):
    for c in range(4, 6):
        line = [(r + i, c - i) for i in range(5)]
        ALL_LINES.append(line)

# Quadrant definitions: (row_start, row_end, col_start, col_end)
QUADS = [
    (0, 3, 0, 3),
    (0, 3, 3, 6),
    (3, 6, 0, 3),
    (3, 6, 3, 6)
]

def rotate_quadrant(board, quad, direction):
    """Rotate 3x3 quadrant in place on board (0-indexed)."""
    rs, re, cs, ce = QUADS[quad]
    sub = board[rs:re, cs:ce].copy()
    if direction == 'L':  # anticlockwise
        sub = np.rot90(sub, 1)
    else:  # clockwise
        sub = np.rot90(sub, -1)
    board[rs:re, cs:ce] = sub

def count_line_score(board_you, board_opp):
    """Score based on marbles in 5-in-a-row lines."""
    score = 0
    for line in ALL_LINES:
        yc = sum(board_you[r, c] for r, c in line)
        oc = sum(board_opp[r, c] for r, c in line)
        if yc > 0 and oc == 0:
            score += (1 << yc)  # exponential bonus
        elif oc > 0 and yc == 0:
            score -= (1 << oc)
    return score

def evaluate(you_board, opp_board):
    """Heuristic evaluation of position."""
    score = 0
    # Line scores
    score += count_line_score(you_board, opp_board) * 10
    
    # Center control
    center_cells = [(2,2),(2,3),(3,2),(3,3)]
    for r, c in center_cells:
        if you_board[r, c]:
            score += 2
        elif opp_board[r, c]:
            score -= 2
    
    # Mobility (empty cells adjacent to own marbles)
    dirs = [(-1,0),(1,0),(0,-1),(0,1)]
    for r in range(6):
        for c in range(6):
            if you_board[r, c]:
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 6 and 0 <= nc < 6 and you_board[nr, nc] == 0 and opp_board[nr, nc] == 0:
                        score += 0.5
            elif opp_board[r, c]:
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 6 and 0 <= nc < 6 and you_board[nr, nc] == 0 and opp_board[nr, nc] == 0:
                        score -= 0.5
    
    return score

def check_win(board_you, board_opp):
    """Return 1 if you win, -1 if opponent wins, 0 otherwise."""
    for line in ALL_LINES:
        yc = sum(board_you[r, c] for r, c in line)
        oc = sum(board_opp[r, c] for r, c in line)
        if yc == 5:
            return 1
        if oc == 5:
            return -1
    return 0

def generate_moves(you_board, opp_board):
    """Yield all legal moves (row, col, quad, dir) as tuples."""
    empty = np.where((you_board == 0) & (opp_board == 0))
    empty_cells = list(zip(empty[0], empty[1]))
    # Prioritize center placements
    empty_cells.sort(key=lambda rc: abs(rc[0]-2.5) + abs(rc[1]-2.5))
    for r, c in empty_cells:
        for q in range(4):
            for d in ('L', 'R'):
                yield (r+1, c+1, q, d)  # convert to 1-indexed for output

def apply_move(you_board, opp_board, move):
    """Apply move to copies of boards."""
    r, c, q, d = move
    r0, c0 = r-1, c-1
    new_you = you_board.copy()
    new_opp = opp_board.copy()
    new_you[r0, c0] = 1
    rotate_quadrant(new_you, q, d)
    rotate_quadrant(new_opp, q, d)
    return new_you, new_opp

def minimax(you_board, opp_board, depth, alpha, beta, maximizing):
    """Alpha-beta search."""
    win = check_win(you_board, opp_board)
    if win != 0:
        return win * 10000, None
    if depth == 0:
        return evaluate(you_board, opp_board), None
    
    best_move = None
    if maximizing:
        best_val = -float('inf')
        for move in generate_moves(you_board, opp_board):
            ny, no = apply_move(you_board, opp_board, move)
            val, _ = minimax(ny, no, depth-1, alpha, beta, False)
            if val > best_val:
                best_val = val
                best_move = move
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best_val, best_move
    else:
        best_val = float('inf')
        for move in generate_moves(you_board, opp_board):
            ny, no = apply_move(you_board, opp_board, move)
            val, _ = minimax(ny, no, depth-1, alpha, beta, True)
            if val < best_val:
                best_val = val
                best_move = move
            beta = min(beta, val)
            if beta <= alpha:
                break
        return best_val, best_move

def policy(you, opponent):
    """Main policy function."""
    start_time = time.time()
    you_board = np.array(you, dtype=int)
    opp_board = np.array(opponent, dtype=int)
    
    # If first move, place near center
    if np.sum(you_board) == 0 and np.sum(opp_board) == 0:
        return "3,3,0,L"
    
    best_move = None
    # Iterative deepening with time limit
    for depth in range(2, 5):
        if time.time() - start_time > 0.8:
            break
        val, move = minimax(you_board, opp_board, depth, -float('inf'), float('inf'), True)
        if move is not None:
            best_move = move
        # If winning move found, return immediately
        if val > 5000:
            break
    
    if best_move is None:
        # fallback: first legal move
        for move in generate_moves(you_board, opp_board):
            best_move = move
            break
    
    r, c, q, d = best_move
    return f"{r},{c},{q},{d}"
