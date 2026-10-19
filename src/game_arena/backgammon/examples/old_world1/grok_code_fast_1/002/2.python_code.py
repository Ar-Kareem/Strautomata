
import copy

def policy(state):
    moves = state['dice']
    if not moves:
        return "H:P,P"
    
    # Handle bar first if necessary
    if state['my_bar'] > 0:
        q_high = 23 - max(moves)
        if 0 <= q_high < 24 and state['opp_pts'][q_high] < 2:
            if len(moves) == 1:
                return "H:B,P"
            else:
                return "H:B,P"  # Play higher die first arbitrarily for bar
        q_low = 23 - min(moves)
        if len(moves) > 1 and 0 <= q_low < 24 and state['opp_pts'][q_low] < 2:
            return "L:B,P"
        # Assume some move is possible; fallback (though engine enforces legality)
        return "H:P,B" if len(moves) > 1 else "H:B,P"
    
    # Check if bearing off is possible (all checkers in home: points 0-5)
    bearing_off_possible = all(state['my_pts'][i] == 0 for i in range(6, 24))
    
    if len(moves) == 1:
        d = moves[0]
        if bearing_off_possible:
            for p in range(6):
                if state['my_pts'][p] > 0:
                    # Can bear off if die >= p and move legal
                    if self._is_move_legal(p, d, state):
                        return f"H:A{p},P"
        else:
            for p in range(23, -1, -1):
                if self._is_move_legal(p, d, state):
                    return f"H:A{p},P"
        return "H:P,P"
    
    # Two dice
    d1, d2 = sorted(moves)
    for order in ['L', 'H']:
        die1 = d1 if order == 'L' else d2
        die2 = d2 if order == 'L' else d1
        # Find first move
        p1 = self._find_greedy_from(die1, state, bearing_off_possible)
        if p1 is None:
            continue
        # Simulate board after first move (shallow copy for efficiency)
        temp_state = self._simulate_move(state, p1, die1)
        # Find second move after simulation
        p2 = self._find_greedy_from(die2, temp_state, self._can_bear_off(temp_state))
        if p2 is not None:
            return f"{order}:A{p1},A{p2}"
    # Fallback: try to play one move if possible
    p = self._find_greedy_from(d2, state, bearing_off_possible)
    if p is not None:
        return f"H:A{p},P"
    p = self._find_greedy_from(d1, state, bearing_off_possible)
    if p is not None:
        return f"L:A{p},B"  # Some arbitrary but legal format for one move
    return "H:P,P"

def _is_move_legal(from_p, d, state):
    if state['my_pts'][from_p] == 0:
        return False
    dest = from_p - d
    if dest >= 0:
        if state['opp_pts'][dest] >= 2:
            return False
    # Bearing off or on-board move is allowed
    return True

def _can_bear_off(state):
    return all(state['my_pts'][i] == 0 for i in range(6, 24)) and state['my_bar'] == 0

def _find_greedy_from(d, state, bearing_off):
    if bearing_off:
        for p in range(6):
            if self._is_move_legal(p, d, state):
                return p
    else:
        for p in range(23, -1, -1):
            if self._is_move_legal(p, d, state):
                return p
    return None

def _simulate_move(state, from_p, d):
    # Shallow copy dict
    temp = copy.copy(state)
    temp['my_pts'] = state['my_pts'][:]
    temp['my_pts'][from_p] -= 1
    dest = from_p - d
    if dest >= 0:
        temp['my_pts'][dest] += 1
    # Else, assume borne off, no change
    return temp
