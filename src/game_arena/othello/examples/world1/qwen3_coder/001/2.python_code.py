
import numpy as np

# Directions for flipping discs (8 directions)
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),           (0, 1),
              (1, -1),  (1, 0),  (1, 1)]

# Board size
BOARD_SIZE = 8

# Convert move (r, c) to string notation like "d3"
def move_to_str(r, c):
    return chr(ord('a') + c) + str(r + 1)

# Convert string notation like "d3" to (r, c)
def str_to_move(s):
    c = ord(s[0]) - ord('a')
    r = int(s[1]) - 1
    return r, c

# Check if a move is legal
def is_legal_move(board, opponent_board, r, c):
    if board[r][c] != 0 or opponent_board[r][c] != 0:
        return False

    for dr, dc in DIRECTIONS:
        if is_valid_direction(board, opponent_board, r, c, dr, dc):
            return True
    return False

# Check if a direction leads to flipping
def is_valid_direction(board, opponent_board, r, c, dr, dc):
    found_opponent = False
    r += dr
    c += dc
    while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
        if opponent_board[r][c] == 1:
            found_opponent = True
        elif board[r][c] == 1:
            return found_opponent
        else:
            return False
        r += dr
        c += dc
    return False

# Get all legal moves for a player
def get_legal_moves(board, opponent_board):
    moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if is_legal_move(board, opponent_board, r, c):
                moves.append((r, c))
    return moves

# Apply a move and flip discs
def apply_move(board, opponent_board, r, c):
    new_board = board.copy()
    new_opponent_board = opponent_board.copy()
    
    new_board[r][c] = 1
    
    for dr, dc in DIRECTIONS:
        if is_valid_direction(board, opponent_board, r, c, dr, dc):
            r_temp, c_temp = r + dr, c + dc
            while 0 <= r_temp < BOARD_SIZE and 0 <= c_temp < BOARD_SIZE:
                if opponent_board[r_temp][c_temp] == 1:
                    new_board[r_temp][c_temp] = 1
                    new_opponent_board[r_temp][c_temp] = 0
                elif board[r_temp][c_temp] == 1:
                    break
                else:
                    break
                r_temp += dr
                c_temp += dc
    return new_board, new_opponent_board

# Evaluate a board position
def evaluate_move(board, opponent_board, r, c):
    # Apply move
    new_board, new_opponent_board = apply_move(board, opponent_board, r, c)
    
    # Current disc count
    my_discs = np.sum(new_board)
    opp_discs = np.sum(new_opponent_board)
    disc_diff = my_discs - opp_discs
    
    # Mobility
    my_moves = len(get_legal_moves(new_board, new_opponent_board))
    opp_moves = len(get_legal_moves(new_opponent_board, new_board))
    mobility = my_moves - opp_moves
    
    # Corner bonus
    corner_positions = [(0,0), (0,7), (7,0), (7,7)]
    corner_bonus = 0
    for cr, cc in corner_positions:
        if new_board[cr][cc] == 1:
            corner_bonus += 20
    
    # Adjacent to corner penalty (unless capturing corner)
    bad_positions = [
        (0,1), (1,0), (1,1),    # top-left
        (0,6), (1,7), (1,6),    # top-right
        (6,0), (7,1), (6,1),    # bottom-left
        (6,7), (7,6), (6,6)     # bottom-right
    ]
    corner_adj_penalty = 0
    for br, bc in bad_positions:
        if new_board[br][bc] == 1:
            # Check if corner is empty or captured
            corner_captured = False
            if (br == 0 and bc == 1):
                if new_board[0][0] == 1: corner_captured = True
            elif (br == 1 and bc == 0):
                if new_board[0][0] == 1: corner_captured = True
            elif (br == 1 and bc == 1):
                if new_board[0][0] == 1: corner_captured = True
            elif (br == 0 and bc == 6):
                if new_board[0][7] == 1: corner_captured = True
            elif (br == 1 and bc == 7):
                if new_board[0][7] == 1: corner_captured = True
            elif (br == 1 and bc == 6):
                if new_board[0][7] == 1: corner_captured = True
            elif (br == 6 and bc == 0):
                if new_board[7][0] == 1: corner_captured = True
            elif (br == 7 and bc == 1):
                if new_board[7][0] == 1: corner_captured = True
            elif (br == 6 and bc == 1):
                if new_board[7][0] == 1: corner_captured = True
            elif (br == 6 and bc == 7):
                if new_board[7][7] == 1: corner_captured = True
            elif (br == 7 and bc == 6):
                if new_board[7][7] == 1: corner_captured = True
            elif (br == 6 and bc == 6):
                if new_board[7][7] == 1: corner_captured = True
                
            if not corner_captured:
                corner_adj_penalty += 5
    
    # Stability-like heuristic: avoid edges if not safe
    # Count discs on edges
    edge_bonus = 0
    for i in range(8):
        if new_board[0][i] == 1: edge_bonus += 1
        if new_board[7][i] == 1: edge_bonus += 1
        if new_board[i][0] == 1: edge_bonus += 1
        if new_board[i][7] == 1: edge_bonus += 1
    
    # Combine features
    score = (
        10 * disc_diff +
        50 * mobility +
        100 * corner_bonus -
        25 * corner_adj_penalty +
        5 * edge_bonus
    )
    
    return score

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        return "pass"
    
    # If a corner is available, take it immediately
    corner_positions = [(0,0), (0,7), (7,0), (7,7)]
    for r, c in legal_moves:
        if (r, c) in corner_positions:
            return move_to_str(r, c)
    
    # Evaluate all moves
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for r, c in legal_moves:
        score = evaluate_move(you, opponent, r, c)
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    return move_to_str(best_move[0], best_move[1])
