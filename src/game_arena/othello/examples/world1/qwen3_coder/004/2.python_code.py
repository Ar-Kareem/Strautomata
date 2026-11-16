
import numpy as np
import itertools

# Directions for checking flips
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# Precompute positions
POSITIONS = [(r, c) for r in range(8) for c in range(8)]

# Convert position to move string
def pos_to_move(r, c):
    return chr(ord('a') + c) + str(r + 1)

# Convert move string to position
def move_to_pos(move):
    c = ord(move[0]) - ord('a')
    r = int(move[1]) - 1
    return r, c

# Check if a position is on the board
def is_on_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8

# Get all legal moves for a player
def get_legal_moves(you, opponent):
    legal_moves = set()
    for r, c in POSITIONS:
        if you[r][c] == 0 and opponent[r][c] == 0:
            # Check if this move is legal
            for dr, dc in DIRECTIONS:
                r1, c1 = r + dr, c + dc
                if is_on_board(r1, c1) and opponent[r1][c1] == 1:
                    # Found a neighbor opponent disc, check along this line
                    while is_on_board(r1, c1) and opponent[r1][c1] == 1:
                        r1 += dr
                        c1 += dc
                    if is_on_board(r1, c1) and you[r1][c1] == 1:
                        # Found a bracketing disc
                        legal_moves.add((r, c))
                        break
    return legal_moves

# Make a move and return the new board states
def make_move(you, opponent, r, c):
    new_you = you.copy()
    new_opponent = opponent.copy()
    
    new_you[r][c] = 1
    
    # Flip discs in all directions
    for dr, dc in DIRECTIONS:
        discs_to_flip = []
        r1, c1 = r + dr, c + dc
        while is_on_board(r1, c1) and opponent[r1][c1] == 1:
            discs_to_flip.append((r1, c1))
            r1 += dr
            c1 += dc
        if is_on_board(r1, c1) and new_you[r1][c1] == 1:
            # Valid line, flip discs
            for r_flip, c_flip in discs_to_flip:
                new_you[r_flip][c_flip] = 1
                new_opponent[r_flip][c_flip] = 0
                
    return new_you, new_opponent

# Evaluation function
def evaluate(you, opponent, stage):
    # Game stage: 0 (early), 1 (mid), 2 (late)
    # Count pieces
    my_count = np.sum(you)
    opp_count = np.sum(opponent)
    
    # Piece difference (weighted by game stage)
    piece_weight = 0
    if stage == 2:
        piece_weight = 1
    
    piece_diff = piece_weight * (my_count - opp_count)
    
    # Mobility difference
    my_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))
    mobility_diff = 4 * (my_moves - opp_count)
    
    # Corner occupancy
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    my_corners = sum(1 for r, c in corners if you[r][c] == 1)
    opp_corners = sum(1 for r, c in corners if opponent[r][c] == 1)
    corner_diff = 25 * (my_corners - opp_corners)
    
    # Edge occupancy
    my_edges = 0
    opp_edges = 0
    for r in range(8):
        for c in [0, 7]:
            if you[r][c] == 1:
                my_edges += 1
            elif opponent[r][c] == 1:
                opp_edges += 1
    for c in range(1, 7):
        for r in [0, 7]:
            if you[r][c] == 1:
                my_edges += 1
            elif opponent[r][c] == 1:
                opp_edges += 1
    edge_diff = 5 * (my_edges - opp_edges)
    
    return piece_diff + mobility_diff + corner_diff + edge_diff

# Game stage determination
def get_game_stage(you, opponent):
    total_discs = np.sum(you) + np.sum(opponent)
    if total_discs < 20:
        return 0  # Early game
    elif total_discs < 50:
        return 1  # Mid game
    else:
        return 2  # Late game

# Minimax with alpha-beta pruning
def minimax(you, opponent, depth, alpha, beta, maximizing_player, stage):
    if depth == 0:
        return evaluate(you, opponent, stage)
    
    if maximizing_player:
        legal_moves = get_legal_moves(you, opponent)
        if not legal_moves:
            # Check if opponent can move
            opp_legal_moves = get_legal_moves(opponent, you)
            if not opp_legal_moves:
                # Game over
                my_count = np.sum(you)
                opp_count = np.sum(opponent)
                return 10000 * (my_count - opp_count)
            else:
                # Pass
                return -minimax(opponent, you, depth - 1, -beta, -alpha, False, stage)
        
        max_eval = -np.inf
        # Sort moves by a simple heuristic (corners first)
        sorted_moves = sorted(legal_moves, key=lambda pos: (pos in [(0,0), (0,7), (7,0), (7,7)]), reverse=True)
        for r, c in sorted_moves:
            new_you, new_opponent = make_move(you, opponent, r, c)
            eval_score = minimax(new_opponent, new_you, depth - 1, -beta, -alpha, False, stage)
            eval_score = -eval_score
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        legal_moves = get_legal_moves(you, opponent)
        if not legal_moves:
            # Check if opponent can move
            opp_legal_moves = get_legal_moves(opponent, you)
            if not opp_legal_moves:
                # Game over
                my_count = np.sum(you)
                opp_count = np.sum(opponent)
                return 10000 * (my_count - opp_count)
            else:
                # Pass
                return -minimax(opponent, you, depth - 1, -beta, -alpha, True, stage)
        
        min_eval = np.inf
        # Sort moves by a simple heuristic (corners first)
        sorted_moves = sorted(legal_moves, key=lambda pos: (pos in [(0,0), (0,7), (7,0), (7,7)]), reverse=True)
        for r, c in sorted_moves:
            new_you, new_opponent = make_move(you, opponent, r, c)
            eval_score = minimax(new_opponent, new_you, depth - 1, -beta, -alpha, True, stage)
            eval_score = -eval_score
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

# Main policy function
def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    legal_moves = get_legal_moves(you, opponent)
    if not legal_moves:
        return "pass"
    
    # Determine game stage
    stage = get_game_stage(you, opponent)
    
    # Adjust search depth based on game stage and number of moves
    if stage == 0:
        depth = 4
    elif stage == 1:
        depth = 5
    else:
        depth = 6
    
    # If few legal moves, go deeper
    if len(legal_moves) < 4:
        depth += 1
    
    best_move = None
    best_value = -np.inf
    
    # Sort moves by a simple heuristic (corners first)
    sorted_moves = sorted(legal_moves, key=lambda pos: (pos in [(0,0), (0,7), (7,0), (7,7)]), reverse=True)
    
    for r, c in sorted_moves:
        new_you, new_opponent = make_move(you, opponent, r, c)
        # Evaluate the opponent's response
        value = -minimax(new_opponent, new_you, depth - 1, -np.inf, np.inf, False, stage)
        if value > best_value:
            best_value = value
            best_move = (r, c)
            
    if best_move is None:
        # Should not happen, but just in case
        best_move = legal_moves.pop()
        
    return pos_to_move(best_move[0], best_move[1])
