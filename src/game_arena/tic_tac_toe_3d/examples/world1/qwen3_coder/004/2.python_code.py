
import copy
from typing import List, Tuple, Optional

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Constants
    PLAYER = 1
    OPPONENT = -1
    EMPTY = 0
    
    def is_winner(board, player):
        # Check all possible winning lines in 3D tic-tac-toe
        # Check rows in each layer
        for z in range(3):
            for y in range(3):
                if all(board[z][y][x] == player for x in range(3)):
                    return True
            for x in range(3):
                if all(board[z][y][x] == player for y in range(3)):
                    return True
            # Check diagonals in this z-layer
            if all(board[z][i][i] == player for i in range(3)):
                return True
            if all(board[z][i][2-i] == player for i in range(3)):
                return True
        
        # Check columns across layers
        for y in range(3):
            for x in range(3):
                if all(board[z][y][x] == player for z in range(3)):
                    return True
        
        # Check vertical diagonals
        for i in range(3):
            # Along y-axis diagonals
            if all(board[z][i][z] == player for z in range(3)):
                return True
            if all(board[z][i][2-z] == player for z in range(3)):
                return True
            # Along x-axis diagonals
            if all(board[z][z][i] == player for z in range(3)):
                return True
            if all(board[z][2-z][i] == player for z in range(3)):
                return True
        
        # Check main 3D diagonals
        if all(board[i][i][i] == player for i in range(3)):
            return True
        if all(board[i][i][2-i] == player for i in range(3)):
            return True
        if all(board[i][2-i][i] == player for i in range(3)):
            return True
        if all(board[i][2-i][2-i] == player for i in range(3)):
            return True
            
        return False
    
    def get_empty_positions(board):
        positions = []
        for z in range(3):
            for y in range(3):
                for x in range(3):
                    if board[z][y][x] == EMPTY:
                        positions.append((z, y, x))
        return positions
    
    def minimax(board, depth, is_maximizing, alpha, beta):
        if is_winner(board, PLAYER):
            return 1000 + depth  # Prefer quicker wins
        if is_winner(board, OPPONENT):
            return -1000 - depth  # Prefer slower losses
        if depth == 0 or not get_empty_positions(board):
            return evaluate_board(board)
        
        if is_maximizing:
            max_eval = float('-inf')
            for z, y, x in get_empty_positions(board):
                board[z][y][x] = PLAYER
                eval_score = minimax(board, depth - 1, False, alpha, beta)
                board[z][y][x] = EMPTY
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for z, y, x in get_empty_positions(board):
                board[z][y][x] = OPPONENT
                eval_score = minimax(board, depth - 1, True, alpha, beta)
                board[z][y][x] = EMPTY
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def evaluate_board(board):
        score = 0
        
        # Prefer center positions
        if board[1][1][1] == PLAYER:
            score += 10
        elif board[1][1][1] == OPPONENT:
            score -= 10
            
        # Count potential lines
        # Check all lines and give points based on how many of our pieces are in them
        # This is a simplified version - a full implementation would be more complex
        
        # Simple heuristic: count pieces and give small bonus for center planes
        player_count = 0
        opponent_count = 0
        for z in range(3):
            for y in range(3):
                for x in range(3):
                    if board[z][y][x] == PLAYER:
                        player_count += 1
                        # Bonus for positions that could lead to wins
                        if z == 1: score += 1
                        if y == 1: score += 1
                        if x == 1: score += 1
                    elif board[z][y][x] == OPPONENT:
                        opponent_count += 1
        
        return score + (player_count - opponent_count) * 5
    
    # First, check if we can win immediately
    for z, y, x in get_empty_positions(board):
        board[z][y][x] = PLAYER
        if is_winner(board, PLAYER):
            board[z][y][x] = EMPTY
            return (z, y, x)
        board[z][y][x] = EMPTY
    
    # Second, check if opponent can win and block
    for z, y, x in get_empty_positions(board):
        board[z][y][x] = OPPONENT
        if is_winner(board, OPPONENT):
            board[z][y][x] = EMPTY
            return (z, y, x)
        board[z][y][x] = EMPTY
    
    # Otherwise, use minimax to find the best move
    best_move = None
    best_value = float('-inf')
    
    # If the board is mostly empty, we might want to just pick a good heuristic position
    empty_count = len(get_empty_positions(board))
    
    if empty_count > 20:  # Early game, use simple heuristic
        # Prefer center, then corners
        priority_moves = [(1,1,1), (0,0,0), (0,0,2), (0,2,0), (0,2,2), 
                         (2,0,0), (2,0,2), (2,2,0), (2,2,2),
                         (1,1,0), (1,1,2), (1,0,1), (1,2,1), (0,1,1), (2,1,1)]
        for move in priority_moves:
            z, y, x = move
            if board[z][y][x] == EMPTY:
                return (z, y, x)
    
    # Use minimax for deeper search with limited depth to stay within time limits
    search_depth = min(3, empty_count // 3 + 1)  # Adjust depth based on empty spaces
    
    for z, y, x in get_empty_positions(board):
        board[z][y][x] = PLAYER
        move_value = minimax(board, search_depth, False, float('-inf'), float('inf'))
        board[z][y][x] = EMPTY
        
        if move_value > best_value:
            best_value = move_value
            best_move = (z, y, x)
    
    # Fallback if no move found
    if best_move is None:
        empty_positions = get_empty_positions(board)
        if empty_positions:
            best_move = empty_positions[0]
    
    return best_move

# Test function definition to verify syntax
if __name__ == "__main__":
    # Example board test
    test_board = [[[0, 0, 0], [0, 0, 0], [0, 0, 0]],
                  [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
                  [[0, 0, 0], [0, 0, 0], [0, 0, 0]]]
    print(policy(test_board))
