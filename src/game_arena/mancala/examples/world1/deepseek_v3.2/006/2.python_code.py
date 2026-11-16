
import time
import sys

def apply_move(you, opponent, move):
    """
    Apply a move for the player whose state is given by `you`.
    Returns (new_you, new_opponent, extra_move) where extra_move is True if the player gets another turn.
    """
    you = list(you)
    opponent = list(opponent)
    seeds = you[move]
    you[move] = 0
    pos = move + 1
    side = 0  # 0 for your side, 1 for opponent side
    last_house = None
    last_value_before = None
    while seeds > 0:
        if side == 0:
            if pos <= 5:
                last_value_before = you[pos]
                you[pos] += 1
                seeds -= 1
                last_house = (0, pos)
                pos += 1
            elif pos == 6:
                last_value_before = you[6]
                you[6] += 1
                seeds -= 1
                last_house = (0, 6)
                pos = 0
                side = 1
            else:
                # wrap to opponent side
                pos = 0
                side = 1
        else:  # opponent side
            if pos <= 5:
                last_value_before = opponent[pos]
                opponent[pos] += 1
                seeds -= 1
                last_house = (1, pos)
                pos += 1
            elif pos == 6:
                # opponent's store, skip
                pos = 0
                side = 0
            else:
                # wrap to your side
                pos = 0
                side = 0
    # after sowing, handle special rules
    extra_move = False
    if last_house[0] == 0 and last_house[1] == 6:
        extra_move = True
    elif last_house[0] == 0 and last_house[1] <= 5:
        if last_value_before == 0:
            opposite = 5 - last_house[1]
            if opponent[opposite] > 0:
                # capture
                you[6] += you[last_house[1]] + opponent[opposite]
                you[last_house[1]] = 0
                opponent[opposite] = 0
    return you, opponent, extra_move

def is_terminal(you, opponent):
    return sum(you[0:6]) == 0 or sum(opponent[0:6]) == 0

def collect_remaining(you, opponent):
    """If game is over, collect all seeds to stores and return final state."""
    you_total = sum(you[0:6])
    opponent_total = sum(opponent[0:6])
    new_you = [0]*6 + [you[6] + you_total]
    new_opponent = [0]*6 + [opponent[6] + opponent_total]
    return new_you, new_opponent

def evaluate_state(you, opponent):
    """
    Heuristic evaluation from the perspective of the player whose store is you[6].
    """
    store_diff = you[6] - opponent[6]
    seeds_diff = sum(you[0:6]) - sum(opponent[0:6])
    return store_diff + 0.1 * seeds_diff

def alphabeta(state, depth, alpha, beta, maximizing):
    """
    state = (you, opponent) where `you` is the player to move.
    Returns the evaluated score for the player who is originally to move at the root.
    """
    you, opponent = state
    if depth == 0 or is_terminal(you, opponent):
        if is_terminal(you, opponent):
            you_f, opponent_f = collect_remaining(you, opponent)
            return evaluate_state(you_f, opponent_f)
        return evaluate_state(you, opponent)
    
    legal_moves = [i for i in range(6) if you[i] > 0]
    # move ordering: sort by number of seeds descending
    legal_moves.sort(key=lambda i: you[i], reverse=True)
    
    if maximizing:
        value = -float('inf')
        for move in legal_moves:
            new_you, new_opponent, extra = apply_move(you, opponent, move)
            if extra:
                new_state = (new_you, new_opponent)
                new_value = alphabeta(new_state, depth-1, alpha, beta, True)
            else:
                new_state = (new_opponent, new_you)
                new_value = alphabeta(new_state, depth-1, alpha, beta, False)
            if new_value > value:
                value = new_value
            alpha = max(alpha, value)
            if value >= beta:
                break
        return value
    else:
        value = float('inf')
        for move in legal_moves:
            new_you, new_opponent, extra = apply_move(you, opponent, move)
            if extra:
                new_state = (new_you, new_opponent)
                new_value = alphabeta(new_state, depth-1, alpha, beta, False)
            else:
                new_state = (new_opponent, new_you)
                new_value = alphabeta(new_state, depth-1, alpha, beta, True)
            if new_value < value:
                value = new_value
            beta = min(beta, value)
            if value <= alpha:
                break
        return value

def policy(you, opponent):
    start_time = time.perf_counter()
    legal_moves = [i for i in range(6) if you[i] > 0]
    if not legal_moves:
        # According to the problem, this should never happen.
        return 0
    
    # Initial ordering: more seeds first
    legal_moves.sort(key=lambda i: you[i], reverse=True)
    best_move = legal_moves[0]
    
    time_limit = 0.95  # seconds, leave a small margin
    depth = 1
    while time.perf_counter() - start_time < time_limit:
        best_value = -float('inf')
        current_best = best_move
        alpha = -float('inf')
        beta = float('inf')
        for move in legal_moves:
            # Check time before evaluating each move
            if time.perf_counter() - start_time >= time_limit:
                break
            new_you, new_opponent, extra = apply_move(you, opponent, move)
            if extra:
                value = alphabeta((new_you, new_opponent), depth-1, alpha, beta, True)
            else:
                value = alphabeta((new_opponent, new_you), depth-1, alpha, beta, False)
            if value > best_value:
                best_value = value
                current_best = move
                alpha = max(alpha, best_value)
        # Only update best_move if we completed the depth without time out
        if time.perf_counter() - start_time < time_limit:
            best_move = current_best
        depth += 1
    return best_move

# Example usage (for testing only):
if __name__ == "__main__":
    # Initial board: each house has 4 seeds, stores empty
    you = [4,4,4,4,4,4,0]
    opponent = [4,4,4,4,4,4,0]
    move = policy(you, opponent)
    print(f"Selected move: {move}")
