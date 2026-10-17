
import random
from typing import List, Tuple, Optional
import copy

def policy(state: dict) -> str:
    """
    Smart Backgammon policy using heuristic evaluation.
    Returns move string in format: <ORDER>:<FROM1>,<FROM2>
    """
    dice = state['dice']
    
    # If no dice or already played, return pass
    if not dice or len(dice) == 0:
        return "H:P,P"
    
    # Generate all legal moves
    legal_moves = generate_legal_moves(state)
    
    if not legal_moves:
        return "H:P,P"
    
    # Score each move and pick the best
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        score = evaluate_move(state, move, dice)
        if score > best_score:
            best_score = score
            best_move = move
    
    # If no good move found, return a random legal move
    if best_move is None:
        best_move = random.choice(legal_moves)
    
    return format_move(best_move, dice)


def generate_legal_moves(state: dict) -> List[List[str]]:
    """Generate all legal move sequences."""
    moves = []
    dice = sorted(state['dice'], reverse=True)  # Higher die first
    my_pts = state['my_pts'].copy()
    opp_pts = state['opp_pts'].copy()
    my_bar = state['my_bar']
    
    # Must play bar moves first if any on bar
    if my_bar > 0:
        bar_moves = generate_bar_moves(state, dice)
        for bar_move in bar_moves:
            moves.append([bar_move])
    else:
        # Generate all possible moves from points
        moves = generate_point_moves(state, dice)
    
    return moves


def generate_bar_moves(state: dict, dice: List[int]) -> List[str]:
    """Generate legal moves from the bar."""
    moves = []
    opp_pts = state['opp_pts']
    
    for die in dice:
        dest = die - 1  # Bar enters at opponent's 1-point (our 24 -> 0)
        if 0 <= dest <= 23:
            if opp_pts[dest] < 2:  # Can move if opponent has 0-1 checkers
                moves.append("B")
    
    return moves


def generate_point_moves(state: dict, dice: List[int]) -> List[List[str]]:
    """Generate all legal move sequences from points."""
    moves = []
    my_pts = state['my_pts'].copy()
    opp_pts = state['opp_pts'].copy()
    my_bar = state['my_bar']
    
    # Must be able to bear off if all checkers in home board
    can_bear_off = all(my_pts[i] == 0 for i in range(6, 24))
    
    # Generate all single moves first
    single_moves = []
    for from_pt in range(24):
        if my_pts[from_pt] > 0:
            for die in dice:
                to_pt = from_pt - die
                
                if to_pt < 0:
                    # Bearing off
                    if can_bear_off:
                        single_moves.append((from_pt, 'off'))
                elif opp_pts[to_pt] < 2:
                    # Regular move
                    single_moves.append((from_pt, to_pt))
    
    # Generate combinations for playing both dice
    for move1 in single_moves:
        # Create temporary state after first move
        temp_state = apply_move_temporary(state, move1)
        
        for move2 in single_moves:
            if move1 != move2:  # Can't use same checker twice
                if is_legal_combined(state, move1, move2):
                    # Format moves
                    from1 = format_from(move1[0])
                    from2 = format_from(move2[0])
                    
                    # Determine order (H = higher die first)
                    die1 = dice[0] if move1[1] == 'off' or move1[0] - move1[1] == dice[0] else dice[1]
                    die2 = dice[1] if die1 == dice[0] else dice[0]
                    
                    if die1 >= die2:
                        moves.append([from1, from2])
                    else:
                        moves.append([from2, from1])
    
    # Add single moves (when can't play both dice)
    for move in single_moves:
        from_pt = format_from(move[0])
        moves.append([from_pt, 'P'])
    
    return moves


def apply_move_temporary(state: dict, move: Tuple) -> dict:
    """Create temporary state after applying a move."""
    temp_state = {
        'my_pts': state['my_pts'].copy(),
        'opp_pts': state['opp_pts'].copy(),
        'my_bar': state['my_bar'],
        'opp_bar': state['opp_bar'],
        'my_off': state['my_off'],
        'opp_off': state['opp_off']
    }
    
    from_pt, to_pt = move
    temp_state['my_pts'][from_pt] -= 1
    
    if to_pt == 'off':
        temp_state['my_off'] += 1
    else:
        temp_state['my_pts'][to_pt] += 1
        # Handle hit if applicable
        if temp_state['opp_pts'][to_pt] == 1:
            temp_state['opp_pts'][to_pt] = 0
            temp_state['opp_bar'] += 1
    
    return temp_state


def is_legal_combined(state: dict, move1: Tuple, move2: Tuple) -> bool:
    """Check if two moves can be played together legally."""
    # Check if moves use different checkers
    if move1[0] == move2[0]:
        if state['my_pts'][move1[0]] < 2:
            return False
    
    # Check if destination conflicts
    if move1[1] != 'off' and move2[1] != 'off':
        if move1[1] == move2[1]:
            return False
    
    return True


def evaluate_move(state: dict, moves: List[str], dice: List[int]) -> float:
    """Evaluate the quality of a move sequence."""
    temp_state = apply_moves(state, moves, dice)
    
    # Calculate various heuristics
    score = 0
    
    # 1. Pip count evaluation (lower is better, so negate)
    my_pips = calculate_pips(temp_state['my_pts'], temp_state['my_bar'])
    opp_pips = calculate_pips(temp_state['opp_pts'], temp_state['opp_bar'])
    pip_diff = opp_pips - my_pips
    score += pip_diff * 0.5
    
    # 2. Board control - count made points
    my_points = sum(1 for i, count in enumerate(temp_state['my_pts']) if count >= 2)
    score += my_points * 10
    
    # 3. Prime evaluation (consecutive made points)
    prime_score = calculate_prime_score(temp_state['my_pts'])
    score += prime_score * 15
    
    # 4. Blot safety (penalize exposed checkers)
    blot_penalty = calculate_blot_penalty(temp_state, state)
    score -= blot_penalty
    
    # 5. Bearing off progress
    score += temp_state['my_off'] * 50
    score -= temp_state['opp_off'] * 50
    
    # 6. Bar evaluation (penalize checkers on bar)
    score -= temp_state['my_bar'] * 30
    score += temp_state['opp_bar'] * 30
    
    # 7. Home board concentration (good when bearing off)
    home_board = sum(temp_state['my_pts'][:6])
    total_checkers = sum(temp_state['my_pts']) + temp_state['my_bar']
    if total_checkers > 0:
        home_concentration = home_board / total_checkers
        score += home_concentration * 20
    
    # 8. Position in opponent's home board (good for hitting)
    opp_home_board = sum(temp_state['opp_pts'][18:24])
    score += opp_home_board * 5
    
    return score


def calculate_pips(pts: List[int], bar: int) -> int:
    """Calculate total pips for a player's checkers."""
    pips = bar * 25  # Each bar checker needs 25 pips to bear off
    for i, count in enumerate(pts):
        pips += count * (i + 1)
    return pips


def calculate_prime_score(pts: List[int]) -> int:
    """Calculate score for prime formation (consecutive made points)."""
    max_prime = 0
    current_prime = 0
    
    for i, count in enumerate(pts):
        if count >= 2:
            current_prime += 1
            max_prime = max(max_prime, current_prime)
        else:
            current_prime = 0
    
    return max_prime


def calculate_blot_penalty(temp_state: dict, original_state: dict) -> float:
    """Calculate penalty for exposed blots."""
    penalty = 0
    
    # Our blots that can be hit
    for i, count in enumerate(temp_state['my_pts']):
        if count == 1:
            # Check if this point is vulnerable
            vulnerability = 1
            for j in range(6):  # Check opponent's potential moves
                if i + j + 1 < 24:
                    if temp_state['opp_pts'][i + j + 1] >= 1:
                        vulnerability += temp_state['opp_pts'][i + j + 1] * 2
            penalty += vulnerability * 5
    
    # Bonus for hitting opponent blots
    for i, count in enumerate(temp_state['opp_pts']):
        if count == 1 and original_state['opp_pts'][i] == 1:
            # We hit them!
            penalty -= 30
    
    return penalty


def apply_moves(state: dict, moves: List[str], dice: List[int]) -> dict:
    """Apply a sequence of moves to get resulting state."""
    temp_state = {
        'my_pts': state['my_pts'].copy(),
        'opp_pts': state['opp_pts'].copy(),
        'my_bar': state['my_bar'],
        'opp_bar': state['opp_bar'],
        'my_off': state['my_off'],
        'opp_off': state['opp_off']
    }
    
    dice_played = []
    
    for move_from in moves:
        if move_from == 'P':
            continue
            
        die = None
        for d in dice:
            if d not in dice_played:
                die = d
                break
        
        if die is None:
            continue
        
        dice_played.append(die)
        
        # Parse move
        if move_from == 'B':
            # Bar move
            temp_state['my_bar'] -= 1
            dest = die - 1
        else:
            from_pt = int(move_from[1:])
            temp_state['my_pts'][from_pt] -= 1
            dest = from_pt - die
        
        # Handle destination
        if dest < 0:
            # Bear off
            temp_state['my_off'] += 1
        else:
            # Move to point
            temp_state['my_pts'][dest] += 1
            
            # Handle hit
            if temp_state['opp_pts'][dest] == 1:
                temp_state['opp_pts'][dest] = 0
                temp_state['opp_bar'] += 1
    
    return temp_state


def format_from(from_pt: int) -> str:
    """Format point index as string."""
    return f"A{from_pt}"


def format_move(moves: List[str], dice: List[int]) -> str:
    """Format move sequence as return string."""
    # Determine order based on which die is used first
    # H = higher die first, L = lower die first
    # We need to figure out which die is used for the first move
    
    # Default to higher die first
    order = 'H'
    
    # Format the move string
    from1 = moves[0] if len(moves) > 0 else 'P'
    from2 = moves[1] if len(moves) > 1 else 'P'
    
    return f"{order}:{from1},{from2}"
