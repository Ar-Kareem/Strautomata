
import numpy as np
from typing import Tuple

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Kalah policy using minimax with alpha-beta pruning.
    
    Returns the best move index (0-5) for the current player.
    """
    
    # Convert to numpy arrays for faster operations
    you_arr = np.array(you, dtype=np.int32)
    opponent_arr = np.array(opponent, dtype=np.int32)
    
    # Get legal moves
    legal_moves = [i for i in range(6) if you_arr[i] > 0]
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Determine search depth based on number of seeds
    total_seeds = you_arr[:6].sum() + opponent_arr[:6].sum()
    if total_seeds > 30:
        depth = 6
    elif total_seeds > 20:
        depth = 8
    else:
        depth = 10
    
    best_move = legal_moves[0]
    best_value = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    # Try moves in order of potential value (more seeds first)
    moves_sorted = sorted(legal_moves, key=lambda i: you_arr[i], reverse=True)
    
    for move in moves_sorted:
        # Make the move
        new_you, new_opponent, extra_move = make_move(you_arr.copy(), opponent_arr.copy(), move)
        
        if extra_move:
            # If we get an extra move, we continue searching from this state
            value = search_extra_move(new_you, new_opponent, depth - 1, alpha, beta, True)
        else:
            # Opponent's turn
            value = -search(new_opponent, new_you, depth - 1, -beta, -alpha, False)
        
        if value > best_value:
            best_value = value
            best_move = move
            
        alpha = max(alpha, best_value)
        if alpha >= beta:
            break
            
    return best_move

def make_move(you: np.ndarray, opponent: np.ndarray, move: int) -> Tuple[np.ndarray, np.ndarray, bool]:
    """
    Execute a move and return the new state and whether we get an extra move.
    """
    seeds = you[move]
    you[move] = 0
    
    # Determine the sequence of pits to sow into
    pits = []
    # Your houses after the chosen house
    for i in range(move + 1, 6):
        pits.append(('you', i))
    # Your store
    pits.append(('you_store', 0))
    # Opponent's houses
    for i in range(6):
        pits.append(('opponent', i))
    # Your houses from the beginning
    for i in range(move):
        pits.append(('you', i))
    
    # Distribute seeds
    pit_idx = 0
    for _ in range(seeds):
        pit_type, idx = pits[pit_idx]
        if pit_type == 'you':
            you[idx] += 1
        elif pit_type == 'opponent':
            opponent[idx] += 1
        # Skip opponent's store
        pit_idx = (pit_idx + 1) % len(pits)
    
    # Check for extra move
    extra_move = False
    last_pit_type, last_idx = pits[(pit_idx - 1) % len(pits)]
    if last_pit_type == 'you_store':
        extra_move = True
    
    # Check for capture
    if last_pit_type == 'you' and you[last_idx] == 1:
        # Check if opponent's opposite house has seeds
        opp_house = 5 - last_idx
        if opponent[opp_house] > 0:
            # Capture
            you[6] += you[last_idx] + opponent[opp_house]
            you[last_idx] = 0
            opponent[opp_house] = 0
    
    return you, opponent, extra_move

def search(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """
    Minimax search with alpha-beta pruning.
    """
    # Check game end
    if you[:6].sum() == 0 or opponent[:6].sum() == 0:
        return evaluate_game_end(you, opponent)
    
    if depth == 0:
        return evaluate(you, opponent, maximizing)
    
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    if not legal_moves:
        return evaluate(you, opponent, maximizing)
    
    if maximizing:
        value = float('-inf')
        for move in legal_moves:
            new_you, new_opponent, extra_move = make_move(you.copy(), opponent.copy(), move)
            
            if extra_move:
                value = max(value, search(new_you, new_opponent, depth, alpha, beta, True))
            else:
                value = max(value, -search(new_opponent, new_you, depth - 1, -beta, -alpha, False))
            
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = float('inf')
        for move in legal_moves:
            new_you, new_opponent, extra_move = make_move(you.copy(), opponent.copy(), move)
            
            if extra_move:
                value = min(value, search(new_you, new_opponent, depth, alpha, beta, False))
            else:
                value = min(value, -search(new_opponent, new_you, depth - 1, -beta, -alpha, True))
            
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

def search_extra_move(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """
    Search when we have an extra move.
    """
    if depth <= 0:
        return evaluate(you, opponent, maximizing)
    
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    if not legal_moves:
        return evaluate(you, opponent, maximizing)
    
    if maximizing:
        value = float('-inf')
        for move in legal_moves:
            new_you, new_opponent, extra_move = make_move(you.copy(), opponent.copy(), move)
            
            if extra_move:
                value = max(value, search_extra_move(new_you, new_opponent, depth, alpha, beta, True))
            else:
                value = max(value, -search(new_opponent, new_you, depth - 1, -beta, -alpha, False))
            
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = float('inf')
        for move in legal_moves:
            new_you, new_opponent, extra_move = make_move(you.copy(), opponent.copy(), move)
            
            if extra_move:
                value = min(value, search_extra_move(new_you, new_opponent, depth, alpha, beta, False))
            else:
                value = min(value, -search(new_opponent, new_you, depth - 1, -beta, -alpha, True))
            
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

def evaluate_game_end(you: np.ndarray, opponent: np.ndarray) -> float:
    """
    Evaluate a game end state.
    """
    you_final = you[6] + you[:6].sum()
    opp_final = opponent[6] + opponent[:6].sum()
    return you_final - opp_final

def evaluate(you: np.ndarray, opponent: np.ndarray, maximizing: bool) -> float:
    """
    Evaluate the current board state.
    """
    # Store difference
    store_diff = you[6] - opponent[6]
    
    # Material advantage (seeds on board)
    my_material = you[:6].sum()
    opp_material = opponent[:6].sum()
    material_diff = my_material - opp_material
    
    # Mobility (number of legal moves)
    my_moves = sum(1 for i in range(6) if you[i] > 0)
    opp_moves = sum(1 for i in range(6) if opponent[i] > 0)
    mobility_diff = my_moves - opp_moves
    
    # Extra move bonus
    extra_move_bonus = 0
    for i in range(6):
        if you[i] > 0:
            # Check if this move would land in store
            seeds = you[i]
            if (i + seeds) % 13 == 6:  # 13 pits total, index 6 is store
                extra_move_bonus += 5
    
    # Combine factors
    score = (store_diff * 10 + 
             material_diff * 1 + 
             mobility_diff * 2 + 
             extra_move_bonus)
    
    return score if maximizing else -score
