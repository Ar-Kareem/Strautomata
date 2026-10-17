
import copy

def policy(state: dict) -> str:
    """
    Simple rule-based Backgammon policy.
    Prioritize: bar moves > bearing off > advancing farthest checkers.
    """
    dice = state['dice']
    if not dice:
        return 'H:P,P'
    
    sorted_dice = sorted(dice, reverse=True)  # sorted_dice[0] is the higher die
    if len(dice) == 1:
        # Single die: play it on the best available point
        best_from = _find_best_move(state, sorted_dice[0])
        return f'H:{best_from},P'
    elif len(dice) == 2:
        # Two dice: play higher first, then lower, on best points
        first_from = _find_best_move(state, sorted_dice[0])
        second_from = _find_best_move(state, sorted_dice[1])
        return f'H:{first_from},{second_from}'

def _find_best_move(state: dict, die_val: int) -> str:
    """
    Find the best 'from' location for a given die value.
    Prioritizes bar > bearing off potential > farthest points.
    """
    # 1. Prioritize bar if checkers are on it
    if state['my_bar'] > 0:
        return 'B'
    
    # Check if bearing off is possible (all checkers in 0-5)
    can_bear_off = all(state['my_pts'][i] == 0 for i in range(6, 24))
    if can_bear_off:
        # Prioritize points 0-5 in order from highest to lowest (farthest first)
        for p in range(5, -1, -1):  # A5 to A0
            if state['my_pts'][p] > 0:
                return f'A{p}'
    
    # 3. Otherwise, move from the farthest point with checkers (23 to 0)
    for p in range(23, -1, -1):
        if state['my_pts'][p] > 0:
            return f'A{p}'
    
    # Fallback: should not happen if there are checkers left
    return 'P'
