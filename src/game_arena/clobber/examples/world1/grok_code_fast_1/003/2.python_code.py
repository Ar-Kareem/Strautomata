
import numpy as np

def get_moves(player_board, opponent_board):
    moves = []
    for r in range(5):
        for c in range(6):
            if player_board[r][c] == 1:
                for dr, dc, dir_char in [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 5 and 0 <= nc < 6 and opponent_board[nr][nc] == 1:
                        moves.append(f"{r},{c},{dir_char}")
    return moves

def apply_move(player_board, opponent_board, move_str):
    r, c, dir_char = move_str.split(',')
    r, c = int(r), int(c)
    if dir_char == 'U':
        dr, dc = -1, 0
    elif dir_char == 'R':
        dr, dc = 0, 1
    elif dir_char == 'D':
        dr, dc = 1, 0
    elif dir_char == 'L':
        dr, dc = 0, -1
    nr, nc = r + dr, c + dc
    # Create new boards
    new_player = [row[:] for row in player_board]
    new_opponent = [row[:] for row in opponent_board]
    new_player[r][c] = 0
    new_player[nr][nc] = 1
    new_opponent[nr][nc] = 0
    return new_player, new_opponent

def heuristic(my_board, opp_board):
    my_moves = len(get_moves(my_board, opp_board))
    opp_moves = len(get_moves(opp_board, my_board))
    return my_moves - opp_moves

def minimax(current_me, current_opp, depth, is_max, alpha=-float('inf'), beta=float('inf')):
    if depth == 0:
        return heuristic(current_me, current_opp) if is_max else -heuristic(current_me, current_opp)
    moves = get_moves(current_me, current_opp) if is_max else get_moves(current_opp, current_me)
    if not moves:
        return -1000 if is_max else 1000
    if is_max:
        val = -float('inf')
        for move in moves:
            nme, nopp = apply_move(current_me, current_opp, move)
            val = max(val, minimax(nme, nopp, depth-1, False, alpha, beta))
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return val
    else:
        val = float('inf')
        for move in moves:
            nopp, nme = apply_move(current_opp, current_me, move)
            val = min(val, minimax(nme, nopp, depth-1, True, alpha, beta))
            beta = min(beta, val)
            if beta <= alpha:
                break
        return val

def policy(you, opponent):
    moves = get_moves(you, opponent)
    best_move = moves[0] if moves else None
    best_score = -float('inf')
    for move in moves:
        nyou, nopp = apply_move(you, opponent, move)
        score = minimax(nyou, nopp, depth=3, is_max=False)
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
