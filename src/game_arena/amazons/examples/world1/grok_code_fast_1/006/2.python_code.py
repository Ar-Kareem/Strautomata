
import numpy as np
import math  # Though not used in this code, kept for consistency

def policy(board):
    if not (isinstance(board, np.ndarray) and board.shape == (6, 6)):
        raise ValueError("Invalid board: must be a 6x6 numpy array.")
    
    dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    def is_valid(r, c):
        return 0 <= r < 6 and 0 <= c < 6
    
    def get_move_positions(curr_board, r, c):
        pos = []
        for dr, dc in dirs:
            for k in range(1, 7):  # max distance on 6x6
                nr = r + dr * k
                nc = c + dc * k
                if not is_valid(nr, nc):
                    break
                if curr_board[nr, nc] != 0:
                    break
                pos.append((nr, nc))
        return pos
    
    def count_moves(curr_board, player):
        pos = np.where(curr_board == player)
        total_moves = 0
        for i in range(len(pos[0])):
            r, c = pos[0][i], pos[1][i]
            move_list = get_move_positions(curr_board, r, c)
            for to_r, to_c in move_list:
                temp = curr_board.copy()
                temp[to_r, to_c] = player
                temp[r, c] = 0
                arrow_list = get_move_positions(temp, to_r, to_c)
                total_moves += len(arrow_list)
        return total_moves
    
    my_pos = np.where(board == 1)
    my_pos_list = list(zip(my_pos[0], my_pos[1]))
    
    best_score = -float('inf')
    best_move = None
    for fr, fc in my_pos_list:
        move_list = get_move_positions(board, fr, fc)
        for tr, tc in move_list:
            temp_board = board.copy()
            temp_board[fr, fc] = 0
            temp_board[tr, tc] = 1
            arrow_list = get_move_positions(temp_board, tr, tc)
            for ar, ac in arrow_list:
                board_after = temp_board.copy()
                board_after[ar, ac] = -1
                my_future_moves = count_moves(board_after, 1)
                opp_future_moves = count_moves(board_after, 2)
                score = my_future_moves - opp_future_moves
                if score > best_score:
                    best_score = score
                    best_move = f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
    
    if best_move is None:
        raise RuntimeError("No legal move found, which should not happen if board is valid.")
    return best_move
