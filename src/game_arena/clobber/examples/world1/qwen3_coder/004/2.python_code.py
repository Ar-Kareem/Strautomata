
import numpy as np
from collections import deque

def policy(you: list[int], opponent: list[int]) -> str:
    you = np.array(you)
    opponent = np.array(opponent)
    
    rows, cols = 5, 6
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    
    def get_legal_moves(board_you, board_opponent):
        moves = []
        for r in range(rows):
            for c in range(cols):
                if board_you[r, c] == 1:
                    for dr, dc, dir_char in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if board_opponent[nr, nc] == 1:
                                moves.append((r, c, dir_char))
        return moves
    
    def apply_move(board_you, board_opponent, r, c, direction):
        new_you = board_you.copy()
        new_opponent = board_opponent.copy()
        
        dr, dc = 0, 0
        if direction == 'U': dr = -1
        elif direction == 'R': dc = 1
        elif direction == 'D': dr = 1
        elif direction == 'L': dc = -1
        
        nr, nc = r + dr, c + dc
        
        new_you[r, c] = 0
        new_you[nr, nc] = 1
        new_opponent[nr, nc] = 0
        
        return new_you, new_opponent
    
    def count_moves(board_you, board_opponent):
        return len(get_legal_moves(board_you, board_opponent))
    
    def is_opponent_stuck(board_you, board_opponent):
        return len(get_legal_moves(board_opponent, board_you)) == 0
    
    def evaluate_move(board_you, board_opponent):
        my_moves = count_moves(board_you, board_opponent)
        opp_moves = count_moves(board_opponent, board_you)
        return my_moves - opp_moves
    
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        # Should not happen as we must return a move
        return "0,0,U"
    
    # Check for immediate win
    for r, c, direction in legal_moves:
        new_you, new_opponent = apply_move(you, opponent, r, c, direction)
        # After our move, it's opponent's turn with new_you and new_opponent swapped in get_legal_moves
        opp_legal = get_legal_moves(new_opponent, new_you)
        if not opp_legal:
            return f"{r},{c},{direction}"
    
    # Evaluate moves with 1-ply lookahead
    best_score = -float('inf')
    best_move = legal_moves[0]
    
    for r, c, direction in legal_moves:
        new_you, new_opponent = apply_move(you, opponent, r, c, direction)
        # Evaluate resulting position (from our perspective after opponent's turn)
        score = evaluate_move(new_you, new_opponent)
        
        # If this move is better, or same score but we want the first one
        if score > best_score:
            best_score = score
            best_move = (r, c, direction)
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
