
import random
import numpy as np
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Convert to 0-indexed coordinates for internal processing
    me_coords = [(row-1, col-1) for row, col in me]
    opponent_coords = [(row-1, col-1) for row, col in opponent]
    
    # Create board state (0 = empty, 1 = me, 2 = opponent)
    board = np.zeros((19, 19), dtype=int)
    for r, c in me_coords:
        board[r, c] = 1
    for r, c in opponent_coords:
        board[r, c] = 2
    
    # Get all possible moves
    def get_valid_moves():
        moves = []
        for r in range(19):
            for c in range(19):
                if board[r, c] == 0:
                    moves.append((r, c))
        return moves
    
    # Check if a move is legal (simple implementation)
    def is_legal_move(r, c, player):
        # Can't play on occupied position
        if board[r, c] != 0:
            return False
        # Check if move would capture
        # For simplicity, we'll not implement full ko rule here
        return True
    
    # Simple heuristic for move evaluation (basic safety + territory)
    def evaluate_move(r, c, player):
        # Prioritize center and corners
        center_dist = min(abs(r - 9), abs(c - 9))
        score = 10 - center_dist
        
        # Avoid suicidal moves - but we won't do full analysis here
        # Just basic safety
        if score > 0:  # Simplification
            return score
        return 1
    
    # Basic MCTS implementation
    def mcts_move(board_state, player, opponent):
        valid_moves = get_valid_moves()
        if not valid_moves:
            return (0, 0)
        
        # Simplified: just pick based on simple heuristic
        best_score = -1
        best_move = valid_moves[0]
        
        # Compute scores for all valid moves
        scores = []
        for r, c in valid_moves:
            score = evaluate_move(r, c, player)
            
            # Prefer moves next to existing stones
            adjacent_score = 0
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < 19 and 0 <= nc < 19:
                    if board_state[nr, nc] == player or board_state[nr, nc] == opponent:
                        adjacent_score += 1
            score += adjacent_score * 2
            
            scores.append((score, (r, c)))
        
        if not scores:
            return valid_moves[0]
        
        # Return highest scoring move
        best_move = max(scores, key=lambda x: x[0])[1]
        return best_move
    
    # Perform MCTS search
    move = mcts_move(board, 1, 2)
    
    # Convert back to 1-indexed coordinates
    if move == (0, 0):
        return (0, 0)
    return (move[0] + 1, move[1] + 1)
