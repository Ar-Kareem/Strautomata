
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    
    # Get all legal moves (where board is 0)
    legal_moves = [(r, c) for r in range(3) for c in range(3) if board[r, c] == 0]
    
    # Check if we can win with any move
    for move in legal_moves:
        r, c = move
        test_board = board.copy()
        test_board[r, c] = 1
        if check_win(test_board, 1):
            return move
    
    # Create a simple heuristic function for move evaluation
    def score_move(move):
        r, c = move
        # Count how many lines this position is part of
        row = board[r, :]
        col = board[:, c]
        if r == c:
            diag1 = board.diagonal()
        else:
            diag1 = None
        if r == 2 - c:
            diag2 = board[[0, 1, 2], [2, 1, 0]]
        else:
            diag2 = None
            
        lines = []
        if diag1 is not None:
            lines.append(diag1)
        if diag2 is not None:
            lines.append(diag2)
        lines.append(row)
        lines.append(col)
        
        # Score based on how many lines contain one of our pieces
        score = 0
        for line in lines:
            if 1 in line and 0 in line:
                score += 1
        # Preference for positions closer to the center
        score += -abs(r - 1) - abs(c - 1)
        return score
    
    # Score all moves and return the one with the highest score
    return max(legal_moves, key=score_move)

def check_win(board, player):
    # Check rows
    for i in range(3):
        if all(board[i, j] == player for j in range(3)):
            return True
    
    # Check columns
    for j in range(3):
        if all(board[i, j] == player for i in range(3)):
            return True
    
    # Check diagonals
    if all(board[i, i] == player for i in range(3)):
        return True
    if all(board[i, 2-i] == player for i in range(3)):
        return True
    
    return False
