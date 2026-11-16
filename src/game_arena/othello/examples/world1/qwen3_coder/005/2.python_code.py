
import numpy as np

# Define the board weights for positional evaluation
BOARD_WEIGHTS = np.array([
    [30, -12, 0, -1, -1, 0, -12, 30],
    [-12, -15, -3, -3, -3, -3, -15, -12],
    [0, -3, 0, -1, -1, 0, -3, 0],
    [-1, -3, -1, -1, -1, -1, -3, -1],
    [-1, -3, -1, -1, -1, -1, -3, -1],
    [0, -3, 0, -1, -1, 0, -3, 0],
    [-12, -15, -3, -3, -3, -3, -15, -12],
    [30, -12, 0, -1, -1, 0, -12, 30]
])

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Generate all possible moves
    moves = generate_moves(you, opponent)
    
    # If no moves available, pass
    if not moves:
        return "pass"
    
    # If only one move, return it
    if len(moves) == 1:
        return move_to_string(moves[0])
    
    # Otherwise, use minimax to select the best move
    best_move = None
    best_value = float('-inf')
    
    for move in moves:
        # Make the move
        new_you, new_opponent = make_move(you, opponent, move)
        # Evaluate the move using minimax with alpha-beta pruning
        value = minimax(new_opponent, new_you, 3, False, float('-inf'), float('inf'))
        if value > best_value:
            best_value = value
            best_move = move
    
    return move_to_string(best_move)

def move_to_string(move):
    r, c = move
    col = chr(ord('a') + c)
    row = str(r + 1)
    return col + row

def generate_moves(player, opponent):
    moves = []
    for r in range(8):
        for c in range(8):
            if is_legal_move(player, opponent, r, c):
                moves.append((r, c))
    return moves

def is_legal_move(player, opponent, r, c):
    # Check if the cell is empty
    if player[r][c] == 1 or opponent[r][c] == 1:
        return False
    
    # Check all 8 directions
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            if check_direction(player, opponent, r, c, dr, dc):
                return True
    return False

def check_direction(player, opponent, r, c, dr, dc):
    r += dr
    c += dc
    found_opponent = False
    
    while 0 <= r < 8 and 0 <= c < 8:
        if opponent[r][c] == 1:
            found_opponent = True
            r += dr
            c += dc
        elif player[r][c] == 1:
            return found_opponent
        else:
            return False
    
    return False

def make_move(player, opponent, move):
    r, c = move
    new_player = player.copy()
    new_opponent = opponent.copy()
    
    new_player[r][c] = 1
    
    # Flip opponent discs in all directions
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            if check_direction(player, opponent, r, c, dr, dc):
                flip_direction(new_player, new_opponent, r, c, dr, dc)
    
    return new_player, new_opponent

def flip_direction(player, opponent, r, c, dr, dc):
    r += dr
    c += dc
    
    while 0 <= r < 8 and 0 <= c < 8:
        if opponent[r][c] == 1:
            opponent[r][c] = 0
            player[r][c] = 1
            r += dr
            c += dc
        else:
            break

def evaluate(player, opponent):
    # Calculate the difference in disc count
    player_count = np.sum(player)
    opponent_count = np.sum(opponent)
    disc_difference = player_count - opponent_count
    
    # Calculate the difference in positional score
    player_score = np.sum(player * BOARD_WEIGHTS)
    opponent_score = np.sum(opponent * BOARD_WEIGHTS)
    positional_difference = player_score - opponent_score
    
    # Combine the two factors
    return disc_difference + positional_difference

def minimax(player, opponent, depth, maximizing_player, alpha, beta):
    # Base case: depth = 0 or no moves
    if depth == 0:
        return evaluate(player, opponent)
    
    moves = generate_moves(player, opponent)
    
    if not moves:
        # Pass move
        if depth == 1:
            return evaluate(player, opponent)
        return minimax(opponent, player, depth - 1, not maximizing_player, alpha, beta)
    
    if maximizing_player:
        max_eval = float('-inf')
        for move in moves:
            new_player, new_opponent = make_move(player, opponent, move)
            eval_value = minimax(new_opponent, new_player, depth - 1, False, alpha, beta)
            max_eval = max(max_eval, eval_value)
            alpha = max(alpha, eval_value)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            new_player, new_opponent = make_move(player, opponent, move)
            eval_value = minimax(new_opponent, new_player, depth - 1, True, alpha, beta)
            min_eval = min(min_eval, eval_value)
            beta = min(beta, eval_value)
            if beta <= alpha:
                break
        return min_eval
