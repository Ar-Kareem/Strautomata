
import copy

def policy(you: list[int], opponent: list[int]) -> int:
    def get_moves(state_you):
        return [i for i in range(6) if state_you[i] > 0]

    def simulate(state_you, state_opp, move):
        y = list(state_you)
        o = list(state_opp)
        seeds = y[move]
        y[move] = 0
        
        curr_side = 'y'
        curr_idx = move + 1
        repeat_turn = False
        
        while seeds > 0:
            if curr_side == 'y':
                if curr_idx < 7:
                    y[curr_idx] += 1
                    seeds -= 1
                    if seeds == 0:
                        if curr_idx == 6:
                            repeat_turn = True
                        elif y[curr_idx] == 1 and o[5 - curr_idx] > 0:
                            y[6] += y[curr_idx] + o[5 - curr_idx]
                            y[curr_idx] = 0
                            o[5 - curr_idx] = 0
                    curr_idx += 1
                else:
                    curr_side = 'o'
                    curr_idx = 0
            else:
                if curr_idx < 6:
                    o[curr_idx] += 1
                    seeds -= 1
                    curr_idx += 1
                else:
                    curr_side = 'y'
                    curr_idx = 0
        
        # Check game end
        if sum(y[:6]) == 0 or sum(o[:6]) == 0:
            y[6] += sum(y[:6])
            o[6] += sum(o[:6])
            for i in range(6):
                y[i] = 0
                o[i] = 0
            return y, o, False
            
        return y, o, repeat_turn

    def evaluate(y, o):
        return y[6] - o[6]

    def minimax(y, o, depth, alpha, beta, maximizing):
        if depth == 0 or sum(y[:6]) == 0 or sum(o[:6]) == 0:
            # Final scoring if game over
            y_final = y[6] + sum(y[:6])
            o_final = o[6] + sum(o[:6])
            return y_final - o_final

        moves = get_moves(y if maximizing else o)
        if maximizing:
            max_eval = -float('inf')
            for m in moves:
                ny, no, repeat = simulate(y, o, m)
                if repeat:
                    eval = minimax(ny, no, depth - 1, alpha, beta, True)
                else:
                    eval = minimax(no, ny, depth - 1, -beta, -alpha, False)
                    eval = -eval
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            # This branch is technically handled by the recursion flip above
            min_eval = float('inf')
            for m in moves:
                no, ny, repeat = simulate(o, y, m)
                if repeat:
                    eval = minimax(ny, no, depth - 1, alpha, beta, False)
                else:
                    eval = minimax(no, ny, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    best_move = -1
    best_val = -float('inf')
    
    # Priority move: Get extra turn if possible
    possible_moves = get_moves(you)
    
    # Simple depth-limited search
    depth_limit = 10 
    
    for m in possible_moves:
        ny, no, repeat = simulate(you, opponent, m)
        if repeat:
            val = minimax(ny, no, depth_limit, -float('inf'), float('inf'), True)
        else:
            val = -minimax(no, ny, depth_limit, -float('inf'), float('inf'), False)
            
        if val > best_val:
            best_val = val
            best_move = m
            
    return best_move if best_move != -1 else possible_moves[0]
