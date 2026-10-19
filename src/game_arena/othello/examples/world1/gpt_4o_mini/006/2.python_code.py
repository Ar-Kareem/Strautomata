
import numpy as np

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), 
              (0, -1),         (0, 1), 
              (1, -1), (1, 0), (1, 1)]

def is_valid_move(board, r, c, player):
    if board[r][c] != 0:
        return False
    opponent = 1 if player == 2 else 2
    can_flip = False
    
    for dr, dc in DIRECTIONS:
        rr, cc = r + dr, c + dc
        if 0 <= rr < 8 and 0 <= cc < 8 and board[rr][cc] == opponent:
            while 0 <= rr < 8 and 0 <= cc < 8:
                if board[rr][cc] == 0:
                    break
                if board[rr][cc] == player:
                    can_flip = True
                    break
                rr += dr
                cc += dc
                
    return can_flip

def get_legal_moves(board, player):
    legal_moves = []
    for r in range(8):
        for c in range(8):
            if is_valid_move(board, r, c, player):
                legal_moves.append((r, c))
    return legal_moves

def evaluate_move(board, r, c, player):
    opponent = 1 if player == 2 else 2
    flips = 0
    
    for dr, dc in DIRECTIONS:
        rr, cc = r + dr, c + dc
        while 0 <= rr < 8 and 0 <= cc < 8:
            if board[rr][cc] == 0:
                break
            if board[rr][cc] == player:
                flips += 1
                break
            rr += dr
            cc += dc
            
    return flips

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    board = you + opponent
    legal_moves = get_legal_moves(board, 1)
    
    if not legal_moves:
        return "pass"

    best_move = None
    best_flip_count = -1
    
    for r, c in legal_moves:
        flip_count = evaluate_move(board, r, c, 1)
        if flip_count > best_flip_count:
            best_flip_count = flip_count
            best_move = (r, c)

    if best_move:
        r, c = best_move
        return f"{chr(c + ord('a'))}{r + 1}"

    return "pass"
