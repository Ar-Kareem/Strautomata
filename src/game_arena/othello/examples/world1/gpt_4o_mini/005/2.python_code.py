
import numpy as np

def valid_move(board, r, c, player):
    if board[r][c] != 0:
        return False
    
    opponent = 1 if player == 2 else 2
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1), (1, 0), (1, 1),
    ]
    
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == opponent:
            while 0 <= nr < 8 and 0 <= nc < 8:
                if board[nr][nc] == player:
                    return True
                if board[nr][nc] == 0:
                    break
                nr += dr
                nc += dc
    return False

def get_legal_moves(board, player):
    legal_moves = []
    for r in range(8):
        for c in range(8):
            if valid_move(board, r, c, player):
                legal_moves.append((r, c))
    return legal_moves

def evaluate_move(board, r, c, player):
    score = 0
    opponent = 1 if player == 2 else 2
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1), (1, 0), (1, 1),
    ]
    
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == opponent:
            nr += dr
            nc += dc
        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == player:
            score += 1  # Increment score for each opponent disc flipped
            
    return score

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    board = you + opponent
    legal_moves = get_legal_moves(board, 1)
    
    if not legal_moves:
        return "pass"
    
    # Evaluate all possible moves
    best_move = None
    best_score = -1
    
    for r, c in legal_moves:
        score = evaluate_move(board, r, c, 1)
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    if best_move:
        col, row = best_move[1], best_move[0]
        return f"{chr(col + 97)}{8 - row}"  # Convert to chess notation
    
    return "pass"
