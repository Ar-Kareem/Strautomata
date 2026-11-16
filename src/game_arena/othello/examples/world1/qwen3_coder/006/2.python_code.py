
import numpy as np

# Precomputed position weights for evaluation
POSITION_WEIGHTS = np.array([
    [ 30, -12,  1,  1,  1,  1, -12,  30],
    [-12, -15, -1, -1, -1, -1, -15, -12],
    [  1,  -1,  0,  0,  0,  0,  -1,   1],
    [  1,  -1,  0,  0,  0,  0,  -1,   1],
    [  1,  -1,  0,  0,  0,  0,  -1,   1],
    [  1,  -1,  0,  0,  0,  0,  -1,   1],
    [-12, -15, -1, -1, -1, -1, -15, -12],
    [ 30, -12,  1,  1,  1,  1, -12,  30]
])

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    board_size = 8
    empty = (you == 0) & (opponent == 0)
    
    def get_legal_moves(player, opp):
        moves = []
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        for r in range(board_size):
            for c in range(board_size):
                if player[r][c] == 1 or opp[r][c] == 1:
                    continue
                is_legal = False
                for dr, dc in directions:
                    r_curr, c_curr = r + dr, c + dc
                    found_opponent = False
                    while 0 <= r_curr < board_size and 0 <= c_curr < board_size:
                        if opp[r_curr][c_curr] == 1:
                            found_opponent = True
                        elif player[r_curr][c_curr] == 1 and found_opponent:
                            is_legal = True
                            break
                        else:
                            break
                        r_curr += dr
                        c_curr += dc
                    if is_legal:
                        break
                if is_legal:
                    moves.append((r, c))
        return moves
    
    def make_move(player, opp, r, c):
        new_player = player.copy()
        new_opp = opp.copy()
        new_player[r][c] = 1
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        for dr, dc in directions:
            r_curr, c_curr = r + dr, c + dc
            flip_list = []
            while 0 <= r_curr < board_size and 0 <= c_curr < board_size:
                if opp[r_curr][c_curr] == 1:
                    flip_list.append((r_curr, c_curr))
                elif player[r_curr][c_curr] == 1:
                    for fr, fc in flip_list:
                        new_player[fr][fc] = 1
                        new_opp[fr][fc] = 0
                    break
                else:
                    break
                r_curr += dr
                c_curr += dc
        return new_player, new_opp

    def evaluate(player, opp):
        score = 0
        # Piece difference
        player_count = np.sum(player)
        opp_count = np.sum(opp)
        score += (player_count - opp_count) * 10
        
        # Positional weights
        score += np.sum(POSITION_WEIGHTS * player) * 1
        score -= np.sum(POSITION_WEIGHTS * opp) * 1
        
        # Mobility
        player_moves = len(get_legal_moves(player, opp))
        opp_moves = len(get_legal_moves(opp, player))
        score += (player_moves - opp_moves) * 50
        
        return score

    def minimax(player, opp, depth, alpha, beta, maximizing):
        player_moves = get_legal_moves(player, opp)
        opp_moves = get_legal_moves(opp, player)
        
        if depth == 0 or (len(player_moves) == 0 and len(opp_moves) == 0):
            return evaluate(player, opp)
        
        if maximizing:
            max_eval = -np.inf
            for r, c in player_moves:
                new_player, new_opp = make_move(player, opp, r, c)
                eval_score = minimax(new_opp, new_player, depth-1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval if max_eval != -np.inf else evaluate(player, opp)
        else:
            min_eval = np.inf
            for r, c in opp_moves:
                new_opp, new_player = make_move(opp, player, r, c)
                eval_score = minimax(new_player, new_opp, depth-1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval if min_eval != np.inf else evaluate(player, opp)

    # Determine search depth based on number of empty squares
    empty_count = np.sum(empty)
    if empty_count > 50:
        depth = 4
    elif empty_count > 20:
        depth = 5
    elif empty_count > 10:
        depth = 6
    else:
        depth = 8

    legal_moves = get_legal_moves(you, opponent)
    if not legal_moves:
        return "pass"
    
    best_move = None
    best_value = -np.inf
    
    for r, c in legal_moves:
        new_you, new_opponent = make_move(you, opponent, r, c)
        move_value = minimax(new_opponent, new_you, depth-1, -np.inf, np.inf, False)
        if move_value > best_value:
            best_value = move_value
            best_move = (r, c)
            
    if best_move is None:
        return "pass"
        
    r, c = best_move
    col_letter = chr(ord('a') + c)
    row_number = str(r + 1)
    return col_letter + row_number
