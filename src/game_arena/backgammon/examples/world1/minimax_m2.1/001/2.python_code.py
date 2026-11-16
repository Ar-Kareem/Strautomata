
import random
from typing import List, Tuple, Dict

def evaluate_move(state: Dict, from_pos: str, die: int, is_higher_first: bool) -> float:
    """
    Evaluate the quality of a potential move.
    
    Args:
        state: Current game state
        from_pos: Starting position ('A0'..'A23', 'B', or 'P')
        die: Die value to use
        is_higher_first: Whether higher die is played first
    
    Returns:
        Score representing move quality (higher is better)
    """
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    
    # Handle bar moves
    if from_pos == 'B':
        dest = 24 - die  # Bar moves go to destination based on die
        
        # Check if move is legal
        if dest < 0 or dest > 23:
            return -1000  # Invalid destination
        
        opp_on_dest = opp_pts[dest]
        if opp_on_dest >= 2:
            return -1000  # Cannot move onto occupied point
        
        # Great move if it hits and is safe
        if opp_on_dest == 1:
            # Check safety of the hit
            if is_safe(state, dest, True):
                return 1000 + 100 * (6 - die)  # Prefer larger hits
        
        # Good move if it lands on own point
        if my_pts[dest] > 0:
            return 800 + 50 * my_pts[dest]
        
        # Good to advance
        return 500 + 20 * (6 - die)
    
    # Handle pass
    if from_pos == 'P':
        return 0
    
    # Parse position
    if not from_pos.startswith('A'):
        return -1000
    
    try:
        point = int(from_pos[1:])
    except:
        return -1000
    
    if point < 0 or point > 23:
        return -1000
    
    if my_pts[point] == 0:
        return -1000  # No checker to move
    
    # Calculate destination (moving toward 0)
    dest = point - die
    if dest < 0:
        # Bear off move
        if can_bear_off(state):
            return 700 + 50 * (6 - die)  # Prefer bearing off with larger dice
        else:
            return -1000  # Cannot bear off yet
    
    opp_on_dest = opp_pts[dest]
    if opp_on_dest >= 2:
        return -1000  # Cannot move onto occupied point
    
    # Evaluate the move
    score = 0
    
    # Hitting evaluation
    if opp_on_dest == 1:
        if is_safe(state, dest, True):
            score += 1000 + 50 * (6 - die)
        else:
            score += 200  # Hit even if risky
    
    # Point building evaluation
    if my_pts[dest] > 0:
        score += 800 + 30 * my_pts[dest]  # Good to build existing points
    
    # Safety of destination
    if my_pts[dest] + 1 >= 2:  # Will have at least 2 checkers
        score += 400
    
    # Advance checkers toward bear-off
    distance_advancement = die
    if dest <= 5:  # In home board
        distance_advancement *= 2  # Double weight for home board progress
    
    score += 100 * distance_advancement
    
    # Strategic considerations
    # Avoid leaving blots (exposed single checkers)
    if my_pts[point] == 1:
        # Moving from a blot is good
        score += 50
    
    # Prefer moves that create anchors (points in opponent's home board)
    if dest >= 18 and my_pts[dest] + 1 == 1:
        score += 300  # Create an anchor
    
    # Priming: build consecutive points
    if can_extend_prime(state, dest):
        score += 200
    
    return score

def is_safe(state: Dict, point: int, is_mine: bool) -> bool:
    """Check if a point is safe from being hit."""
    pts = state['my_pts'] if is_mine else state['opp_pts']
    opp_pts = state['opp_pts'] if is_mine else state['my_pts']
    
    # Check surrounding points for opponent checkers
    for offset in range(-5, 6):
        if offset == 0:
            continue
        check_point = point + offset
        if 0 <= check_point <= 23:
            if opp_pts[check_point] >= 2:
                return False
    
    return True

def can_extend_prime(state: Dict, new_point: int) -> bool:
    """Check if adding a checker at new_point extends a prime."""
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    
    # Check if we have consecutive points around new_point
    for offset in range(1, 6):
        # Check left side
        left = new_point - offset
        if left >= 0 and my_pts[left] > 0 and opp_pts[left] == 0:
            # Found consecutive point
            return True
        
        # Check right side
        right = new_point + offset
        if right < 24 and my_pts[right] > 0 and opp_pts[right] == 0:
            return True
    
    return False

def can_bear_off(state: Dict) -> bool:
    """Check if player can bear off checkers."""
    my_pts = state['my_pts']
    bar = state['my_bar']
    
    # All checkers must be in home board (0-5)
    total = bar
    for i in range(6, 24):
        total += my_pts[i]
    
    return total == 0

def get_bar_moves(state: Dict, die: int) -> List[str]:
    """Get legal bar moves for a given die."""
    moves = []
    if state['my_bar'] > 0:
        dest = 24 - die
        if 0 <= dest <= 23:
            if state['opp_pts'][dest] < 2:
                moves.append('B')
    return moves

def get_point_moves(state: Dict, from_point: int, die: int) -> List[str]:
    """Get legal moves from a specific point with a given die."""
    moves = []
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    
    if my_pts[from_point] == 0:
        return moves
    
    dest = from_point - die
    if dest < 0:
        if can_bear_off(state):
            moves.append(f'A{from_point}')
        return moves
    
    if dest >= 0 and dest <= 23:
        if opp_pts[dest] < 2:
            moves.append(f'A{from_point}')
    
    return moves

def evaluate_state(state: Dict) -> float:
    """Evaluate the overall quality of the current position."""
    score = 0
    
    # Count checkers in different regions
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    
    # My position scoring
    for i in range(24):
        count = my_pts[i]
        if count > 0:
            # Prefer checkers closer to bearing off
            position_score = (24 - i) * 10
            
            # Home board bonus
            if i <= 5:
                position_score *= 2
            
            # Safety bonus for multiple checkers
            if count >= 2:
                position_score += 50 * count
            
            score += count * position_score
    
    # Penalty for checkers on bar
    score -= state['my_bar'] * 200
    
    # Bonus for checkers off board
    score += state['my_off'] * 500
    
    # Opponent position scoring (negative)
    for i in range(24):
        count = opp_pts[i]
        if count > 0:
            # Penalty for opponent checkers close to bearing off
            position_score = i * 5
            if i >= 18:  # Opponent in their home board
                position_score *= 2
            score -= count * position_score
    
    # Penalty for opponent checkers on bar
    score += state['opp_bar'] * 100
    
    # Penalty for opponent checkers off board (negative)
    score -= state['opp_off'] * 500
    
    return score

def generate_all_moves(state: Dict, dice: List[int]) -> List[Tuple[str, str, str]]:
    """
    Generate all possible move sequences.
    
    Returns:
        List of tuples: (order, from1, from2)
    """
    moves = []
    bar = state['my_bar']
    
    if bar > 0:
        # Must move from bar first
        bar_moves = []
        for die in dice:
            legal_moves = get_bar_moves(state, die)
            bar_moves.extend(legal_moves)
        
        if not bar_moves:
            # No legal bar moves
            return [('H', 'P', 'P')]
        
        # Generate combinations of bar and point moves
        for first_move in bar_moves:
            remaining_dice = [d for d in dice]
            if first_move == 'B':
                # Find which die was used
                used_die = None
                for i, die in enumerate(dice):
                    dest = 24 - die
                    if 0 <= dest <= 23 and state['opp_pts'][dest] < 2:
                        used_die = remaining_dice.pop(i)
                        break
            
            if remaining_dice:
                # Try second move
                second_moves = generate_second_move(state, remaining_dice)
                for second_move in second_moves:
                    order = 'H' if first_move == 'B' else 'L'
                    moves.append((order, first_move, second_move))
            else:
                moves.append(('H', first_move, 'P'))
    
    else:
        # No bar checkers, can move from points
        all_moves = []
        
        for from_point in range(24):
            if state['my_pts'][from_point] > 0:
                for die in dice:
                    point_moves = get_point_moves(state, from_point, die)
                    all_moves.extend(point_moves)
        
        if not all_moves:
            return [('H', 'P', 'P')]
        
        # Generate combinations of two moves
        used_combinations = set()
        for move1 in all_moves:
            remaining_dice = dice.copy()
            
            # Simulate move1 to update state
            simulated_state = simulate_move(state, move1, remaining_dice[0] if remaining_dice else None)
            
            remaining_dice_used = []
            if remaining_dice:
                # Find which die was used
                for i, die in enumerate(remaining_dice):
                    if is_legal_move(state, move1, die):
                        remaining_dice_used.append(remaining_dice.pop(i))
                        break
            
            if remaining_dice:
                for move2 in all_moves:
                    if move2 == move1:
                        # Check if we have multiple checkers to move from same point
                        if state['my_pts'][int(move1[1:])] < 2:
                            continue
                    
                    # Check if move2 is legal with remaining dice
                    for die in remaining_dice:
                        if is_legal_move(state, move2, die):
                            # Both moves possible
                            key = tuple(sorted([move1, move2]))
                            if key not in used_combinations:
                                used_combinations.add(key)
                                order = 'H' if dice[0] > dice[1] else 'L'
                                moves.append((order, move1, move2))
                            break
            else:
                # Only one move possible - must use higher die
                if dice:
                    order = 'H'
                    moves.append((order, move1, 'P'))
    
    return moves

def is_legal_move(state: Dict, from_pos: str, die: int) -> bool:
    """Check if a move is legal with a given die."""
    if from_pos == 'B':
        dest = 24 - die
        return 0 <= dest <= 23 and state['opp_pts'][dest] < 2
    
    if from_pos == 'P':
        return True
    
    if not from_pos.startswith('A'):
        return False
    
    try:
        point = int(from_pos[1:])
    except:
        return False
    
    if point < 0 or point > 23:
        return False
    
    if state['my_pts'][point] == 0:
        return False
    
    dest = point - die
    if dest < 0:
        return can_bear_off(state)
    
    return 0 <= dest <= 23 and state['opp_pts'][dest] < 2

def simulate_move(state: Dict, from_pos: str, die: int) -> Dict:
    """Create a simulated state after making a move."""
    new_state = state.copy()
    new_state['my_pts'] = state['my_pts'].copy()
    new_state['opp_pts'] = state['opp_pts'].copy()
    
    if from_pos == 'B':
        new_state['my_bar'] -= 1
        dest = 24 - die
        if 0 <= dest <= 23:
            if new_state['opp_pts'][dest] == 1:
                new_state['opp_pts'][dest] = 0
                new_state['opp_bar'] += 1
            new_state['my_pts'][dest] += 1
    
    elif from_pos.startswith('A'):
        try:
            point = int(from_pos[1:])
        except:
            return state
        
        new_state['my_pts'][point] -= 1
        dest = point - die
        if dest >= 0:
            if new_state['opp_pts'][dest] == 1:
                new_state['opp_pts'][dest] = 0
                new_state['opp_bar'] += 1
            new_state['my_pts'][dest] += 1
        else:
            new_state['my_off'] += 1
    
    return new_state

def generate_second_move(state: Dict, remaining_dice: List[int]) -> List[str]:
    """Generate possible second moves after first move."""
    moves = []
    
    for from_point in range(24):
        if state['my_pts'][from_point] > 0:
            for die in remaining_dice:
                point_moves = get_point_moves(state, from_point, die)
                moves.extend(point_moves)
    
    if not moves:
        moves.append('P')
    
    return moves

def policy(state: dict) -> str:
    """
    Main policy function that returns the best move string.
    
    Args:
        state: Current game state dictionary
    
    Returns:
        Move string in format '<ORDER>:<FROM1>,<FROM2>'
    """
    dice = state['dice']
    
    if not dice:
        return 'H:P,P'
    
    # Generate all possible moves
    all_moves = generate_all_moves(state, dice)
    
    if not all_moves:
        return 'H:P,P'
    
    # Evaluate each move sequence
    best_move = None
    best_score = float('-inf')
    
    for order, from1, from2 in all_moves:
        # Evaluate first move
        die1 = dice[0] if order == 'H' else dice[-1]
        score1 = evaluate_move(state, from1, die1, order == 'H')
        
        # Simulate first move
        simulated_state = simulate_move(state, from1, die1)
        
        # Evaluate second move
        die2 = dice[-1] if order == 'H' else dice[0]
        if from2 != 'P':
            score2 = evaluate_move(simulated_state, from2, die2, order == 'H')
        else:
            score2 = 0
        
        # Calculate total score
        total_score = score1 + score2
        
        # Add state evaluation for strategic awareness
        if from2 != 'P':
            final_state = simulate_move(simulated_state, from2, die2)
            strategic_score = evaluate_state(final_state) * 0.1
            total_score += strategic_score
        else:
            strategic_score = evaluate_state(simulated_state) * 0.05
            total_score += strategic_score
        
        # Add small random factor for variety
        total_score += random.uniform(-5, 5)
        
        if total_score > best_score:
            best_score = total_score
            best_move = (order, from1, from2)
    
    if best_move is None:
        return 'H:P,P'
    
    order, from1, from2 = best_move
    return f'{order}:{from1},{from2}'
