
import numpy as np
from typing import List, Tuple

def policy(board) -> str:
    # Directions: 8 possible (orthogonal + diagonal)
    directions = [(-1,-1), (-1,0), (-1,1),
                  (0,-1),           (0,1),
                  (1,-1),  (1,0),   (1,1)]
    
    def is_in_bounds(r, c):
        return 0 <= r < 6 and 0 <= c < 6
    
    def trace_path(start, direction, steps=None):
        """Yield all positions from start in direction until blocked or out of bounds."""
        r, c = start
        dr, dc = direction
        path = []
        for _ in range(1, 6):  # Max 5 steps on 6x6
            r += dr
            c += dc
            if not is_in_bounds(r, c):
                break
            path.append((r, c))
        return path

    def get_ray_moves(start, board_state):
        """Get all squares reachable from start via unobstructed queen moves."""
        moves = []
        for d in directions:
            for r, c in trace_path(start, d):
                if board_state[r, c] == 0:
                    moves.append((r, c))
                else:
                    break
        return moves

    def get_legal_moves_and_shots():
        """Generate all legal (from, to, arrow) moves for player 1."""
        legal_moves = []
        for r in range(6):
            for c in range(6):
                if board[r, c] == 1:  # Your amazon
                    # Get all possible move destinations
                    for to_r, to_c in get_ray_moves((r, c), board):
                        # Simulate move: create intermediate board
                        temp_board = board.copy()
                        temp_board[r, c] = 0
                        temp_board[to_r, to_c] = 1

                        # From new position, get all legal arrow shots
                        for arrow_r, arrow_c in get_ray_moves((to_r, to_c), temp_board):
                            legal_moves.append((r, c, to_r, to_c, arrow_r, arrow_c))
        return legal_moves

    def evaluate_move(move):
        from_r, from_c, to_r, to_c, arrow_r, arrow_c = move
        
        # Simulate the move
        temp_board = board.copy()
        temp_board[from_r, from_c] = 0
        temp_board[to_r, to_c] = 1
        temp_board[arrow_r, arrow_c] = -1  # Shoot arrow

        # Heuristic score components
        score = 0

        # 1. Centrality of new amazon position
        center = (2.5, 2.5)
        dist_to_center = abs(to_r - center[0]) + abs(to_c - center[1])
        score += (5 - dist_to_center)  # Prefer central

        # 2. Penalize if arrow blocks own mobility
        my_amazons = [(i, j) for i in range(6) for j in range(6) if temp_board[i, j] == 1]
        opponent_amazons = [(i, j) for i in range(6) for j in range(6) if temp_board[i, j] == 2]
        
        # Evaluate own future mobility (after move)
        my_mobility = 0
        for ar, ac in my_amazons:
            my_mobility += len(get_ray_moves((ar, ac), temp_board))
        
        # Evaluate opponent future mobility
        opp_mobility = 0
        for ar, ac in opponent_amazons:
            opp_mobility += len(get_ray_moves((ar, ac), temp_board))
        
        # Reward high own mobility, penalize opp mobility
        score += 0.1 * my_mobility
        score -= 0.2 * opp_mobility

        # 3. Bonus if arrow splits opponent or blocks access to center
        if opp_mobility == 0:
            score += 1000  # Win move!
        
        # 4. Arrow near opponent amazons is good (reduces space)
        for opp_r, opp_c in opponent_amazons:
            manhattan = abs(arrow_r - opp_r) + abs(arrow_c - opp_c)
            if manhattan <= 2:
                score += 0.1
        
        return score

    # Get all legal moves
    legal_moves = get_legal_moves_and_shots()
    
    # Fallback: if no legal moves, return a dummy (should not happen per rules)
    if not legal_moves:
        # Find any amazon and attempt to move it (shouldn't happen)
        for r in range(6):
            for c in range(6):
                if board[r, c] == 1:
                    return f"{r},{c}:{r},{c}:0,0"  # invalid, but avoid crash
    
    # Score all legal moves
    scored_moves = [(move, evaluate_move(move)) for move in legal_moves]
    
    # Choose best move
    best_move = max(scored_moves, key=lambda x: x[1])[0]
    
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}:{best_move[4]},{best_move[5]}"
