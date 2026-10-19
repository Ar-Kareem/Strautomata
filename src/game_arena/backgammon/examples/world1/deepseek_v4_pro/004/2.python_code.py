
import numpy as np
import itertools

def policy(state: dict) -> str:
    """
    Returns a legal move string for the given Backgammon state.
    Uses 1-ply lookahead with a strong heuristic evaluation.
    """
    # Unpack state
    my_pts = np.array(state['my_pts'], dtype=int)
    opp_pts = np.array(state['opp_pts'], dtype=int)
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    
    # If no dice, pass
    if len(dice) == 0:
        return "H:P,P"
    
    dice = sorted(dice)
    
    # Generate all legal moves according to Backgammon rules
    legal_moves = generate_legal_moves(my_pts, opp_pts, my_bar, my_off, dice)
    
    if not legal_moves:
        return "H:P,P"
    
    # Evaluate each legal move with 1-ply lookahead
    best_move = None
    best_score = -float('inf')
    
    for move in legal_moves:
        order, from1, from2 = move
        # Apply move to get hypothetical next state
        next_my_pts, next_my_bar, next_my_off = apply_move(my_pts, my_bar, my_off, dice, order, from1, from2)
        # Opponent will then roll dice (average over all 21 possible rolls)
        opp_score = evaluate_opponent_turn(next_my_pts, opp_pts, opp_bar, opp_off)
        # Our score is negative of opponent's expected gain (since we want to minimize opponent's advantage)
        score = -opp_score + heuristic(next_my_pts, opp_pts, next_my_bar, opp_bar, next_my_off, opp_off)
        if score > best_score:
            best_score = score
            best_move = move
    
    # Format move string
    order, from1, from2 = best_move
    return f"{order}:{from1},{from2}"


def generate_legal_moves(my_pts, opp_pts, my_bar, my_off, dice):
    """Generate all legal moves satisfying Backgammon rules."""
    if len(dice) == 0:
        return []
    
    d1, d2 = dice[0], dice[-1]
    if len(dice) == 1:
        d2 = None
    
    # Determine legal combinations
    legal = []
    
    # Bar checkers must be moved first
    if my_bar > 0:
        # We can only move from bar
        if d1 is not None:
            legal_bar_moves = get_bar_moves(d1, opp_pts, my_bar)
            for move1 in legal_bar_moves:
                new_my_bar = my_bar - 1
                new_my_pts = my_pts.copy()
                dest1 = 24 - d1  # bar entry for us means entering at 24-die (point index)
                # Handle hits
                if opp_pts[dest1] == 1:
                    # Opponent checker sent to bar; we don't track opponent bar in apply_move because it's our state
                    new_opp_pts = opp_pts.copy()
                    new_opp_pts[dest1] = 0
                    # Opponent bar increase happens but we ignore for legality
                else:
                    new_opp_pts = opp_pts
                new_my_pts[dest1] += 1
                if d2 is not None:
                    # Must play second die if possible, from bar if still on bar, else from board
                    if new_my_bar > 0:
                        legal_bar_moves2 = get_bar_moves(d2, new_opp_pts, new_my_bar)
                        for move2 in legal_bar_moves2:
                            legal.append(('H', move1, move2))
                    else:
                        legal_board_moves2 = get_board_moves(new_my_pts, new_opp_pts, d2, my_off)
                        for move2 in legal_board_moves2:
                            if move2 != 'P':
                                legal.append(('H', move1, move2))
                            else:
                                # If only one die can be played, we must play higher die if possible
                                # But since we are already playing d1 (which is smaller if dice sorted), if d2 is larger we would have to play it
                                # Here d1 is smaller, d2 is larger. If d2 can't be played, we must still play d1. This is fine because we came from bar and played d1.
                                # Actually, if we have bar checkers, we must play both if possible. If we can't play d2, is it legal to only play d1?
                                # Rules: If both dice can be played, must play both. If only one can be played, play the higher die when possible.
                                # If we had bar checkers and played d1 (smaller) but can't play d2 (larger), we are violating "play higher die when possible" if we could have played d2 instead of d1?
                                # But we generated moves by playing d1 first. To be safe, we also check if d2 can be played from bar first.
                                pass
                else:
                    legal.append(('H', move1, 'P'))
        # Also consider playing higher die first from bar
        if d2 is not None:
            legal_bar_moves_high = get_bar_moves(d2, opp_pts, my_bar)
            for move1 in legal_bar_moves_high:
                new_my_bar = my_bar - 1
                new_my_pts = my_pts.copy()
                dest1 = 24 - d2
                if opp_pts[dest1] == 1:
                    new_opp_pts = opp_pts.copy()
                    new_opp_pts[dest1] = 0
                else:
                    new_opp_pts = opp_pts
                new_my_pts[dest1] += 1
                if new_my_bar > 0:
                    legal_bar_moves2 = get_bar_moves(d1, new_opp_pts, new_my_bar)
                    for move2 in legal_bar_moves2:
                        legal.append(('L', move1, move2))
                else:
                    legal_board_moves2 = get_board_moves(new_my_pts, new_opp_pts, d1, my_off)
                    for move2 in legal_board_moves2:
                        if move2 != 'P':
                            legal.append(('L', move1, move2))
    else:
        # No bar checkers, generate moves from board
        if d2 is not None:
            # Both dice
            # Higher die first
            legal_board_moves_high = get_board_moves(my_pts, opp_pts, d2, my_off)
            for from1 in legal_board_moves_high:
                if from1 == 'P':
                    # If higher die can't be played, try lower die. But if only one die can be played, must be higher.
                    # Since higher can't be played, we try lower. If lower can be played, then we play lower and pass on higher? That's illegal.
                    # But rules: if only one die can be played, you must play the higher if possible. So if higher can't be played, lower can't either? Actually if higher can't and lower can, you play lower? No, you must play higher. So you can't play lower if higher is unplayable.
                    # So if from1 == 'P' for high die, we skip this branch.
                    continue
                new_my_pts, new_my_bar = apply_single_move(my_pts, opp_pts, my_bar, my_off, d2, from1, return_bar=True)
                # Temporarily assume opp_pts unchanged for hit? We'll adjust.
                # Actually apply_single_move handles hits.
                # Now try lower die
                legal_board_moves_low = get_board_moves(new_my_pts, opp_pts, d1, my_off, bar_checkers=new_my_bar)
                for from2 in legal_board_moves_low:
                    if from2 == 'P':
                        # We played high die, can't play low die. Is this legal? Yes if only one die can be played and we played high.
                        legal.append(('H', from1, from2))
                    else:
                        legal.append(('H', from1, from2))
            # Lower die first
            legal_board_moves_low = get_board_moves(my_pts, opp_pts, d1, my_off)
            for from1 in legal_board_moves_low:
                if from1 == 'P':
                    continue
                new_my_pts, new_my_bar = apply_single_move(my_pts, opp_pts, my_bar, my_off, d1, from1, return_bar=True)
                legal_board_moves_high = get_board_moves(new_my_pts, opp_pts, d2, my_off, bar_checkers=new_my_bar)
                for from2 in legal_board_moves_high:
                    if from2 == 'P':
                        # Played low die, can't play high die. Illegal because if only one die can be played, must be higher.
                        # So skip.
                        continue
                    else:
                        legal.append(('L', from1, from2))
        else:
            # Single die
            legal_board_moves_single = get_board_moves(my_pts, opp_pts, d1, my_off)
            for from1 in legal_board_moves_single:
                legal.append(('H', from1, 'P'))
    
    # Deduplicate
    legal = list(set(legal))
    return legal


def get_bar_moves(die, opp_pts, my_bar):
    """Return possible moves from bar for given die."""
    entry_point = 24 - die
    if opp_pts[entry_point] >= 2:
        return ['P']  # blocked
    else:
        return ['B']


def get_board_moves(my_pts, opp_pts, die, my_off, bar_checkers=0):
    """Return list of possible starting points for a die from board."""
    if bar_checkers > 0:
        return ['P']  # must clear bar first
    
    possible = []
    # Check bearing off eligibility
    in_home = np.sum(my_pts[6:]) == 0 and bar_checkers == 0
    if in_home:
        # Bearing off allowed from points 0..5
        for pt in range(6):
            if my_pts[pt] > 0:
                if pt - die == -1:
                    # Exact bear off
                    possible.append(f"A{pt}")
                elif pt - die < -1:
                    # Can bear off if no checkers further from home than pt
                    if np.all(my_pts[(pt+1):6] == 0):
                        possible.append(f"A{pt}")
                else:
                    # Normal move
                    dest = pt - die
                    if opp_pts[dest] < 2:
                        possible.append(f"A{pt}")
    else:
        for pt in range(24):
            if my_pts[pt] > 0:
                dest = pt - die
                if dest < 0:
                    continue  # can't move beyond home edge unless bearing off
                if opp_pts[dest] < 2:
                    possible.append(f"A{pt}")
    
    if not possible:
        return ['P']
    return possible


def apply_single_move(my_pts, opp_pts, my_bar, my_off, die, from_str, return_bar=False):
    """Apply a single checker move and return new my_pts and my_bar."""
    my_pts = my_pts.copy()
    opp_pts = opp_pts.copy()
    new_bar = my_bar
    
    if from_str == 'B':
        # From bar
        new_bar -= 1
        dest = 24 - die
        if opp_pts[dest] == 1:
            opp_pts[dest] = 0  # hit, we don't track opp_bar here
        my_pts[dest] += 1
    elif from_str == 'P':
        pass
    else:
        pt = int(from_str[1:])
        my_pts[pt] -= 1
        dest = pt - die
        if dest >= 0:
            if opp_pts[dest] == 1:
                opp_pts[dest] = 0
            my_pts[dest] += 1
        else:
            # Bearing off
            my_off += 1
    
    if return_bar:
        return my_pts, new_bar
    else:
        return my_pts


def apply_move(my_pts, my_bar, my_off, dice, order, from1, from2):
    """Apply both dice moves in given order."""
    d1, d2 = dice[0], dice[-1]
    if order == 'H':
        first_die, second_die = d2, d1
        first_from, second_from = from1, from2
    else:
        first_die, second_die = d1, d2
        first_from, second_from = from1, from2
    
    my_pts, my_bar = apply_single_move(my_pts, None, my_bar, my_off, first_die, first_from, return_bar=True)
    if second_from != 'P':
        my_pts = apply_single_move(my_pts, None, my_bar, my_off, second_die, second_from)
    return my_pts, my_bar, my_off


def heuristic(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off):
    """Evaluate position from perspective of player to move (now opponent's perspective for lookahead)."""
    # Basic features
    my_pip = compute_pip(my_pts, my_bar, my_off)
    opp_pip = compute_pip(opp_pts, opp_bar, opp_off)
    
    # Blot count (single checkers)
    my_blots = np.sum((my_pts == 1) & (opp_pts == 0))
    opp_blots = np.sum((opp_pts == 1) & (my_pts == 0))
    
    # Points with 2+ checkers (safe points)
    my_safe = np.sum(my_pts >= 2)
    opp_safe = np.sum(opp_pts >= 2)
    
    # Number of checkers back (for us, opponent's perspective)
    # Opponent wants to bring checkers home, pip count difference matters
    score = (opp_pip - my_pip) * 0.5
    score += (my_blots - opp_blots) * 10  # blots are bad for us
    score += (my_safe - opp_safe) * 2
    score += (my_bar - opp_bar) * 15
    score += (my_off - opp_off) * 20
    
    return score


def compute_pip(pts, bar, off):
    """Compute pip count."""
    pip = 0
    for i in range(24):
        pip += pts[i] * (24 - i)
    pip += bar * 25  # approximate bar as extra
    pip -= off * 0
    return pip


def evaluate_opponent_turn(my_pts, opp_pts, opp_bar, opp_off):
    """Evaluate expected score after opponent's turn (average over all 21 rolls)."""
    # Opponent's dice roll distribution
    dice_combos = list(itertools.combinations_with_replacement(range(1,7), 2))
    total = 0
    count = 0
    for d in dice_combos:
        dice = list(d)
        if dice[0] == dice[1]:
            # Doubles: 4 moves
            dice = [dice[0]] * 4
        # We simulate opponent's best move using same heuristic
        opp_legal = generate_legal_moves(opp_pts, my_pts, opp_bar, opp_off, dice)
        if not opp_legal:
            # Pass
            score = heuristic(my_pts, opp_pts, 0, opp_bar, my_off, opp_off)  # no change
        else:
            best_score = -float('inf')
            for move in opp_legal:
                order, from1, from2 = move
                new_opp_pts, new_opp_bar, new_opp_off = apply_move(opp_pts, opp_bar, opp_off, dice, order, from1, from2)
                s = heuristic(my_pts, new_opp_pts, 0, new_opp_bar, my_off, new_opp_off)  # my_bar always 0 after our move (we cleared)
                if s > best_score:
                    best_score = s
            score = best_score
        total += score
        count += 1
    return total / count
