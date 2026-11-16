
import copy

def policy(you, opponent):
    """
    Choose the best move for the current Kalah state.
    Returns an integer 0-5 representing the house to sow from.
    """
    # Convert to internal representation: two lists of length 7
    state = (list(you), list(opponent))
    best_move = None
    best_value = -float('inf')
    
    # For each legal move
    for i in range(6):
        if you[i] == 0:
            continue
        
        # Evaluate move using minimax with alpha-beta pruning
        new_state, extra_turn = simulate_move(state, i, player=0)
        
        # If game ended after this move, evaluate terminal state
        if is_terminal(new_state):
            value = evaluate_terminal(new_state)
        else:
            # If extra turn, we get to move again, so we can think of it as same player's turn
            if extra_turn:
                value = alphabeta(new_state, depth=7, alpha=-float('inf'), beta=float('inf'), maximizing=True)
            else:
                value = alphabeta(new_state, depth=7, alpha=-float('inf'), beta=float('inf'), maximizing=False)
        
        if value > best_value:
            best_value = value
            best_move = i
    
    # In case no move selected (should not happen), fallback to first legal move
    if best_move is None:
        for i in range(6):
            if you[i] > 0:
                best_move = i
                break
    
    return best_move

def alphabeta(state, depth, alpha, beta, maximizing):
    """
    Minimax with alpha-beta pruning.
    state: tuple (our_houses, opponent_houses) where each is list of 7 ints.
    maximizing: True if it's our turn (the player who called policy), False for opponent.
    """
    if depth == 0 or is_terminal(state):
        return evaluate(state)
    
    our_houses, opp_houses = state
    if maximizing:
        max_eval = -float('inf')
        legal_moves = [i for i in range(6) if our_houses[i] > 0]
        for move in legal_moves:
            new_state, extra_turn = simulate_move(state, move, player=0)
            if extra_turn:
                eval_child = alphabeta(new_state, depth-1, alpha, beta, True)
            else:
                eval_child = alphabeta(new_state, depth-1, alpha, beta, False)
            max_eval = max(max_eval, eval_child)
            alpha = max(alpha, eval_child)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        legal_moves = [i for i in range(6) if opp_houses[i] > 0]
        for move in legal_moves:
            new_state, extra_turn = simulate_move(state, move, player=1)
            if extra_turn:
                eval_child = alphabeta(new_state, depth-1, alpha, beta, False)
            else:
                eval_child = alphabeta(new_state, depth-1, alpha, beta, True)
            min_eval = min(min_eval, eval_child)
            beta = min(beta, eval_child)
            if beta <= alpha:
                break
        return min_eval

def simulate_move(state, move, player):
    """
    Simulate sowing from house `move` for player `player` (0 for us, 1 for opponent).
    Returns (new_state, extra_turn) where new_state is tuple (our_houses, opp_houses),
    extra_turn is True if the same player gets another move.
    """
    our_houses, opp_houses = copy.deepcopy(state)
    if player == 0:
        current_side = our_houses
        other_side = opp_houses
    else:
        current_side = opp_houses
        other_side = our_houses
    
    seeds = current_side[move]
    if seeds == 0:
        raise ValueError("Illegal move: empty house")
    
    # Pick seeds
    current_side[move] = 0
    current_index = move + 1
    
    # Track last seed placement
    last_side = current_side  # side where last seed placed
    last_index = None
    
    # Sow seeds
    while seeds > 0:
        # If we are on current side (the player who moved)
        side = current_side
        other = other_side
        is_current_player_side = True
        # Determine if we are on the moving player's side
        # Actually current_side is always the moving player's side at start, but after crossing to opponent, we switch
        # We'll handle with a flag.
        # Better: we have two sides: current_side and other_side. We'll keep track of which side we are sowing on.
        # We'll use a variable sowing_side = current_side initially.
        # Actually we can think of the board as a circular list of 14 positions, skipping opponent's store.
        # Let's implement the sowing logic as described in rules.
        # We'll simulate step by step.
        # I'll rewrite this part more clearly.
        pass  # This is getting long; let me think of a simpler implementation.
    
    # Instead of complex logic, I'll implement a direct simulation using the rule description.
    # Let's restart this function.

def simulate_move(state, move, player):
    our, opp = copy.deepcopy(state)
    if player == 0:
        board = our + opp  # length 14, indices: 0-6 our houses+store, 7-13 opponent houses+store
        # but opponent store is at index 13? Actually opponent store is opp[6], which is board[13].
        # However the sowing order: our houses 0-5, our store 6, opponent houses 7-12, skip opponent store 13, then back to our houses.
        # So we need to handle skipping opponent store.
    else:
        # opponent's turn: from opponent's perspective, their houses are 0-5, store 6.
        # We'll represent board as opp + our? Actually easier to swap perspectives.
        # Let's always represent from perspective of player to move.
        # So if player == 1, swap.
        our, opp = opp, our
        board = our + opp
        move = move  # move is relative to opponent's houses (0-5), which are now our in swapped view.
    
    # Now board: indices 0-5: current player houses, 6: current player store, 7-12: opponent houses, 13: opponent store.
    seeds = board[move]
    board[move] = 0
    pos = move + 1
    while seeds > 0:
        if pos == 13:  # opponent store, skip
            pos = 0
            continue
        board[pos] += 1
        seeds -= 1
        last_pos = pos
        pos += 1
        if pos == 14:
            pos = 0
    
    # Check for extra turn
    extra_turn = False
    if last_pos == 6:  # landed in current player's store
        extra_turn = True
    
    # Check for capture
    if not extra_turn and 0 <= last_pos <= 5 and board[last_pos] == 1:
        # last seed landed in current player's empty house (now has 1)
        # Check opposite house
        opp_index = 12 - last_pos  # because opposite house of index i is 12-i (since opponent houses are 7-12)
        if board[opp_index] > 0:
            # capture
            board[6] += board[last_pos] + board[opp_index]
            board[last_pos] = 0
            board[opp_index] = 0
    
    # Convert back to our/opp representation
    if player == 0:
        our_new = board[0:7]
        opp_new = board[7:14]
    else:
        # we swapped earlier, so swap back
        opp_new = board[0:7]
        our_new = board[7:14]
    
    # Check if game ended
    # (We'll handle terminal elsewhere)
    return ((our_new, opp_new), extra_turn)

def is_terminal(state):
    our, opp = state
    # If either side has all houses empty
    if all(our[i] == 0 for i in range(6)) or all(opp[i] == 0 for i in range(6)):
        return True
    return False

def evaluate_terminal(state):
    our, opp = state
    # Collect remaining seeds
    our_seeds = sum(our[:6])
    opp_seeds = sum(opp[:6])
    our_store = our[6] + our_seeds
    opp_store = opp[6] + opp_seeds
    return our_store - opp_store

def evaluate(state):
    """
    Heuristic evaluation of non-terminal state.
    """
    our, opp = state
    our_store = our[6]
    opp_store = opp[6]
    store_diff = our_store - opp_store
    
    our_seeds = sum(our[:6])
    opp_seeds = sum(opp[:6])
    seed_diff = our_seeds - opp_seeds
    
    # Vulnerability: count our empty houses where opponent opposite has seeds
    vulnerability = 0
    for i in range(6):
        if our[i] == 0:
            if opp[5 - i] > 0:
                vulnerability += 1
    
    # Extra move potential: for each house that if sown would land in store, add small bonus
    # Actually computing this requires knowing seeds count, but we can approximate:
    # A house i with seeds s such that (s + i) % 13 == 6 would land in store.
    # But we don't know if opponent store is skipped? Actually the skipping makes it non-linear.
    # Let's skip this for now.
    
    # Heuristic weights (tuned roughly)
    value = store_diff * 100 + seed_diff * 10 - vulnerability * 5
    return value
