
import copy

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Kalah move selection policy using Minimax with Alpha-Beta pruning.
    """

    def get_legal_moves(state_you):
        return [i for i in range(6) if state_you[i] > 0]

    def simulate_move(state_you, state_opp, move_idx):
        # Create copies to avoid mutating original lists
        new_you = list(state_you)
        new_opp = list(state_opp)
        
        seeds = new_you[move_idx]
        new_you[move_idx] = 0
        
        curr_side = 0 # 0 for 'you', 1 for 'opp'
        curr_pos = move_idx + 1
        
        another_turn = False
        
        while seeds > 0:
            if curr_side == 0:
                if curr_pos <= 6:
                    new_you[curr_pos] += 1
                    seeds -= 1
                    if seeds == 0:
                        if curr_pos == 6:
                            another_turn = True
                        elif new_you[curr_pos] == 1 and new_opp[5 - curr_pos] > 0:
                            # Capture logic
                            new_you[6] += new_you[curr_pos] + new_opp[5 - curr_pos]
                            new_you[curr_pos] = 0
                            new_opp[5 - curr_pos] = 0
                    curr_pos += 1
                else:
                    curr_side = 1
                    curr_pos = 0
            else:
                if curr_pos <= 5:
                    new_opp[curr_pos] += 1
                    seeds -= 1
                    curr_pos += 1
                else:
                    curr_side = 0
                    curr_pos = 0
        
        # Check game end
        if sum(new_you[:6]) == 0 or sum(new_opp[:6]) == 0:
            new_you[6] += sum(new_you[:6])
            new_opp[6] += sum(new_opp[:6])
            for i in range(6):
                new_you[i] = 0
                new_opp[i] = 0
            return new_you, new_opp, False # End of game, no extra turn
            
        return new_you, new_opp, another_turn

    def evaluate(state_you, state_opp):
        # Primary goal: difference in stores
        score = state_you[6] - state_opp[6]
        # Secondary goal: seeds in houses (potential)
        score += 0.5 * (sum(state_you[:6]) - sum(state_opp[:6]))
        return score

    def minimax(state_you, state_opp, depth, alpha, beta, maximizing_player):
        moves = get_legal_moves(state_you if maximizing_player else state_opp)
        
        if depth == 0 or not moves:
            return evaluate(state_you, state_opp)

        if maximizing_player:
            max_eval = float('-inf')
            for m in moves:
                ny, no, extra = simulate_move(state_you, state_opp, m)
                if extra:
                    eval = minimax(ny, no, depth - 1, alpha, beta, True)
                else:
                    eval = minimax(ny, no, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            # Opponent is 'you' from their perspective
            for m in moves:
                no, ny, extra = simulate_move(state_opp, state_you, m)
                if extra:
                    eval = minimax(ny, no, depth - 1, alpha, beta, False)
                else:
                    eval = minimax(ny, no, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    # Search Logic
    best_move = -1
    best_val = float('-inf')
    legal_moves = get_legal_moves(you)
    
    # Heuristic: Prefer moves that give extra turns first
    legal_moves.sort(key=lambda m: (you[m] % 13 == (6 - m)), reverse=True)

    for move in legal_moves:
        ny, no, extra = simulate_move(you, opponent, move)
        if extra:
            val = minimax(ny, no, 10, float('-inf'), float('inf'), True)
        else:
            val = minimax(ny, no, 10, float('-inf'), float('inf'), False)
        
        if val > best_val:
            best_val = val
            best_move = move
            
    return best_move

