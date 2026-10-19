
import numpy as np
from typing import Tuple
import math

def policy(board: list[list[list[int]]]) -> Tuple[int, int, int]:
    board_arr = np.array(board, dtype=int)
    empty = list(zip(*np.where(board_arr == 0)))
    if not empty:
        # fallback, but should not happen
        return (0, 0, 0)
    
    # All possible lines in a 3x3x3 cube
    lines = []
    for i in range(3):
        for j in range(3):
            lines.append([(i,j,k) for k in range(3)])
            lines.append([(i,k,j) for k in range(3)])
            lines.append([(k,i,j) for k in range(3)])
        lines.append([(i,k,k) for k in range(3)])
        lines.append([(i,k,2-k) for k in range(3)])
        lines.append([(k,i,k) for k in range(3)])
        lines.append([(k,i,2-k) for k in range(3)])
        lines.append([(k,k,i) for k in range(3)])
        lines.append([(k,2-k,i) for k in range(3)])
    # main diagonals
    lines.append([(k,k,k) for k in range(3)])
    lines.append([(k,k,2-k) for k in range(3)])
    lines.append([(k,2-k,k) for k in range(3)])
    lines.append([(2-k,k,k) for k in range(3)])
    
    # Precompute line indices for fast evaluation
    line_coords = np.array(lines)
    
    def evaluate(board_state: np.ndarray) -> float:
        score = 0.0
        for line in line_coords:
            vals = board_state[line[:,0], line[:,1], line[:,2]]
            player_count = np.sum(vals == 1)
            opp_count = np.sum(vals == -1)
            if player_count > 0 and opp_count > 0:
                continue
            if player_count == 3:
                return 10000
            if opp_count == 3:
                return -10000
            if player_count == 2:
                score += 100
            elif player_count == 1:
                score += 5
            if opp_count == 2:
                score -= 120  # slightly higher than attack to prioritize block
            elif opp_count == 1:
                score -= 5
        # center bonus
        if board_state[1,1,1] == 1:
            score += 3
        elif board_state[1,1,1] == -1:
            score -= 3
        return score
    
    def minimax(board_state: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> Tuple[float, Tuple]:
        empty_cells = list(zip(*np.where(board_state == 0)))
        if depth == 0 or not empty_cells:
            return evaluate(board_state), (-1, -1, -1)
        
        if maximizing:
            max_eval = -math.inf
            best_move = empty_cells[0]
            for move in empty_cells:
                board_state[move] = 1
                eval_val, _ = minimax(board_state, depth-1, alpha, beta, False)
                board_state[move] = 0
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = move
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = math.inf
            best_move = empty_cells[0]
            for move in empty_cells:
                board_state[move] = -1
                eval_val, _ = minimax(board_state, depth-1, alpha, beta, True)
                board_state[move] = 0
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = move
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval, best_move

    # Iterative deepening with time constraint - simple version, fixed depth
    # We use depth based on number of empty cells
    empty_count = len(empty)
    if empty_count >= 20:
        search_depth = 2
    elif empty_count >= 15:
        search_depth = 3
    elif empty_count >= 10:
        search_depth = 4
    else:
        search_depth = 6  # enough to search to end

    _, best_move = minimax(board_arr, search_depth, -math.inf, math.inf, True)
    return tuple(int(x) for x in best_move)
