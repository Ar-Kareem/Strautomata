
import numpy as np
from typing import Tuple

def _make_move(you: list[int], opponent: list[int], move: int) -> Tuple[list[int], list[int], bool]:
    """Execute a move and return new state and whether extra move was gained"""
    you = you.copy()
    opponent = opponent.copy()
    
    seeds = you[move]
    you[move] = 0
    current_side = 'you'
    current_pos = move + 1
    last_pos = None
    
    while seeds > 0:
        if current_side == 'you':
            if current_pos <= 6:
                you[current_pos] += 1
                last_pos = ('you', current_pos)
                current_pos += 1
            else:
                current_side = 'opponent'
                current_pos = 0
        else:
            if current_pos <= 5:
                opponent[current_pos] += 1
                last_pos = ('opponent', current_pos)
                current_pos += 1
            else:
                current_side = 'you'
                current_pos = 0
        seeds -= 1
    
    # Check for capture
    if last_pos and last_pos[0] == 'you' and 0 <= last_pos[1] <= 5:
        if you[last_pos[1]] == 1 and opponent[5 - last_pos[1]] > 0:
            # Capture
            you[6] += you[last_pos[1]] + opponent[5 - last_pos[1]]
            you[last_pos[1]] = 0
            opponent[5 - last_pos[1]] = 0
    
    extra_move = last_pos == ('you', 6)
    return you, opponent, extra_move

def _evaluate(you: list[int], opponent: list[int]) -> float:
    """Evaluate board position from your perspective"""
    score_diff = you[6] - opponent[6]
    
    # Count seeds in play
    you_in_play = sum(you[0:6])
    opp_in_play = sum(opponent[0:6])
    
    # Basic evaluation
    eval_score = score_diff
    
    # Bonus for having more seeds in play (more options)
    if you_in_play > opp_in_play:
        eval_score += 0.1 * (you_in_play - opp_in_play)
    
    # Penalty for letting opponent have many seeds ready to score
    for i in range(6):
        if opponent[i] == 6 - i:  # Can score on next move
            eval_score -= 1.0
    
    # Bonus for having seeds that can score next move
    for i in range(6):
        if you[i] == 6 - i:
            eval_score += 0.8
    
    return eval_score

def _minimax(you: list[int], opponent: list[int], depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """Minimax search with alpha-beta pruning"""
    if depth == 0 or sum(you[0:6]) == 0 or sum(opponent[0:6]) == 0:
        return _evaluate(you, opponent)
    
    if maximizing:
        max_eval = float('-inf')
        for move in range(6):
            if you[move] > 0:
                new_you, new_opp, extra = _make_move(you, opponent, move)
                if extra:
                    eval_score = _minimax(new_you, new_opp, depth, alpha, beta, True)
                else:
                    eval_score = _minimax(new_opp, new_you, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
        return max_eval
    else:
        min_eval = float('inf')
        for move in range(6):
            if opponent[move] > 0:
                new_opp, new_you, extra = _make_move(opponent, you, move)
                if extra:
                    eval_score = _minimax(new_you, new_opp, depth - 1, alpha, beta, False)
                else:
                    eval_score = _minimax(new_you, new_opp, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
        return min_eval

def policy(you: list[int], opponent: list[int]) -> int:
    """Main policy function"""
    # Determine search depth based on game state
    total_seeds = sum(you[0:6]) + sum(opponent[0:6])
    if total_seeds > 30:
        depth = 4
    elif total_seeds > 20:
        depth = 5
    elif total_seeds > 10:
        depth = 6
    else:
        depth = 7
    
    # Get all legal moves
    legal_moves = [i for i in range(6) if you[i] > 0]
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Evaluate all moves
    best_move = legal_moves[0]
    best_value = float('-inf')
    
    for move in legal_moves:
        new_you, new_opp, extra = _make_move(you, opponent, move)
        
        # Quick evaluation to avoid obviously bad moves
        if new_you[6] - opponent[6] < you[6] - new_opp[6] - 2:
            continue
        
        if extra:
            value = _minimax(new_you, new_opp, depth, float('-inf'), float('inf'), True)
        else:
            value = _minimax(new_opp, new_you, depth - 1, float('-inf'), float('inf'), False)
        
        if value > best_value:
            best_value = value
            best_move = move
    
    return best_move
