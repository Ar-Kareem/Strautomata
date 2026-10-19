
import math

# Configuration
SEARCH_DEPTH = 10
PITS_PER_SIDE = 6
STORE_IDX = 6
OPP_STORE_IDX = 13
TOTAL_PITS = 14 # Indices 0-5 (You), 6 (Store), 7-12 (Opponent), 13 (Opponent Store)

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Determines the next move for the Kalah game using Minimax with Alpha-Beta pruning.
    """
    # Combine lists into a single board representation for easier index arithmetic.
    # board[0:6] -> your houses
    # board[6]   -> your store
    # board[7:13] -> opponent houses
    # board[13]  -> opponent store
    board = you + opponent

    # Identify legal moves
    legal_moves = [i for i in range(PITS_PER_SIDE) if board[i] > 0]
    if not legal_moves:
        return 0

    best_move = -1
    best_value = -math.inf
    alpha = -math.inf
    beta = math.inf

    # Move Ordering: Prioritize moves that give an extra turn (landing in store)
    def score_potential(move):
        seeds = board[move]
        # Check if this move lands in store (index 6)
        # Distance to store is 6 - move.
        # Cycle length is 13 (we skip index 13, opponent's store)
        dist = STORE_IDX - move
        if (seeds - dist) % 13 == 0 and seeds >= dist:
            return 0 # Highest priority
        return 1

    legal_moves.sort(key=score_potential)

    for move in legal_moves:
        # Create a copy of the board for simulation
        next_board = list(board)
        extra_turn = apply_move(next_board, move, is_player=True)

        if extra_turn:
            value = minimax(next_board, SEARCH_DEPTH - 1, alpha, beta, maximizing=True)
        else:
            value = minimax(next_board, SEARCH_DEPTH - 1, alpha, beta, maximizing=False)

        if value > best_value:
            best_value = value
            best_move = move
        
        alpha = max(alpha, value)
        # Pruning is less effective at the root, but good practice
        if beta <= alpha:
            break

    return best_move

def apply_move(board: list[int], move: int, is_player: bool) -> bool:
    """
    Simulates sowing seeds from the specified pit.
    Updates board in place.
    Returns True if the move grants an extra turn.
    """
    seeds = board[move]
    board[move] = 0
    current_idx = move
    
    while seeds > 0:
        current_idx += 1
        
        # Handle wrapping and skipping stores
        if is_player:
            # Player (indices 0-6, 7-12). Store is 6. Skip 13.
            if current_idx == TOTAL_PITS - 1: # Skip opponent store (13)
                current_idx = 0
        else:
            # Opponent (indices 7-13, 0-6). Store is 13. Skip 6.
            if current_idx == STORE_IDX: # Skip player store (6)
                current_idx += 1
            if current_idx >= TOTAL_PITS: # Wrap around
                current_idx = 0
                
        board[current_idx] += 1
        seeds -= 1

    # Capture Rule
    # If last seed is in an empty house on own side, and opposite house is not empty
    if is_player and 0 <= current_idx <= 5: # Player's house
        if board[current_idx] == 1: # Was empty before drop
            opposite_idx = 12 - current_idx # Map 0->12, 1->11, ..., 5->7
            if board[opposite_idx] > 0:
                board[STORE_IDX] += board[current_idx] + board[opposite_idx]
                board[current_idx] = 0
                board[opposite_idx] = 0
    elif not is_player and 7 <= current_idx <= 12: # Opponent's house
        if board[current_idx] == 1:
            opposite_idx = 12 - current_idx
            if board[opposite_idx] > 0:
                board[OPP_STORE_IDX] += board[current_idx] + board[opposite_idx]
                board[current_idx] = 0
                board[opposite_idx] = 0

    # Extra Turn Rule
    if is_player and current_idx == STORE_IDX:
        return True
    if not is_player and current_idx == OPP_STORE_IDX:
        return True
    
    return False

def minimax(board: list[int], depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """
    Minimax algorithm with Alpha-Beta pruning.
    """
    # Check Terminal State
    player_houses_empty = all(board[i] == 0 for i in range(6))
    opponent_houses_empty = all(board[i] == 0 for i in range(7, 13))

    if player_houses_empty or opponent_houses_empty:
        # Game Over
        # Collect remaining seeds
        player_score = board[STORE_IDX] + sum(board[0:6])
        opponent_score = board[OPP_STORE_IDX] + sum(board[7:13])
        return player_score - opponent_score

    if depth == 0:
        return evaluate(board)

    if maximizing:
        max_eval = -math.inf
        moves = [i for i in range(6) if board[i] > 0]
        
        # Sort moves: Extra turns first
        moves.sort(key=lambda m: 1 if (board[m] - (STORE_IDX - m)) % 13 == 0 and board[m] >= (STORE_IDX - m) else 2)

        for move in moves:
            next_board = list(board)
            extra = apply_move(next_board, move, True)
            
            if extra:
                eval_val = minimax(next_board, depth - 1, alpha, beta, True)
            else:
                eval_val = minimax(next_board, depth - 1, alpha, beta, False)
            
            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        moves = [i for i in range(7, 13) if board[i] > 0]
        
        # Sort moves: Extra turns first
        # Opponent store is 13. Distance from m (7-12) is 13 - m.
        moves.sort(key=lambda m: 1 if (board[m] - (OPP_STORE_IDX - m)) % 13 == 0 and board[m] >= (OPP_STORE_IDX - m) else 2)

        for move in moves:
            next_board = list(board)
            extra = apply_move(next_board, move, False)
            
            if extra:
                eval_val = minimax(next_board, depth - 1, alpha, beta, False)
            else:
                eval_val = minimax(next_board, depth - 1, alpha, beta, True)
            
            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval

def evaluate(board: list[int]) -> float:
    """
    Heuristic evaluation of the board state.
    Score = (My Store - Opp Store) + 0.5 * (My Material - Opp Material)
    """
    store_diff = board[STORE_IDX] - board[OPP_STORE_IDX]
    my_material = sum(board[0:6])
    opp_material = sum(board[7:13])
    material_diff = my_material - opp_material
    return store_diff + 0.5 * material_diff
