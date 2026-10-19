
import time
import sys

# Increase recursion limit for deep searches
sys.setrecursionlimit(10000)

WIN_SCORE = 10000
TIME_LIMIT = 0.95

def simulate(you, opp, move):
    """Simulate a move and return (new_you, new_opp, extra_turn)."""
    y = you[:]
    o = opp[:]
    seeds = y[move]
    y[move] = 0
    pos = move
    # Sow seeds: 0-5 (you), 6 (your store), 7-12 (opp houses)
    while seeds > 0:
        pos = (pos + 1) % 13
        if pos < 6:
            y[pos] += 1
        elif pos == 6:
            y[6] += 1
        else:  # 7-12 map to opp[0-5]
            o[pos - 7] += 1
        seeds -= 1
    
    # Extra turn if last seed lands in your store (position 6)
    if pos == 6:
        return y, o, True
    
    # Capture rule: last seed lands in empty house on your side (0-5)
    if 0 <= pos <= 5:
        if y[pos] == 1:  # was empty before this drop
            opp_idx = 5 - pos
            if o[opp_idx] > 0:
                y[6] += y[pos] + o[opp_idx]
                y[pos] = 0
                o[opp_idx] = 0
    return y, o, False

def is_terminal(you, opp):
    """Check if game is over (one side has no seeds in houses)."""
    return all(x == 0 for x in you[:6]) or all(x == 0 for x in opp[:6])

def eval_terminal(you, opp):
    """Evaluate terminal state. Large positive for win, negative for loss."""
    you_final = you[6] + sum(you[:6])
    opp_final = opp[6] + sum(opp[:6])
    if you_final > opp_final:
        return WIN_SCORE
    elif you_final < opp_final:
        return -WIN_SCORE
    return 0

def heuristic(you, opp):
    """Heuristic for non-terminal states: store diff + potential seeds."""
    store_diff = you[6] - opp[6]
    pot_diff = sum(you[:6]) - sum(opp[:6])
    return store_diff + 0.5 * pot_diff

def move_priority(you, opp, m):
    """Return priority for move ordering: 2=extra turn, 1=capture, 0=other."""
    seeds = you[m]
    pos = (m + seeds) % 13
    if pos == 6:
        return 2
    # Capture possible only if seeds < 13 (no full wrap) and lands on empty house
    if seeds < 13 and 0 <= pos <= 5 and you[pos] == 0 and opp[5 - pos] > 0:
        return 1
    return 0

def negamax(you, opp, depth, alpha, beta, start_time):
    """Negamax search with alpha-beta pruning."""
    if time.time() - start_time > TIME_LIMIT:
        raise TimeoutError()
    
    if is_terminal(you, opp):
        return eval_terminal(you, opp)
    if depth == 0:
        return heuristic(you, opp)
    
    moves = [i for i in range(6) if you[i] > 0]
    # Order moves for better pruning
    moves.sort(key=lambda m: move_priority(you, opp, m), reverse=True)
    
    max_eval = -float('inf')
    for m in moves:
        new_you, new_opp, extra = simulate(you, opp, m)
        if extra:
            val = negamax(new_you, new_opp, depth - 1, alpha, beta, start_time)
        else:
            val = -negamax(new_opp, new_you, depth - 1, -beta, -alpha, start_time)
        
        if val > max_eval:
            max_eval = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
    return max_eval

def search_root(you, opp, depth, start_time):
    """Find best move at given depth."""
    moves = [i for i in range(6) if you[i] > 0]
    if not moves:
        return 0, 0  # Should not happen
    
    moves.sort(key=lambda m: move_priority(you, opp, m), reverse=True)
    
    best_move = moves[0]
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    for m in moves:
        new_you, new_opp, extra = simulate(you, opp, m)
        if extra:
            score = negamax(new_you, new_opp, depth - 1, alpha, beta, start_time)
        else:
            score = -negamax(new_opp, new_you, depth - 1, -beta, -alpha, start_time)
        
        if score > best_score:
            best_score = score
            best_move = m
        if score > alpha:
            alpha = score
    return best_move, best_score

def policy(you, opponent):
    """
    Select the best move using iterative deepening alpha-beta search.
    Always returns a legal move.
    """
    start_time = time.time()
    
    # Find a fallback legal move
    fallback = 0
    for i in range(6):
        if you[i] > 0:
            fallback = i
            break
    
    best_move = fallback
    
    try:
        # Iterative deepening until time runs out
        for depth in range(1, 20):
            if time.time() - start_time > TIME_LIMIT:
                break
            move, _ = search_root(you, opponent, depth, start_time)
            best_move = move
    except TimeoutError:
        pass
    
    return best_move
