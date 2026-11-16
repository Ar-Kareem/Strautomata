
import numpy as np
from typing import List, Tuple, Optional

def policy(state: dict) -> str:
    """
    Smart backgammon policy using heuristic evaluation.
    """
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = sorted(state['dice'], reverse=True)
    
    # If no dice, return pass
    if len(dice) == 0:
        return "H:P,P"
    
    # Generate all legal moves
    legal_moves = generate_legal_moves(my_pts, opp_pts, my_bar, my_off, dice)
    
    if not legal_moves:
        return "H:P,P"
    
    # Evaluate each move and pick the best one
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        # Simulate the move
        new_my_pts, new_my_bar, new_my_off = simulate_move(
            my_pts, opp_pts, my_bar, my_off, dice, move
        )
        
        score = evaluate_position(new_my_pts, opp_pts, new_my_bar, opp_bar, 
                                  new_my_off, opp_off, my_off)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is None:
        return "H:P,P"
    
    # Format the move string
    order, from1, from2 = best_move
    return f"{order}:{from1},{from2}"


def generate_legal_moves(my_pts: List[int], opp_pts: List[int], 
                         my_bar: int, my_off: int, 
                         dice: List[int]) -> List[Tuple[str, str, str]]:
    """
    Generate all legal moves for the current state.
    Returns list of (order, from1, from2) tuples.
    """
    moves = []
    high_die = dice[0]
    low_die = dice[1] if len(dice) > 1 else None
    
    if len(dice) == 1:
        # Single die
        if my_bar > 0:
            # Must enter from bar
            entry_point = 24 - high_die
            if entry_point >= 0 and entry_point <= 23:
                if opp_pts[entry_point] < 2:
                    moves.append(('H', f'A{entry_point}', 'P'))
        else:
            # Find all possible moves
            for start in range(24):
                if my_pts[start] > 0:
                    dest = start - high_die
                    if dest >= 0 and opp_pts[dest] < 2:
                        if can_bear_off(my_pts, my_off, start):
                            if dest == 0 or (dest < 0 and all_in_home(my_pts, my_off)):
                                moves.append(('H', f'A{start}', 'P'))
                        elif dest >= 0:
                            moves.append(('H', f'A{start}', 'P'))
            # Check bearing off
            if all_in_home(my_pts, my_off):
                for start in range(6):
                    if my_pts[start] > 0:
                        if start == high_die - 1:
                            moves.append(('H', f'A{start}', 'P'))
                        elif start < high_die - 1:
                            can_bear = True
                            for i in range(start + 1, 6):
                                if my_pts[i] > 0:
                                    can_bear = False
                                    break
                            if can_bear:
                                moves.append(('H', f'A{start}', 'P'))
    else:
        # Two dice - try both orders
        for order in ['H', 'L']:
            if order == 'H':
                first_die = high_die
                second_die = low_die
            else:
                first_die = low_die
                second_die = high_die
            
            temp_pts = list(my_pts)
            temp_bar = my_bar
            temp_off = my_off
            
            # Try first move
            first_moves = []
            if temp_bar > 0:
                entry = 24 - first_die
                if 0 <= entry <= 23 and opp_pts[entry] < 2:
                    first_moves.append(('B', f'A{entry}'))
            else:
                for start in range(24):
                    if temp_pts[start] > 0:
                        dest = start - first_die
                        if dest >= 0 and opp_pts[dest] < 2:
                            if can_bear_off(temp_pts, temp_off, start):
                                if dest == 0 or (dest < 0 and all_in_home(temp_pts, temp_off)):
                                    first_moves.append((f'A{start}', f'A{start}'))
                            elif dest >= 0:
                                first_moves.append((f'A{start}', f'A{start}'))
                if all_in_home(temp_pts, temp_off):
                    for start in range(6):
                        if temp_pts[start] > 0:
                            if start == first_die - 1:
                                first_moves.append((f'A{start}', f'A{start}'))
                            elif start < first_die - 1:
                                can_bear = all(temp_pts[i] == 0 for i in range(start + 1, 6))
                                if can_bear:
                                    first_moves.append((f'A{start}', f'A{start}'))
            
            for from1, _ in first_moves:
                # Simulate first move
                new_pts, new_bar, new_off = simulate_single_move(
                    temp_pts, opp_pts, temp_bar, temp_off, first_die, from1
                )
                
                # Try second move
                second_moves = []
                if new_bar > 0:
                    entry = 24 - second_die
                    if 0 <= entry <= 23 and opp_pts[entry] < 2:
                        second_moves.append('B')
                else:
                    for start in range(24):
                        if new_pts[start] > 0:
                            dest = start - second_die
                            if dest >= 0 and opp_pts[dest] < 2:
                                if can_bear_off(new_pts, new_off, start):
                                    if dest == 0 or (dest < 0 and all_in_home(new_pts, new_off)):
                                        second_moves.append(f'A{start}')
                                elif dest >= 0:
                                    second_moves.append(f'A{start}')
                    if all_in_home(new_pts, new_off):
                        for start in range(6):
                            if new_pts[start] > 0:
                                if start == second_die - 1:
                                    second_moves.append(f'A{start}')
                                elif start < second_die - 1:
                                    can_bear = all(new_pts[i] == 0 for i in range(start + 1, 6))
                                    if can_bear:
                                        second_moves.append(f'A{start}')
                
                if second_moves:
                    for from2 in second_moves:
                        # Determine actual from1 and from2 display
                        display_from1 = from1 if from1 == 'B' else f'A{from1}' if from1.startswith('A') else from1
                        # The from1 is already the entry point if from bar
                        if from1 == 'B':
                            entry = 24 - first_die
                            display_from1 = f'A{entry}'
                        moves.append((order, display_from1, from2))
                else:
                    # Can only play one die
                    display_from1 = from1
                    if from1 == 'B':
                        entry = 24 - first_die
                        display_from1 = f'A{entry}'
                    
                    # Check if we must play the higher die
                    if order == 'L' and first_die == low_die and second_die == high_die:
                        # We're playing low die first, but maybe we can play high die instead
                        temp_pts2 = list(my_pts)
                        temp_bar2 = my_bar
                        temp_off2 = my_off
                        high_first_moves = []
                        if temp_bar2 > 0:
                            entry = 24 - high_die
                            if 0 <= entry <= 23 and opp_pts[entry] < 2:
                                high_first_moves.append('B')
                        else:
                            for start in range(24):
                                if temp_pts2[start] > 0:
                                    dest = start - high_die
                                    if dest >= 0 and opp_pts[dest] < 2:
                                        if can_bear_off(temp_pts2, temp_off2, start):
                                            if dest == 0 or (dest < 0 and all_in_home(temp_pts2, temp_off2)):
                                                high_first_moves.append(f'A{start}')
                                        elif dest >= 0:
                                            high_first_moves.append(f'A{start}')
                            if all_in_home(temp_pts2, temp_off2):
                                for start in range(6):
                                    if temp_pts2[start] > 0:
                                        if start == high_die - 1:
                                            high_first_moves.append(f'A{start}')
                                        elif start < high_die - 1:
                                            can_bear = all(temp_pts2[i] == 0 for i in range(start + 1, 6))
                                            if can_bear:
                                                high_first_moves.append(f'A{start}')
                        if high_first_moves:
                            # We should play the higher die instead
                            continue
                    
                    moves.append((order, display_from1, 'P'))
    
    return moves


def simulate_single_move(my_pts: List[int], opp_pts: List[int], my_bar: int, 
                         my_off: int, die: int, from_pos: str) -> Tuple[List[int], int, int]:
    """Simulate a single move and return new state."""
    new_pts = list(my_pts)
    new_bar = my_bar
    new_off = my_off
    
    if from_pos == 'B':
        entry = 24 - die
        new_bar -= 1
        if opp_pts[entry] == 1:
            # Hit
            new_pts[entry] = 1
            # Opponent goes to bar - handled by engine, but we track our state
        else:
            new_pts[entry] += 1
    else:
        start = int(from_pos[1:])
        dest = start - die
        new_pts[start] -= 1
        if dest >= 0:
            if opp_pts[dest] == 1:
                new_pts[dest] = 1
            else:
                new_pts[dest] += 1
        else:
            new_off += 1
    
    return new_pts, new_bar, new_off


def simulate_move(my_pts: List[int], opp_pts: List[int], my_bar: int, 
                  my_off: int, dice: List[int], 
                  move: Tuple[str, str, str]) -> Tuple[List[int], int, int]:
    """Simulate a complete move (possibly two checker moves)."""
    order, from1, from2 = move
    high_die = dice[0]
    low_die = dice[1] if len(dice) > 1 else None
    
    if order == 'H':
        first_die = high_die
        second_die = low_die
    else:
        first_die = low_die
        second_die = high_die
    
    new_pts, new_bar, new_off = simulate_single_move(my_pts, opp_pts, my_bar, my_off, 
                                                      first_die, from1)
    
    if from2 != 'P' and second_die is not None:
        new_pts, new_bar, new_off = simulate_single_move(new_pts, opp_pts, new_bar, new_off, 
                                                          second_die, from2)
    
    return new_pts, new_bar, new_off


def can_bear_off(my_pts: List[int], my_off: int, start: int) -> bool:
    """Check if bearing off is possible from this point."""
    return start < 6


def all_in_home(my_pts: List[int], my_off: int) -> bool:
    """Check if all checkers are in home board."""
    for i in range(6, 24):
        if my_pts[i] > 0:
            return False
    return True


def evaluate_position(my_pts: List[int], opp_pts: List[int], my_bar: int, 
                      opp_bar: int, my_off: int, opp_off: int, orig_my_off: int) -> float:
    """
    Evaluate the board position heuristically.
    Higher score is better for us.
    """
    score = 0.0
    
    # Points for bearing off
    score += (my_off - orig_my_off) * 1000
    
    # Penalty for checkers on the bar
    score -= my_bar * 500
    
    # Bonus for opponent on bar
    score += opp_bar * 400
    
    # Evaluate point distribution
    for i in range(24):
        # Points we have made (2+ checkers)
        if my_pts[i] >= 2:
            score += 50
            # Bonus for points in our home board
            if i < 6:
                score += 30
            # Bonus for blocking points (5-11)
            if 5 <= i <= 11:
                score += 40
        
        # Blots are risky
        if my_pts[i] == 1:
            # Distance from opponent's home
            if i >= 18:
                score -= 30
            elif i >= 12:
                score -= 15
            else:
                score -= 5
        
        # Opponent's points
        if opp_pts[i] >= 2:
            score -= 40
            if i >= 18:
                score -= 30
    
    # Bonus for having checkers in opponent's home board (we're escaping)
    for i in range(18, 24):
        if my_pts[i] > 0:
            score -= 20
    
    # Bonus for advancing checkers
    for i in range(24):
        if my_pts[i] > 0:
            score += (24 - i) * my_pts[i] * 2
    
    # Connection bonus - adjacent checkers protect each other
    for i in range(23):
        if my_pts[i] >= 2 and my_pts[i+1] >= 2:
            score += 20
    
    # Endgame bonus
    if all_in_home(my_pts, my_off):
        score += 200
        # Bonus for bearing off quickly
        total_home = sum(my_pts[:6])
        score += (15 - total_home) * 100
    
    return score

