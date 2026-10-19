
def policy(you: list[int], opponent: list[int]) -> int:
    """Kalah AI using minimax with alpha-beta pruning."""
    legal_moves = [i for i in range(6) if you[i] > 0]
    if not legal_moves:
        return 0
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        new_you, new_opp, extra = make_move(you, opponent, move, True)
        if extra:
            score = minimax(new_you, new_opp, 8, float('-inf'), float('inf'), True)
        else:
            score = minimax(new_you, new_opp, 8, float('-inf'), float('inf'), False)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move


def make_move(you, opponent, move, is_you_turn):
    """Execute a move and return (new_you, new_opp, extra_turn)."""
    if is_you_turn:
        my, their = list(you), list(opponent)
    else:
        my, their = list(opponent), list(you)
    
    seeds = my[move]
    my[move] = 0
    
    start_pos = move + 1
    for i in range(seeds):
        pos = (start_pos + i) % 13
        if pos < 6:
            my[pos] += 1
        elif pos == 6:
            my[6] += 1
        else:
            their[pos - 7] += 1
    
    last_pos = (start_pos + seeds - 1) % 13
    extra_turn = (last_pos == 6)
    
    if last_pos < 6 and my[last_pos] == 1 and their[5 - last_pos] > 0:
        captured = their[5 - last_pos] + 1
        my[6] += captured
        my[last_pos] = 0
        their[5 - last_pos] = 0
    
    if is_you_turn:
        return my, their, extra_turn
    else:
        return their, my, extra_turn


def is_game_over(you, opponent):
    return all(you[i] == 0 for i in range(6)) or all(opponent[i] == 0 for i in range(6))


def get_final_score(you, opponent):
    return you[6] + sum(you[:6]) - opponent[6] - sum(opponent[:6])


def minimax(you, opponent, depth, alpha, beta, is_maximizing):
    if is_game_over(you, opponent):
        return get_final_score(you, opponent) * 100
    
    if depth == 0:
        return evaluate(you, opponent)
    
    if is_maximizing:
        legal_moves = [i for i in range(6) if you[i] > 0]
        if not legal_moves:
            return get_final_score(you, opponent) * 100
        
        legal_moves.sort(key=lambda m: 0 if (m + you[m]) % 13 == 6 else 1)
        
        max_eval = float('-inf')
        for move in legal_moves:
            new_you, new_opp, extra = make_move(you, opponent, move, True)
            if extra:
                score = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
            else:
                score = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return max_eval
    else:
        legal_moves = [i for i in range(6) if opponent[i] > 0]
        if not legal_moves:
            return get_final_score(you, opponent) * 100
        
        legal_moves.sort(key=lambda m: 0 if (m + opponent[m]) % 13 == 6 else 1)
        
        min_eval = float('inf')
        for move in legal_moves:
            new_opp, new_you, extra = make_move(opponent, you, move, False)
            if extra:
                score = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
            else:
                score = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return min_eval


def evaluate(you, opponent):
    score = (you[6] - opponent[6]) * 10
    score += (sum(you[:6]) - sum(opponent[:6])) * 0.5
    
    for i in range(6):
        if you[i] > 0:
            last_pos = (i + you[i]) % 13
            if last_pos == 6:
                score += 2
            elif last_pos < 6 and you[last_pos] == 0 and opponent[5 - last_pos] > 0:
                score += 1
        
        if opponent[i] > 0:
            last_pos = (i + opponent[i]) % 13
            if last_pos == 6:
                score -= 2
            elif last_pos < 6 and opponent[last_pos] == 0 and you[5 - last_pos] > 0:
                score -= 1
    
    return score
