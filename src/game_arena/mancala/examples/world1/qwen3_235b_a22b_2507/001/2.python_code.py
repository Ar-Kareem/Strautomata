
import numpy as np

def simulate_move(you, opponent, move):
    # Copy to avoid mutation
    my_board = you[:]
    opp_board = opponent[:]
    seeds = my_board[move]
    my_board[move] = 0
    pos = move
    is_my_side = True
    # Sow the seeds
    while seeds > 0:
        if is_my_side:
            pos += 1
            if pos == 6:  # landing in store
                my_board[6] += 1
                seeds -= 1
                if seeds == 0:  # last seed in store → extra turn
                    return my_board, opp_board, True, False, None
                # continue to opponent's side
                is_my_side = False
                pos = -1  # will become 0 on next increment
            else:
                my_board[pos] += 1
                seeds -= 1
                if seeds == 0:
                    # Check capture
                    if pos < 6 and my_board[pos] == 1:  # landed in empty house
                        opp_pos = 5 - pos
                        if opp_board[opp_pos] > 0:
                            capture = 1 + opp_board[opp_pos]
                            my_board[6] += capture
                            my_board[pos] = 0
                            opp_board[opp_pos] = 0
                            return my_board, opp_board, False, True, capture
                    return my_board, opp_board, False, False, 0
        else:
            pos += 1
            if pos == 6:
                # Skip opponent's store, go back to my side
                is_my_side = True
                pos = -1
            else:
                opp_board[pos] += 1
                seeds -= 1
                if seeds == 0:
                    # Last seed in opponent's house → no special
                    return my_board, opp_board, False, False, 0
    return my_board, opp_board, False, False, 0

def policy(you: list[int], opponent: list[int]) -> int:
    legal_moves = [i for i in range(6) if you[i] > 0]
    best_move = legal_moves[0]
    best_score = -1
    
    for move in legal_moves:
        _, _, extra_move, is_capture, capture_amount = simulate_move(you, opponent, move)
        score = 0
        if extra_move:
            score += 1000
        if is_capture:
            score += 10 * capture_amount
        # Prefer extra move captures highly
        if extra_move and is_capture:
            score += 50
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
