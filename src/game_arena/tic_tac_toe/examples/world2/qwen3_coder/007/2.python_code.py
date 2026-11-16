
import copy
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Constants
    PLAYER = 1
    OPPONENT = -1
    EMPTY = 0
    BOARD_SIZE = 4
    
    def check_win(b: List[List[int]], player: int) -> bool:
        # Check rows
        for row in b:
            if all(cell == player for cell in row):
                return True
        
        # Check columns
        for col in range(BOARD_SIZE):
            if all(b[row][col] == player for row in range(BOARD_SIZE)):
                return True
        
        # Check diagonals
        if all(b[i][i] == player for i in range(BOARD_SIZE)):
            return True
        if all(b[i][BOARD_SIZE-1-i] == player for i in range(BOARD_SIZE)):
            return True
            
        return False
    
    def get_empty_positions(b: List[List[int]]) -> List[Tuple[int, int]]:
        positions = []
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if b[i][j] == EMPTY:
                    positions.append((i, j))
        return positions
    
    def is_board_full(b: List[List[int]]) -> bool:
        return all(b[i][j] != EMPTY for i in range(BOARD_SIZE) for j in range(BOARD_SIZE))
    
    def evaluate(b: List[List[int]]) -> int:
        # If player wins, return high score
        if check_win(b, PLAYER):
            return 1000
        # If opponent wins, return low score
        if check_win(b, OPPONENT):
            return -1000
            
        score = 0
        
        # Evaluate rows
        for row in b:
            player_count = row.count(PLAYER)
            opponent_count = row.count(OPPONENT)
            empty_count = row.count(EMPTY)
            
            if opponent_count == 0 and player_count > 0:
                score += 10 ** player_count
            elif player_count == 0 and opponent_count > 0:
                score -= 10 ** opponent_count
        
        # Evaluate columns
        for col in range(BOARD_SIZE):
            col_cells = [b[row][col] for row in range(BOARD_SIZE)]
            player_count = col_cells.count(PLAYER)
            opponent_count = col_cells.count(OPPONENT)
            empty_count = col_cells.count(EMPTY)
            
            if opponent_count == 0 and player_count > 0:
                score += 10 ** player_count
            elif player_count == 0 and opponent_count > 0:
                score -= 10 ** opponent_count
        
        # Evaluate diagonals
        diag1 = [b[i][i] for i in range(BOARD_SIZE)]
        diag2 = [b[i][BOARD_SIZE-1-i] for i in range(BOARD_SIZE)]
        
        for diag in [diag1, diag2]:
            player_count = diag.count(PLAYER)
            opponent_count = diag.count(OPPONENT)
            
            if opponent_count == 0 and player_count > 0:
                score += 10 ** player_count
            elif player_count == 0 and opponent_count > 0:
                score -= 10 ** opponent_count
                
        # Center control (positions (1,1), (1,2), (2,1), (2,2) are more valuable)
        center_positions = [(1,1), (1,2), (2,1), (2,2)]
        for pos in center_positions:
            if b[pos[0]][pos[1]] == PLAYER:
                score += 2
            elif b[pos[0]][pos[1]] == OPPONENT:
                score -= 2
                
        return score
    
    def minimax(b: List[List[int]], depth: int, alpha: int, beta: int, is_maximizing: bool) -> int:
        # Terminal conditions
        if check_win(b, PLAYER):
            return 1000 + depth  # Prefer quicker wins
        if check_win(b, OPPONENT):
            return -1000 - depth  # Prefer slower losses
        if is_board_full(b) or depth == 0:
            return evaluate(b)
        
        if is_maximizing:
            max_eval = float('-inf')
            for i, j in get_empty_positions(b):
                b[i][j] = PLAYER
                eval_score = minimax(b, depth - 1, alpha, beta, False)
                b[i][j] = EMPTY
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for i, j in get_empty_positions(b):
                b[i][j] = OPPONENT
                eval_score = minimax(b, depth - 1, alpha, beta, True)
                b[i][j] = EMPTY
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Check if we can win immediately
    for i, j in get_empty_positions(board):
        board[i][j] = PLAYER
        if check_win(board, PLAYER):
            board[i][j] = EMPTY
            return (i, j)
        board[i][j] = EMPTY
    
    # Check if opponent can win immediately and block
    for i, j in get_empty_positions(board):
        board[i][j] = OPPONENT
        if check_win(board, OPPONENT):
            board[i][j] = EMPTY
            return (i, j)
        board[i][j] = EMPTY
    
    # Use minimax to find best move
    best_move = None
    best_value = float('-inf')
    
    # Try different depths based on number of empty positions
    empty_count = len(get_empty_positions(board))
    depth = min(5, max(1, empty_count // 3))  # Adjust depth based on board fill
    
    for i, j in get_empty_positions(board):
        board[i][j] = PLAYER
        move_value = minimax(board, depth, float('-inf'), float('inf'), False)
        board[i][j] = EMPTY
        
        if move_value > best_value:
            best_value = move_value
            best_move = (i, j)
    
    # Fallback to first empty position if no better move found
    if best_move is None:
        empty_positions = get_empty_positions(board)
        if empty_positions:
            best_move = empty_positions[0]
    
    return best_move
