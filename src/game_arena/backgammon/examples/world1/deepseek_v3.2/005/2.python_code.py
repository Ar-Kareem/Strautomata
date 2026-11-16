
import copy

def policy(state):
    # ---------- Helper Functions ----------
    def is_legal_move(state, start, die):
        """Check if a single move is legal."""
        if start == 'B':
            if state['my_bar'] == 0:
                return False
            dest = die - 1  # entry point from bar
            if dest < 0 or dest > 23:
                return False
            if state['opp_pts'][dest] >= 2:
                return False
            return True
        else:
            s = start
            if state['my_pts'][s] == 0:
                return False
            
            # Check if all checkers are in home board (indices 18-23)
            bearoff_allowed = True
            for i in range(18):
                if state['my_pts'][i] > 0:
                    bearoff_allowed = False
                    break
            
            dest = s - die
            if dest < 0:
                # Bear-off move
                return bearoff_allowed
            else:
                # Normal move
                if state['opp_pts'][dest] >= 2:
                    return False
                if bearoff_allowed and dest < 18:
                    return False
                return True
    
    def legal_single_moves(state, die):
        """Return list of legal start points for a given die."""
        moves = []
        if state['my_bar'] > 0:
            if is_legal_move(state, 'B', die):
                moves.append('B')
        else:
            for i in range(24):
                if state['my_pts'][i] > 0 and is_legal_move(state, i, die):
                    moves.append(i)
        return moves
    
    def apply_move(state, start, die):
        """Apply a single move and return a new state (assumes move is legal)."""
        new_state = copy.deepcopy(state)
        if start == 'B':
            new_state['my_bar'] -= 1
            dest = die - 1
            if new_state['opp_pts'][dest] == 1:
                new_state['opp_pts'][dest] = 0
                new_state['opp_bar'] += 1
            new_state['my_pts'][dest] += 1
        else:
            s = start
            new_state['my_pts'][s] -= 1
            dest = s - die
            if dest < 0:
                new_state['my_off'] += 1
            else:
                if new_state['opp_pts'][dest] == 1:
                    new_state['opp_pts'][dest] = 0
                    new_state['opp_bar'] += 1
                new_state['my_pts'][dest] += 1
        return new_state
    
    def evaluate(state):
        """Evaluate the state from our perspective (higher is better)."""
        my_pts = state['my_pts']
        opp_pts = state['opp_pts']
        my_bar = state['my_bar']
        opp_bar = state['opp_bar']
        my_off = state['my_off']
        opp_off = state['opp_off']
        
        # Pip counts (lower is better for us)
        my_pip = sum((i + 1) * my_pts[i] for i in range(24)) + 25 * my_bar
        opp_pip = sum((24 - i) * opp_pts[i] for i in range(24)) + 25 * opp_bar
        
        # Blocking points (points with >=2 checkers)
        my_blocking = sum(1 for i in range(24) if my_pts[i] >= 2)
        
        # Blots (single checkers vulnerable to being hit)
        my_blots = sum(1 for i in range(24) if my_pts[i] == 1)
        
        # Home board strength (points in our home board with >=2 checkers)
        home_board = list(range(18, 24))
        my_home_blocking = sum(1 for i in home_board if my_pts[i] >= 2)
        
        # Score components (weights determined empirically)
        score = 0
        score += 0.15 * (opp_pip - my_pip)          # race advantage
        score += 1.5 * (my_off - opp_off)           # borne off checkers
        score += 0.6 * my_blocking                  # general blocking
        score += 0.8 * my_home_blocking             # home board blocking
        score -= 0.4 * my_blots                     # avoid blots
        score += 0.7 * opp_bar                      # opponent on bar
        return score
    
    def format_move(order, move1, move2):
        """Convert move representation to string."""
        def fmt(m):
            if m == 'B' or m == 'P':
                return m
            else:
                return f'A{m}'
        return f'{order}:{fmt(move1)},{fmt(move2)}'
    
    # ---------- Main Logic ----------
    dice = state['dice']
    if not dice:
        return 'H:P,P'
    
    if len(dice) == 1:
        die = dice[0]
        moves = legal_single_moves(state, die)
        if not moves:
            return 'H:P,P'
        # Evaluate each single move
        best_score = -float('inf')
        best_move = None
        for start in moves:
            new_state = apply_move(state, start, die)
            score = evaluate(new_state)
            if score > best_score:
                best_score = score
                best_move = start
        return format_move('H', best_move, 'P')
    
    # Two dice
    a, b = dice
    higher = max(a, b)
    lower = min(a, b)
    
    # Generate all sequences for both orders
    best_score = -float('inf')
    best_sequence = None  # (order, move1, move2)
    
    for order, (first_die, second_die) in [('H', (higher, lower)), ('L', (lower, higher))]:
        first_moves = legal_single_moves(state, first_die)
        for start1 in first_moves:
            state1 = apply_move(state, start1, first_die)
            second_moves = legal_single_moves(state1, second_die)
            for start2 in second_moves:
                state2 = apply_move(state1, start2, second_die)
                score = evaluate(state2)
                if score > best_score:
                    best_score = score
                    best_sequence = (order, start1, start2)
    
    if best_sequence:
        order, start1, start2 = best_sequence
        return format_move(order, start1, start2)
    
    # No legal sequence for two dice -> try single die
    # Try higher die first (rules: must play higher if possible)
    higher_moves = legal_single_moves(state, higher)
    if higher_moves:
        best_score = -float('inf')
        best_move = None
        for start in higher_moves:
            new_state = apply_move(state, start, higher)
            score = evaluate(new_state)
            if score > best_score:
                best_score = score
                best_move = start
        return format_move('H', best_move, 'P')
    
    # Try lower die
    lower_moves = legal_single_moves(state, lower)
    if lower_moves:
        best_score = -float('inf')
        best_move = None
        for start in lower_moves:
            new_state = apply_move(state, start, lower)
            score = evaluate(new_state)
            if score > best_score:
                best_score = score
                best_move = start
        return format_move('L', best_move, 'P')
    
    # No legal moves at all
    return 'H:P,P'
