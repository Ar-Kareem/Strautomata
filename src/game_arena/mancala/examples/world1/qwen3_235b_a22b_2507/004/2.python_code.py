
import numpy as np
from typing import Tuple

def policy(you: list[int], opponent: list[int]) -> int:
    # Fixed depth for minimax
    MAX_DEPTH = 6
    
    # Convert to mutable arrays
    you = np.array(you, dtype=int)
    opponent = np.array(opponent, dtype=int)
    
    # Get legal moves
    moves = [i for i in range(6) if you[i] > 0]
    
    # Try to use move ordering: prioritize moves that give extra moves or captures
    def move_score(move):
        seeds = you[move]
        end_pos = move + seeds
        # Check if ends in store: extra move
        if end_pos == 6:
            return 3
        # Check if ends in empty house and opposite has seeds -> capture
        if end_pos < 6 and you[end_pos] == 0 and seeds % 13 != 0:  # not wrapping around in a way that skips
            opp_idx = 5 - end_pos
            if opponent[opp_idx] > 0:
                return 2
        return 0
    
    # Sort moves: higher score first (extra move, then capture)
    moves.sort(key=move_score, reverse=True)
    
    best_move = moves[0]
    best_value = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    for move in moves:
        new_you, new_opp, extra = apply_move(you, opponent, move)
        if extra:
            value = minimax(new_you, new_opp, MAX_DEPTH-1, alpha, beta, True, True)
        else:
            value = minimax(new_you, new_opp, MAX_DEPTH-1, alpha, beta, False, False)
        
        if value > best_value:
            best_value = value
            best_move = move
        alpha = max(alpha, best_value)
        if alpha >= beta:
            break  # beta cutoff
    
    return best_move

def apply_move(you, opp, move) -> Tuple[np.ndarray, np.ndarray, bool]:
    # Copy board states
    you = you.copy()
    opp = opp.copy()
    seeds = you[move]
    you[move] = 0
    side = 0  # 0: you, 1: opp, 2: you after wrap
    pos = move + 1
    extra_move = False
    
    while seeds > 0:
        if side == 0:  # your side
            if pos <= 5:
                you[pos] += 1
                seeds -= 1
                if seeds == 0:
                    if pos == 6:  # impossible, pos only to 5
                        extra_move = True
                    elif you[pos] == 1:  # just landed and was empty
                        opp_idx = 5 - pos
                        if opp[opp_idx] > 0:
                            # Capture
                            you[6] += you[pos] + opp[opp_idx]
                            you[pos] = 0
                            opp[opp_idx] = 0
                pos += 1
            elif pos == 6:
                # Going to store
                you[6] += 1
                seeds -= 1
                if seeds == 0:
                    extra_move = True
                # Now go to opponent side
                side = 1
                pos = 0
            else:
                # pos > 6, wrap to opposite
                side = 1
                pos = 0
        elif side == 1:  # opponent side
            if pos <= 5:
                opp[pos] += 1
                seeds -= 1
                pos += 1
                if seeds == 0:
                    # if ends in opp side, no capture
                    pass
            if pos > 5:
                # Wrap back to your side
                side = 0
                pos = 0
                # Continue
        # Ensure we continue if seeds remain
    return you, opp, extra_move

def minimax(you, opp, depth, alpha, beta, your_turn, extra_move_chain) -> float:
    if depth == 0 or (is_game_over(you) or is_game_over(opp)):
        return evaluate(you, opp, extra_move_chain)
    
    if your_turn:
        # Your turn to move
        moves = [i for i in range(6) if you[i] > 0]
        if not moves:
            return evaluate(you, opp, extra_move_chain)
        best = -float('inf')
        for move in moves:
            new_you, new_opp, extra = apply_move(you, opp, move)
            if extra:
                value = minimax(new_you, new_opp, depth-1, alpha, beta, True, True)
            else:
                value = minimax(new_you, new_opp, depth, alpha, beta, False, False)  # opponent's turn, don't decrease depth if same turn
            best = max(best, value)
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best
    else:
        # Opponent's turn
        moves = [i for i in range(6) if opp[i] > 0]
        if not moves:
            return evaluate(you, opp, extra_move_chain)
        best = float('inf')
        for move in moves:
            new_opp, new_you, extra = apply_move(opp, you, move)  # swapped: opp moves
            # But in our representation: you=you, opp=new_opp -> after opp's move
            if extra:
                value = minimax(new_you, new_opp, depth, alpha, beta, False, False)
            else:
                value = minimax(new_you, new_opp, depth-1, alpha, beta, True, False)
            best = min(best, value)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best

def evaluate(you, opp, extra_move_chain: bool) -> float:
    score = 0.0
    # Base score difference
    score += (you[6] - opp[6]) * 1.0
    
    # Add seeds on board that will likely go to store
    # Heuristic: each seed on your side: 0.1, store it
    score += np.sum(you[:6]) * 0.1
    score -= np.sum(opp[:6]) * 0.1
    
    # Bonus for extra move
    if extra_move_chain:
        score += 3.0
    
    # Mobility: more non-empty houses
    my_mobility = np.sum(you[:6] > 0)
    opp_mobility = np.sum(opp[:6] > 0)
    score += (my_mobility - opp_mobility) * 0.2
    
    # Avoid empty houses that enable capture by opponent
    for i in range(6):
        if you[i] == 0 and opp[5-i] > 0:
            # We are vulnerable to capture if opponent plays into 5-i and it ends there
            # But hard to judge — just penalize slightly
            score -= 0.5
    
    return score

def is_game_over(side) -> bool:
    # side is you or opp — check if houses 0..5 are all empty
    return np.sum(side[:6]) == 0
