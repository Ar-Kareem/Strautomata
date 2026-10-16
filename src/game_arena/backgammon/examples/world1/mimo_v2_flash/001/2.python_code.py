
import itertools
import random
from typing import List, Tuple, Optional

def policy(state: dict) -> str:
    """
    Smart backgammon policy that balances safety, aggression, and timing.
    """
    # Extract state information
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    
    # Handle no dice (shouldn't happen but safety check)
    if not dice:
        return "H:P,P"
    
    # Sort dice for easier processing
    sorted_dice = sorted(dice, reverse=True)  # High to low
    
    # Get all legal moves for the current dice
    legal_moves = generate_all_legal_moves(my_pts, opp_pts, my_bar, opp_bar, my_off, dice)
    
    if not legal_moves:
        # No legal moves - pass
        return "H:P,P"
    
    # Evaluate each move and select the best one
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        score = evaluate_move(move, my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, dice, state)
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is None:
        # Fallback: return first legal move
        best_move = legal_moves[0]
    
    return format_move(best_move, dice)


def generate_all_legal_moves(my_pts: List[int], opp_pts: List[int], my_bar: int, 
                            opp_bar: int, my_off: int, dice: List[int]) -> List[List[int]]:
    """
    Generate all legal move combinations for the given dice roll.
    Returns list of [from1, from2] moves (using original dice order).
    """
    moves = []
    
    # Special case: if on bar, must re-enter first
    if my_bar > 0:
        return generate_bar_moves(my_pts, opp_pts, dice)
    
    # Generate moves for single die (if only one die or forced to use only one)
    if len(dice) == 1:
        for from_pos in range(24):
            if my_pts[from_pos] > 0:
                if is_move_legal(from_pos, dice[0], my_pts, opp_pts, my_off):
                    moves.append([from_pos, -1])  # -1 means no second move
    
    elif len(dice) == 2:
        # Try using both dice in both orders
        die1, die2 = dice[0], dice[1]
        
        # Try die1 then die2
        for from1 in range(24):
            if my_pts[from1] > 0 and is_move_legal(from1, die1, my_pts, opp_pts, my_off):
                # Make first move temporarily
                temp_my_pts = my_pts[:]
                temp_opp_pts = opp_pts[:]
                make_move_temp(temp_my_pts, temp_opp_pts, from1, die1, my_off)
                
                # Try second move
                for from2 in range(24):
                    if temp_my_pts[from2] > 0 and is_move_legal(from2, die2, temp_my_pts, temp_opp_pts, my_off):
                        moves.append([from1, from2])
                
                # Check if can bear off after first move
                if can_bear_off(temp_my_pts, my_off) and from1 >= 6:
                    # Try bearing off with second die
                    if can_bear_off_with_die(temp_my_pts, die2, my_off):
                        moves.append([from1, -1])
        
        # Try die2 then die1 (different order)
        for from1 in range(24):
            if my_pts[from1] > 0 and is_move_legal(from1, die2, my_pts, opp_pts, my_off):
                # Make first move temporarily
                temp_my_pts = my_pts[:]
                temp_opp_pts = opp_pts[:]
                make_move_temp(temp_my_pts, temp_opp_pts, from1, die2, my_off)
                
                # Try second move
                for from2 in range(24):
                    if temp_my_pts[from2] > 0 and is_move_legal(from2, die1, temp_my_pts, temp_opp_pts, my_off):
                        moves.append([from1, from2])
                
                # Check if can bear off after first move
                if can_bear_off(temp_my_pts, my_off) and from1 >= 6:
                    # Try bearing off with second die
                    if can_bear_off_with_die(temp_my_pts, die1, my_off):
                        moves.append([from1, -1])
        
        # Also try single moves (if double or if using only one die is forced)
        for die in dice:
            for from_pos in range(24):
                if my_pts[from_pos] > 0 and is_move_legal(from_pos, die, my_pts, opp_pts, my_off):
                    moves.append([from_pos, -1])
    
    # Remove duplicates and filter for valid moves
    unique_moves = []
    seen = set()
    for move in moves:
        key = tuple(move)
        if key not in seen:
            seen.add(key)
            unique_moves.append(move)
    
    return unique_moves


def generate_bar_moves(my_pts: List[int], opp_pts: List[int], dice: List[int]) -> List[List[int]]:
    """
    Generate moves when checkers are on the bar (must re-enter).
    """
    moves = []
    
    # When on bar, must use dice in order specified
    if len(dice) == 1:
        for die in dice:
            if can_enter_bar(my_pts, opp_pts, die):
                moves.append([-1, -1])  # Bar entry consumes the die
        return moves
    
    # Two dice - try both orders
    die1, die2 = dice[0], dice[1]
    
    # Try die1 then die2
    if can_enter_bar(my_pts, opp_pts, die1):
        # Try second die
        temp_my_pts = my_pts[:]
        temp_opp_pts = opp_pts[:]
        # Simulate entry
        target1 = 23 - die1
        if target1 >= 0 and temp_opp_pts[target1] < 2:
            temp_my_pts[target1] += 1
        
        for from2 in range(24):
            if temp_my_pts[from2] > 0 and is_move_legal(from2, die2, temp_my_pts, temp_opp_pts, 0):
                moves.append([-1, from2])
    
    # Try die2 then die1
    if can_enter_bar(my_pts, opp_pts, die2):
        temp_my_pts = my_pts[:]
        temp_opp_pts = opp_pts[:]
        target2 = 23 - die2
        if target2 >= 0 and temp_opp_pts[target2] < 2:
            temp_my_pts[target2] += 1
        
        for from2 in range(24):
            if temp_my_pts[from2] > 0 and is_move_legal(from2, die1, temp_my_pts, temp_opp_pts, 0):
                moves.append([-1, from2])
    
    # Also try single entry if only one die can be used
    for die in dice:
        if can_enter_bar(my_pts, opp_pts, die):
            moves.append([-1, -1])
    
    return moves


def is_move_legal(from_pos: int, die: int, my_pts: List[int], opp_pts: List[int], my_off: int) -> bool:
    """
    Check if a single move is legal.
    """
    if from_pos < 0 or from_pos > 23:
        return False
    
    if my_pts[from_pos] == 0:
        return False
    
    dest = from_pos - die
    
    # Check if bearing off
    if dest < 0:
        # Can only bear off if all checkers in home board
        if can_bear_off(my_pts, my_off):
            # If from_pos is beyond what die allows, only valid if no checkers behind
            if from_pos <= 5:  # In home board
                # Check if any checkers behind from_pos
                for i in range(from_pos):
                    if my_pts[i] > 0:
                        return False
                return True
        return False
    
    # Normal move
    if dest > 23:
        return False
    
    # Check destination - can't land on 2+ opponent checkers
    if opp_pts[dest] >= 2:
        return False
    
    return True


def can_bear_off(my_pts: List[int], my_off: int) -> bool:
    """
    Check if player can bear off (all checkers in home board).
    """
    # Check points 0-5 (home board for player moving 23->0)
    for i in range(6):
        if my_pts[i] > 0:
            return False
    
    # Check if any checkers on bar or outside home board
    for i in range(6, 24):
        if my_pts[i] > 0:
            return False
    
    return True


def can_bear_off_with_die(my_pts: List[int], die: int, my_off: int) -> bool:
    """
    Check if can bear off with a specific die.
    """
    if not can_bear_off(my_pts, my_off):
        return False
    
    # Find highest occupied point
    highest = -1
    for i in range(6):
        if my_pts[i] > 0:
            highest = i
    
    if highest == -1:
        return True  # No checkers left
    
    # Can bear off if die matches or exceeds highest point
    return die >= (highest + 1)


def can_enter_bar(my_pts: List[int], opp_pts: List[int], die: int) -> bool:
    """
    Check if can re-enter from bar.
    """
    target = 23 - die
    if target < 0 or target > 23:
        return False
    return opp_pts[target] < 2


def make_move_temp(my_pts: List[int], opp_pts: List[int], from_pos: int, die: int, my_off: int):
    """
    Temporarily make a move for simulation purposes.
    """
    if from_pos == -1:  # Bar entry
        return
    
    dest = from_pos - die
    
    if dest < 0:
        # Bearing off
        my_pts[from_pos] -= 1
        return
    
    # Normal move
    my_pts[from_pos] -= 1
    
    # Check for hit
    if opp_pts[dest] == 1:
        opp_pts[dest] = 0
        # Opponent checker goes to bar (not tracked in simulation)
    
    my_pts[dest] += 1


def evaluate_move(move: List[int], my_pts: List[int], opp_pts: List[int], 
                 my_bar: int, opp_bar: int, my_off: int, opp_off: int, 
                 dice: List[int], state: dict) -> float:
    """
    Evaluate the quality of a move using multiple heuristics.
    """
    score = 0.0
    
    # Make a copy of the state
    temp_my_pts = my_pts[:]
    temp_opp_pts = opp_pts[:]
    temp_my_off = my_off
    
    # Simulate the move
    if move[0] == -1:  # Bar entry
        die = dice[0] if move[1] != -1 else (dice[0] if len(dice) == 1 else dice[0])
        if len(dice) == 2 and move[1] != -1:
            # Check which die was used for bar entry
            if can_enter_bar(my_pts, opp_pts, dice[0]):
                target = 23 - dice[0]
                if target >= 0 and opp_pts[target] < 2:
                    temp_my_pts[target] += 1
            else:
                target = 23 - dice[1]
                if target >= 0 and opp_pts[target] < 2:
                    temp_my_pts[target] += 1
    else:
        # First move
        first_die = dice[0] if len(dice) == 1 else (dice[0] if len(move) > 1 and move[1] != -1 else dice[0])
        if len(dice) == 2 and len(move) > 1 and move[1] != -1:
            # Determine which die corresponds to which move
            if move[1] != -1:
                # Two moves
                die1 = dice[0]
                die2 = dice[1]
                make_move_temp(temp_my_pts, temp_opp_pts, move[0], die1, temp_my_off)
                if move[1] >= 0:
                    make_move_temp(temp_my_pts, temp_opp_pts, move[1], die2, temp_my_off)
        else:
            # Single move
            make_move_temp(temp_my_pts, temp_opp_pts, move[0], first_die, temp_my_off)
    
    # Heuristic 1: Safety - count vulnerable checkers
    vulnerable_before = count_vulnerable(my_pts, opp_pts)
    vulnerable_after = count_vulnerable(temp_my_pts, temp_opp_pts)
    score += (vulnerable_before - vulnerable_after) * 2.0
    
    # Heuristic 2: Hits - count opponent checkers hit
    hits = count_hits(my_pts, temp_my_pts, opp_pts, temp_opp_pts)
    score += hits * 3.0
    
    # Heuristic 3: Home board advancement
    home_improvement = evaluate_home_board(temp_my_pts) - evaluate_home_board(my_pts)
    score += home_improvement * 0.5
    
    # Heuristic 4: Pip count (race position)
    my_pip_before = pip_count(my_pts, my_bar)
    my_pip_after = pip_count(temp_my_pts, my_bar)
    opp_pip = pip_count(opp_pts, opp_bar)
    
    # If we're ahead in race, reduce pip count is good
    if my_pip_before < opp_pip:
        score += (my_pip_before - my_pip_after) * 0.1
    else:
        # Behind in race, be more aggressive
        score += (my_pip_before - my_pip_after) * 0.05
        if hits > 0:
            score += hits * 1.0  # Extra weight for hits when behind
    
    # Heuristic 5: Bearing off readiness
    if can_bear_off(temp_my_pts, temp_my_off):
        score += 5.0
    
    # Heuristic 6: Avoid being hit
    if my_bar == 0 and count_vulnerable(temp_my_pts, temp_opp_pts) > count_vulnerable(my_pts, opp_pts):
        score -= 2.0
    
    # Heuristic 7: Hit opponent blots in their home board
    for i in range(6):  # Opponent home board (points 0-5 from our perspective)
        if opp_pts[i] == 1 and temp_opp_pts[i] == 0:
            score += 2.0
    
    # Heuristic 8: Stack penalty (too many checkers on one point)
    for point in temp_my_pts:
        if point > 3:
            score -= (point - 3) * 0.5
    
    # Heuristic 9: Prime building (consecutive points)
    score += evaluate_primes(temp_my_pts) * 0.3
    
    return score


def count_vulnerable(my_pts: List[int], opp_pts: List[int]) -> int:
    """
    Count vulnerable checkers (single checkers that can be hit).
    """
    count = 0
    for i in range(24):
        if my_pts[i] == 1 and opp_pts[i] == 0:
            # Check if opponent can hit from various positions
            # Simplified: just count single checkers
            count += 1
    return count


def count_hits(my_pts_before: List[int], my_pts_after: List[int], 
               opp_pts_before: List[int], opp_pts_after: List[int]) -> int:
    """
    Count how many opponent checkers were hit.
    """
    hits = 0
    for i in range(24):
        if opp_pts_before[i] == 1 and opp_pts_after[i] == 0:
            hits += 1
    return hits


def evaluate_home_board(my_pts: List[int]) -> float:
    """
    Evaluate the strength of the home board.
    """
    score = 0.0
    for i in range(6):  # Home board points
        if my_pts[i] >= 2:
            score += 1.0
        if my_pts[i] >= 3:
            score += 0.5
    return score


def evaluate_primes(my_pts: List[int]) -> int:
    """
    Count consecutive points (primes) for blocking.
    """
    primes = 0
    consecutive = 0
    for i in range(24):
        if my_pts[i] >= 2:
            consecutive += 1
            if consecutive >= 6:
                primes += 1
        else:
            consecutive = 0
    return primes


def pip_count(my_pts: List[int], my_bar: int) -> int:
    """
    Calculate pip count (total distance to bear off).
    """
    pip = my_bar * 25  # Bar is position 24, so 25 pips
    for i in range(24):
        pip += my_pts[i] * (i + 1)
    return pip


def format_move(move: List[int], dice: List[int]) -> str:
    """
    Format the move into the required string format.
    """
    if len(dice) == 1:
        die_order = "H"
    else:
        # Determine order based on which die was used first
        # For simplicity, use H for higher die first
        die_order = "H" if dice[0] >= dice[1] else "L"
    
    # Convert move positions to format
    pos1 = move[0]
    pos2 = move[1] if len(move) > 1 else -1
    
    str1 = "P" if pos1 == -1 else (f"A{pos1}" if pos1 >= 0 else "B")
    str2 = "P" if pos2 == -1 else (f"A{pos2}" if pos2 >= 0 else "B")
    
    # Special case: bar moves
    if pos1 == -1 and pos2 == -1:
        return f"{die_order}:P,P"
    
    return f"{die_order}:{str1},{str2}"
