import copy

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Kalah AI using Minimax with Alpha-Beta pruning and move ordering.
    """

    def get_legal_moves(state_you):
        return [i for i in range(6) if state_you[i] > 0]

    def simulate_move(state_you, state_opp, move_idx):
        y = list(state_you)
        o = list(state_opp)
        
        seeds = y[move_idx]
        y[move_idx] = 0
        
        curr_pos = move_idx + 1
        is_you_side = True
        extra_move = False
        
        while seeds > 0:
            if is_you_side:
                if curr_pos <= 6:
                    y[curr_pos] += 1
                    seeds -= 1
                    if seeds == 0:
                        if curr_pos == 6:
                            extra_move = True
                        elif y[curr_pos] == 1 and o[5 - curr_pos] > 0:
                            # Capture
                            y[6] += y[curr_pos] + o[5 - curr_pos]
                            y[curr_pos] = 0
                            o[5 - curr_pos] = 0
                    curr_pos += 1
                else:
                    is_you_side = False
                    curr_pos = 0
            else:
                if curr_pos <= 5:
                    o[curr_pos] += 1
                    seeds -= 1
                    curr_pos += 1
                else:
                    is_you_side = True
                    curr_pos = 0
        
        # Check game end
        if sum(y[:6]) == 0:
            y[6] += sum(o[:6])
            for i in range(6): o[i] = 0
        elif sum(o[:6]) == 0:
            o[6] += sum(y[:6])
            for i in range(6): y[i] = 0
            
        return y, o, extra_move

    def evaluate(y, o):
        # Basic heuristic: difference in stores
        # Plus seeds remaining in houses (weighted slightly lower)
        return (y[6] - o[6]) * 10 + (sum(y[:6]) - sum(o[:6]))

    def minimax(y, o, depth, alpha, beta, maximizing):
        if depth == 0 or sum(y[:6]) == 0 or sum(o[:6]) == 0:
            return evaluate(y, o)

        if maximizing:
            max_eval = -float('inf')
            moves = get_legal_moves(y)
            # Simple Move Ordering: prioritize moves that give extra turns
            moves.sort(key=lambda m: (y[m] + m) % 13 == 6, reverse=True)
            
            for move in moves:
                ny, no, extra = simulate_move(y, o, move)
                if extra:
                    eval = minimax(ny, no, depth - 1, alpha, beta, True)
                else:
                    eval = minimax(no, ny, depth - 1, -beta, -alpha, False) # Swapped perspective
                    eval = -eval
                
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            # This branch is handled by the negation in the caller for symmetry
            return -minimax(o, y, depth, alpha, beta, True)

    best_move = -1
    best_value = -float('inf')
    
    # Use iterative deepening or fixed depth (7 is usually safe for 1s)
    legal_moves = get_legal_moves(you)
    if len(legal_moves) == 1:
        return legal_moves[0]

    # Prioritize moves that lead to extra turns for basic ordering
    legal_moves.sort(key=lambda m: (you[m] + m) % 13 == 6, reverse=True)

    for move in legal_moves:
        ny, no, extra = simulate_move(you, opponent, move)
        if extra:
            val = minimax(ny, no, 7, -float('inf'), float('inf'), True)
        else:
            # We pass depth-1 and flip the perspective
            val = -minimax(no, ny, 7, -float('inf'), float('inf'), True)
            
        if val > best_value:
            best_value = val
            best_move = move
            
    return best_move if best_move != -1 else legal_moves[0]
