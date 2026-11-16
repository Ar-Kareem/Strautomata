
import numpy as np
from math import inf
from copy import deepcopy

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    state = np.array(board)
    
    # Check if this is the first move (empty board)
    if np.all(state == 0):
        return (0, 0)  # Start with top-left corner (can be changed)
    
    AI_PLAYER = 1
    HUMAN_PLAYER = -1
    
    def evaluate_window(window, player):
        score = 0
        opp_player = -player
        if np.count_nonzero(window == player) == 4:
            score += 100
        elif np.count_nonzero(window == player) == 3 and np.count_nonzero(window == 0) == 1:
            score += 5
        elif np.count_nonzero(window == player) == 2 and np.count_nonzero(window == 0) == 2:
            score += 2
        if np.count_nonzero(window == opp_player) == 3 and np.count_nonzero(window == 0) == 1:
            score -= 4  # Block opponent
        return score
    
    def evaluate_state(state):
        score = 0
        
        # Check rows
        for row in state:
            score += evaluate_window(row, AI_PLAYER)
        
        # Check columns
        for col in state.T:
            score += evaluate_window(col, AI_PLAYER)
        
        # Check diagonals
        diag1 = state.diagonal()
        diag2 = np.fliplr(state).diagonal()
        score += evaluate_window(diag1, AI_PLAYER)
        score += evaluate_window(diag2, AI_PLAYER)
        
        return score
    
    def is_terminal(state):
        # Check rows
        for row in state:
            if abs(sum(row)) == 4:
                return True
        
        # Check columns
        for col in state.T:
            if abs(sum(col)) == 4:
                return True
        
        # Check diagonals
        diag1 = sum(state.diagonal())
        diag2 = sum(np.fliplr(state).diagonal())
        if abs(diag1) == 4 or abs(diag2) == 4:
            return True
        
        # Check if board is full
        if not (state == 0).any():
            return True
        
        return False
    
    def minimax(state, depth, alpha, beta, maximizing_player):
        if depth == 0 or is_terminal(state):
            return evaluate_state(state)
        
        if maximizing_player:
            max_eval = -inf
            for move in get_valid_moves(state):
                new_state = make_move(state, move, AI_PLAYER)
                eval = minimax(new_state, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = inf
            for move in get_valid_moves(state):
                new_state = make_move(state, move, HUMAN_PLAYER)
                eval = minimax(new_state, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
    
    def get_valid_moves(state):
        moves = []
        for i in range(4):
            for j in range(4):
                if state[i, j] == 0:
                    moves.append((i, j))
        return moves
    
    def make_move(state, move, player):
        new_state = deepcopy(state)
        new_state[move[0], move[1]] = player
        return new_state
    
    # First check if we can win in the next move
    for move in get_valid_moves(state):
        new_state = make_move(state, move, AI_PLAYER)
        if is_terminal(new_state):
            return move
    
    # Then check if opponent can win in next move and block them
    for move in get_valid_moves(state):
        new_state = make_move(state, move, HUMAN_PLAYER)
        if is_terminal(new_state):
            return move
    
    # If no immediate win/loss, use minimax with limited depth to save time
    best_move = None
    best_value = -inf
    depth = 3  # Depth can be adjusted based on performance constraints
    
    for move in get_valid_moves(state):
        new_state = make_move(state, move, AI_PLAYER)
        move_value = minimax(new_state, depth, -inf, inf, False)
        if move_value > best_value:
            best_value = move_value
            best_move = move
    
    return best_move if best_move is not None else get_valid_moves(state)[0]
