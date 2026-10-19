
import copy

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Kalah move-selection policy using Minimax with Alpha-Beta pruning.
    """

    def get_legal_moves(state_you):
        return [i for i in range(6) if state_you[i] > 0]

    def simulate_move(state_you, state_opp, move_idx):
        new_you = list(state_you)
        new_opp = list(state_opp)
        
        seeds = new_you[move_idx]
        new_you[move_idx] = 0
        
        curr_side = 'you'
        curr_idx = move_idx + 1
        
        extra_move = False
        
        while seeds > 0:
            if curr_side == 'you':
                if curr_idx < 7:
                    new_you[curr_idx] += 1
                    seeds -= 1
                    if seeds == 0:
                        if curr_idx == 6:
                            extra_move = True
                        elif new_you[curr_idx] == 1 and new_opp[5 - curr_idx] > 0:
                            # Capture rule
                            new_you[6] += new_you[curr_idx] + new_opp[5 - curr_idx]
                            new_you[curr_idx] = 0
                            new_opp[5 - curr_idx] = 0
                    curr_idx += 1
                else:
                    curr_side = 'opp'
                    curr_idx = 0
            else: # opponent side
                if curr_idx < 6:
                    new_opp[curr_idx] += 1
                    seeds -= 1
                    curr_idx += 1
                else:
                    curr_side = 'you'
                    curr_idx = 0
        
        # Check game end
        if sum(new_you[:6]) == 0 or sum(new_opp[:6]) == 0:
            new_you[6] += sum(new_you[:6])
            new_opp[6] += sum(new_opp[:6])
            for i in range(6):
                new_you[i] = 0
                new_opp[i] = 0
            return new_you, new_opp, False # End of game, no extra move
            
        return new_you, new_opp, extra_move

    def evaluate(state_you, state_opp):
        return state_you[6] - state_opp[6]

    def minimax(state_you, state_opp, depth, alpha, beta, maximizing_player):
        legal_moves = get_legal_moves(state_you if maximizing_player else state_opp)
        
        if depth == 0 or not legal_moves:
            return evaluate(state_you, state_opp)
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in legal_moves:
                next_you, next_opp, extra = simulate_move(state_you, state_opp, move)
                if extra:
                    eval = minimax(next_you, next_opp, depth - 1, alpha, beta, True)
                else:
                    eval = minimax(next_opp, next_you, depth - 1, -beta, -alpha, False)
                    eval = -eval # Switch perspective
                
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            # This part is handled by the recursive call with inverted perspective
            return 0

    # Entry point for the policy decision
    best_move = -1
    best_val = float('-inf')
    
    # Check for immediate extra move opportunities first
    moves = get_legal_moves(you)
    if len(moves) == 1:
        return moves[0]

    # Search depth. 6 is generally safe for time limits in Python.
    for move in moves:
        next_you, next_opp, extra = simulate_move(you, opponent, move)
        if extra:
            # Depth + 1 because we get to go again
            val = minimax(next_you, next_opp, 5, float('-inf'), float('inf'), True)
        else:
            val = -minimax(next_opp, next_you, 5, float('-inf'), float('inf'), True)
        
        if val > best_val:
            best_val = val
            best_move = move
            
    return best_move if best_move != -1 else moves[0]
