
import numpy as np

def policy(board) -> str:
    all_moves = generate_legal_moves(board, 1)
    if not all_moves:
        return ""
    
    best_move = all_moves[0]
    min_opponent_moves = len(generate_legal_moves(apply_move(board, best_move), 2))
    
    for move in all_moves[1:]:
        new_board = apply_move(board, move)
        opponent_moves = generate_legal_moves(new_board, 2)
        num_opponent_moves = len(opponent_moves)
        if num_opponent_moves < min_opponent_moves:
            min_opponent_moves = num_opponent_moves
            best_move = move
    
    return best_move

def generate_legal_moves(board, player):
    directions = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    moves = []
    
    for r in range(6):
        for c in range(6):
            if board[r][c] == player:
                for dr, dc in directions:
                    step = 1
                    while True:
                        new_r = r + dr * step
                        new_c = c + dc * step
                        if not (0 <= new_r < 6 and 0 <= new_c < 6):
                            break
                        if board[new_r][new_c] != 0:
                            break
                        # Now process arrow positions for the current (new_r, new_c)
                        for a_dr, a_dc in directions:
                            a_step = 1
                            current_valid = True
                            while True:
                                a_r = new_r + a_dr * a_step
                                a_c = new_c + a_dc * a_step
                                if not (0 <= a_r < 6 and 0 <= a_c < 6):
                                    break
                                # Update validity for the arrow step
                                if current_valid:
                                    if (a_r == r and a_c == c) or board[a_r][a_c] == 0:
                                        pass
                                    else:
                                        current_valid = False
                                if current_valid:
                                    move_str = f"{r},{c}:{new_r},{new_c}:{a_r},{a_c}"
                                    moves.append(move_str)
                                    a_step += 1
                                else:
                                    break
                        step += 1
    return moves

def apply_move(board, move_str):
    parts = move_str.split(':')
    fr, fc = map(int, parts[0].split(','))
    tr, tc = map(int, parts[1].split(','))
    ar, ac = map(int, parts[2].split(','))
    new_board = board.copy()
    new_board[fr, fc] = 0
    new_board[tr, tc] = 1
    new_board[ar, ac] = -1
    return new_board
