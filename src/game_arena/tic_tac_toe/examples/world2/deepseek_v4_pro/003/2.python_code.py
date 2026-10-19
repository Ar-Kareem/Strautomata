
import numpy as np
import math

def evaluate_board(board, player):
    """
    Heuristic evaluation of board from player's perspective.
    """
    opponent = -player
    score = 0
    
    # Check all lines of 4 for potential wins
    lines = get_all_lines(board)
    
    for line in lines:
        player_count = line.count(player)
        opponent_count = line.count(opponent)
        empty_count = line.count(0)
        
        if player_count == 4:
            return 1000
        if opponent_count == 4:
            return -1000
            
        if opponent_count == 0:
            if player_count == 3 and empty_count == 1:
                score += 100
            elif player_count == 2 and empty_count == 2:
                score += 10
            elif player_count == 1 and empty_count == 3:
                score += 1
                
        if player_count == 0:
            if opponent_count == 3 and empty_count == 1:
                score -= 100
            elif opponent_count == 2 and empty_count == 2:
                score -= 10
            elif opponent_count == 1 and empty_count == 3:
                score -= 1
                
    # Center and corner preferences
    center_positions = [(1,1), (1,2), (2,1), (2,2)]
    corner_positions = [(0,0), (0,3), (3,0), (3,3)]
    
    for r, c in center_positions:
        if board[r][c] == player:
            score += 3
        elif board[r][c] == opponent:
            score -= 3
            
    for r, c in corner_positions:
        if board[r][c] == player:
            score += 2
        elif board[r][c] == opponent:
            score -= 2
            
    return score

def get_all_lines(board):
    lines = []
    # Rows
    for row in board:
        lines.append(row)
    # Cols
    for c in range(4):
        col = [board[r][c] for r in range(4)]
        lines.append(col)
    # Diagonals
    diag1 = [board[i][i] for i in range(4)]
    diag2 = [board[i][3-i] for i in range(4)]
    lines.append(diag1)
    lines.append(diag2)
    # Additional diagonals of length 3 or 4 (all possible 4-in-a-row lines)
    # Already covered: main diags. Also need broken diagonals from 4x4 tic-tac-toe rules.
    # In 4x4 tic-tac-toe, all rows, cols, and any continuous 4 in a line are valid.
    # The above covers all standard rows/cols/main diagonals.
    return lines

def check_win(board, player):
    lines = get_all_lines(board)
    for line in lines:
        if line.count(player) == 4:
            return True
    return False

def is_full(board):
    for row in board:
        if 0 in row:
            return False
    return True

def minimax(board, depth, alpha, beta, maximizing, player):
    opponent = -player
    
    if check_win(board, player):
        return 1000 + depth
    if check_win(board, opponent):
        return -1000 - depth
    if is_full(board):
        return 0
    if depth == 0:
        return evaluate_board(board, player)
    
    valid_moves = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
    
    if maximizing:
        max_eval = -math.inf
        for r, c in valid_moves:
            board[r][c] = player
            eval = minimax(board, depth-1, alpha, beta, False, player)
            board[r][c] = 0
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for r, c in valid_moves:
            board[r][c] = opponent
            eval = minimax(board, depth-1, alpha, beta, True, player)
            board[r][c] = 0
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the best move for player 1.
    """
    board_copy = [row[:] for row in board]
    
    # Immediate win
    for r in range(4):
        for c in range(4):
            if board_copy[r][c] == 0:
                board_copy[r][c] = 1
                if check_win(board_copy, 1):
                    return (r, c)
                board_copy[r][c] = 0
                
    # Block opponent win
    for r in range(4):
        for c in range(4):
            if board_copy[r][c] == 0:
                board_copy[r][c] = -1
                if check_win(board_copy, -1):
                    return (r, c)
                board_copy[r][c] = 0
                
    # Use minimax to find best move
    best_move = None
    best_score = -math.inf
    alpha = -math.inf
    beta = math.inf
    
    valid_moves = [(r, c) for r in range(4) for c in range(4) if board_copy[r][c] == 0]
    
    # Dynamically choose depth based on number of empty cells to stay within time
    empty_count = len(valid_moves)
    if empty_count >= 12:
        depth = 4
    elif empty_count >= 8:
        depth = 5
    else:
        depth = 6
        
    for r, c in valid_moves:
        board_copy[r][c] = 1
        score = minimax(board_copy, depth-1, alpha, beta, False, 1)
        board_copy[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
        alpha = max(alpha, score)
        
    # Fallback to center if no move found
    if best_move is None:
        for r, c in [(1,1), (1,2), (2,1), (2,2)]:
            if board_copy[r][c] == 0:
                return (r, c)
        for r in range(4):
            for c in range(4):
                if board_copy[r][c] == 0:
                    return (r, c)
                    
    return best_move
