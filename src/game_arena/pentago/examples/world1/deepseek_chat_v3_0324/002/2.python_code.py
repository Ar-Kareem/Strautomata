
import numpy as np
from itertools import product

def policy(you, opponent):
    you_arr = np.array(you)
    opponent_arr = np.array(opponent)
    board = np.zeros((6,6), dtype=int)
    board[you_arr == 1] = 1  # 1 for my pieces
    board[opponent_arr == 1] = -1  # -1 for opponent
    
    all_moves = generate_all_legal_moves(board)
    
    # Check if I can win immediately
    for move in all_moves:
        new_board = apply_move(board.copy(), move, 1)
        if check_win(new_board, 1):
            return move
    
    # Check if opponent can win next turn and block
    for move in all_moves:
        new_board = apply_move(board.copy(), move, 1)
        # Check if opponent wins in response to this move
        opponent_can_win = False
        opp_moves = generate_all_legal_moves(new_board)
        for opp_move in opp_moves:
            opp_new_board = apply_move(new_board.copy(), opp_move, -1)
            if check_win(opp_new_board, -1):
                opponent_can_win = True
                break
        if opponent_can_win:
            return move  # block by making this move
    
    # Use heuristic to select best available move
    best_move = None
    best_score = -float('inf')
    for move in all_moves:
        new_board = apply_move(board.copy(), move, 1)
        score = evaluate_position(new_board)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move if best_move else all_moves[0]

def generate_all_legal_moves(board):
    moves = []
    empty_cells = list(zip(*np.where(board == 0)))
    for (r, c) in empty_cells:
        for quad in range(4):
            for dir in ['L', 'R']:
                moves.append(f"{r+1},{c+1},{quad},{dir}")
    return moves

def apply_move(board, move_str, player):
    r, c, quad, dir = parse_move(move_str)
    if board[r, c] != 0:
        return None  # illegal move
    board[r, c] = player
    rotate_quadrant(board, quad, dir)
    return board

def parse_move(move_str):
    parts = move_str.split(',')
    r = int(parts[0]) - 1
    c = int(parts[1]) - 1
    quad = int(parts[2])
    dir = parts[3]
    return r, c, quad, dir

def rotate_quadrant(board, quadrant, direction):
    row_start = 0 if quadrant in [0,1] else 3
    col_start = 0 if quadrant in [0,2] else 3
    sub = board[row_start:row_start+3, col_start:col_start+3]
    if direction == 'L':
        sub[:] = np.rot90(sub, 1)
    else:
        sub[:] = np.rot90(sub, -1)

def check_win(board, player):
    # Check all possible lines for 5-in-a-row
    # Check rows
    for r in range(6):
        for c in range(2):
            if np.all(board[r, c:c+5] == player):
                return True
    # Check columns
    for c in range(6):
        for r in range(2):
            if np.all(board[r:r+5, c] == player):
                return True
    # Check diagonals
    for r in range(2):
        for c in range(2):
            if np.all([board[r+i, c+i] == player for i in range(5)]):
                return True
            if np.all([board[r+i, 5-c-i] == player for i in range(5)]):
                return True
    return False

def evaluate_position(board):
    # Simple heuristic evaluation of board position
    score = 0
    
    # Prefer center positions
    center = board[2:4, 2:4]
    score += np.sum(center == 1) * 2
    score -= np.sum(center == -1) * 2
    
    # Count potential lines
    for line in get_all_lines():
        my_count = sum(1 for (r,c) in line if board[r,c] == 1)
        opp_count = sum(1 for (r,c) in line if board[r,c] == -1)
        if opp_count == 0:
            score += my_count * my_count
        if my_count == 0:
            score -= opp_count * opp_count
        if my_count >= 4:
            score += 100
        if opp_count >= 4:
            score -= 100
    
    return score

def get_all_lines():
    lines = []
    # Rows
    for r in range(6):
        for c in range(2):
            lines.append([(r, c+i) for i in range(6)])
    # Columns
    for c in range(6):
        for r in range(2):
            lines.append([(r+i, c) for i in range(6)])
    # Diagonals
    for r in range(2):
        for c in range(2):
            lines.append([(r+i, c+i) for i in range(6)])
            lines.append([(r+i, 5-c-i) for i in range(6)])
    return lines
