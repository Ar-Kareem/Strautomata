
import random
from typing import List

ROW_COUNT = 6
COLUMN_COUNT = 7
EMPTY = 0
PLAYER_PIECE = 1
OPPONENT_PIECE = -1

def policy(board: list[list[int]]) -> int:
    valid_moves = get_valid_locations(board)
    if not valid_moves:
        return 0
    
    # Check for immediate win
    for col in valid_moves:
        row = get_next_open_row(board, col)
        temp_board = [r[:] for r in board]
        temp_board[row][col] = PLAYER_PIECE
        if winning_move(temp_board, PLAYER_PIECE):
            return col
    
    # Check for immediate block (opponent win next turn)
    for col in valid_moves:
        row = get_next_open_row(board, col)
        temp_board = [r[:] for r in board]
        temp_board[row][col] = OPPONENT_PIECE
        if winning_move(temp_board, OPPONENT_PIECE):
            return col
    
    # Order moves by center preference for better alpha-beta pruning
    ordered_moves = sorted(valid_moves, key=lambda x: abs(x - 3))
    
    best_score = -float('inf')
    best_col = ordered_moves[0]
    
    for col in ordered_moves:
        row = get_next_open_row(board, col)
        temp_board = [r[:] for r in board]
        temp_board[row][col] = PLAYER_PIECE
        score = minimax(temp_board, 5, -float('inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col

def get_valid_locations(board: list[list[int]]) -> List[int]:
    return [c for c in range(COLUMN_COUNT) if board[0][c] == EMPTY]

def get_next_open_row(board: list[list[int]], col: int) -> int:
    for r in range(ROW_COUNT - 1, -1, -1):
        if board[r][col] == EMPTY:
            return r
    return -1

def winning_move(board: list[list[int]], piece: int) -> bool:
    # Check horizontal
    for c in range(COLUMN_COUNT - 3):
        for r in range(ROW_COUNT):
            if all(board[r][c + i] == piece for i in range(4)):
                return True
    # Check vertical
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT - 3):
            if all(board[r + i][c] == piece for i in range(4)):
                return True
    # Check positively sloped diagonals
    for c in range(COLUMN_COUNT - 3):
        for r in range(ROW_COUNT - 3):
            if all(board[r + i][c + i] == piece for i in range(4)):
                return True
    # Check negatively sloped diagonals
    for c in range(COLUMN_COUNT - 3):
        for r in range(3, ROW_COUNT):
            if all(board[r - i][c + i] == piece for i in range(4)):
                return True
    return False

def evaluate_window(window: List[int], piece: int) -> int:
    score = 0
    opp_piece = OPPONENT_PIECE if piece == PLAYER_PIECE else PLAYER_PIECE
    
    if window.count(piece) == 4:
        score += 100
    elif window.count(piece) == 3 and window.count(EMPTY) == 1:
        score += 5
    elif window.count(piece) == 2 and window.count(EMPTY) == 2:
        score += 2
    
    if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
        score -= 4
    
    return score

def score_position(board: list[list[int]], piece: int) -> int:
    score = 0
    
    # Center column preference
    center_array = [board[r][3] for r in range(ROW_COUNT)]
    center_count = center_array.count(piece)
    score += center_count * 3
    
    # Horizontal
    for r in range(ROW_COUNT):
        row_array = board[r]
        for c in range(COLUMN_COUNT - 3):
            window = row_array[c:c+4]
            score += evaluate_window(window, piece)
    
    # Vertical
    for c in range(COLUMN_COUNT):
        col_array = [board[r][c] for r in range(ROW_COUNT)]
        for r in range(ROW_COUNT - 3):
            window = col_array[r:r+4]
            score += evaluate_window(window, piece)
    
    # Positive diagonal
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, piece)
    
    # Negative diagonal
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            window = [board[r+3-i][c+i] for i in range(4)]
            score += evaluate_window(window, piece)
    
    return score

def is_terminal_node(board: list[list[int]]) -> bool:
    return winning_move(board, PLAYER_PIECE) or winning_move(board, OPPONENT_PIECE) or len(get_valid_locations(board)) == 0

def minimax(board: list[list[int]], depth: int, alpha: float, beta: float, maximizing_player: bool) -> float:
    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)
    
    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, PLAYER_PIECE):
                return 1000000.0
            elif winning_move(board, OPPONENT_PIECE):
                return -1000000.0
            else:
                return 0.0
        else:
            return score_position(board, PLAYER_PIECE)
    
    if maximizing_player:
        value = -float('inf')
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = [r[:] for r in board]
            b_copy[row][col] = PLAYER_PIECE
            new_score = minimax(b_copy, depth - 1, alpha, beta, False)
            value = max(value, new_score)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = float('inf')
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = [r[:] for r in board]
            b_copy[row][col] = OPPONENT_PIECE
            new_score = minimax(b_copy, depth - 1, alpha, beta, True)
            value = min(value, new_score)
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value
