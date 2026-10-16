
import numpy as np
from itertools import product

def policy(board) -> str:
    def get_legal_moves(board, player):
        moves = []
        positions = np.where(board == player)
        positions = list(zip(positions[0], positions[1]))
        
        for fr, fc in positions:
            # Possible movement directions (queen moves)
            directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
            for dr, dc in directions:
                for k in range(1, 6):  # Max board size
                    tr = fr + k * dr
                    tc = fc + k * dc
                    if not (0 <= tr < 6 and 0 <= tc < 6):
                        break
                    if board[tr, tc] != 0:
                        break
                    # For each valid to-position, find arrow shots
                    # Temporarily move amazon to find arrow positions
                    temp_board = board.copy()
                    temp_board[fr, fc] = 0
                    temp_board[tr, tc] = player
                    
                    for ar_dr, ar_dc in directions:
                        for arrow_k in range(1, 6):
                            ar_r = tr + arrow_k * ar_dr
                            ar_c = tc + arrow_k * ar_dc
                            if not (0 <= ar_r < 6 and 0 <= ar_c < 6):
                                break
                            if temp_board[ar_r, ar_c] != 0:
                                break
                            moves.append(((fr, fc), (tr, tc), (ar_r, ar_c)))
        return moves

    def evaluate(board):
        # Evaluate position from our perspective (player 1)
        our_positions = np.where(board == 1)
        opp_positions = np.where(board == 2)
        
        # Count mobility
        our_moves = len(get_legal_moves(board, 1))
        opp_moves = len(get_legal_moves(board, 2))
        
        # Mobility difference (primary factor)
        mobility_diff = our_moves - opp_moves
        
        # Territory control (central control bonus)
        center_score = 0
        for r, c in zip(our_positions[0], our_positions[1]):
            # Prefer central positions
            dist_to_center = abs(r - 2.5) + abs(c - 2.5)
            center_score += (2.5 - dist_to_center) * 0.5
            
        for r, c in zip(opp_positions[0], opp_positions[1]):
            dist_to_center = abs(r - 2.5) + abs(c - 2.5)
            center_score -= (2.5 - dist_to_center) * 0.5
            
        # Blocking effectiveness (count how many opponent positions we can potentially block)
        blocking_potential = 0
        for _, (tr, tc), (ar_r, ar_c) in get_legal_moves(board, 1):
            # Check if this arrow shot limits opponent mobility
            temp_board = board.copy()
            temp_board[tr, tc] = 1  # Move to new position
            temp_board[ar_r, ar_c] = -1  # Shoot arrow
            new_opp_moves = len(get_legal_moves(temp_board, 2))
            blocking_potential += max(0, opp_moves - new_opp_moves)
            
        return mobility_diff * 3 + center_score + blocking_potential * 0.5

    def minimax(board, depth, maximizing):
        if depth == 0:
            return evaluate(board), None

        player = 1 if maximizing else 2
        legal_moves = get_legal_moves(board, player)
        
        if not legal_moves:
            # Terminal state - if we can't move, we lose
            return -10000 if maximizing else 10000, None
            
        if maximizing:
            max_eval = float('-inf')
            best_move = None
            # Sort moves to try better ones first (heuristic for alpha-beta pruning)
            legal_moves.sort(key=lambda m: abs(m[0][0]-m[1][0]) + abs(m[0][1]-m[1][1]), reverse=True)
            
            for move in legal_moves[:min(20, len(legal_moves))]:  # Limit branching factor
                (fr, fc), (tr, tc), (ar_r, ar_c) = move
                new_board = board.copy()
                new_board[fr, fc] = 0
                new_board[tr, tc] = player
                new_board[ar_r, ar_c] = -1
                
                eval_score, _ = minimax(new_board, depth - 1, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                    
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = None
            # Sort opponent moves to improve pruning
            legal_moves.sort(key=lambda m: abs(m[0][0]-m[1][0]) + abs(m[0][1]-m[1][1]), reverse=True)
            
            for move in legal_moves[:min(15, len(legal_moves))]:  # Limit opponent branching
                (fr, fc), (tr, tc), (ar_r, ar_c) = move
                new_board = board.copy()
                new_board[fr, fc] = 0
                new_board[tr, tc] = player
                new_board[ar_r, ar_c] = -1
                
                eval_score, _ = minimax(new_board, depth - 1, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                    
            return min_eval, best_move

    # Get all our legal moves
    our_legal_moves = get_legal_moves(board, 1)
    
    if not our_legal_moves:
        # Fallback to any move (should not happen in normal play)
        return "0,0:0,1:0,2"
    
    # Use minimax with depth 2 to select the best move
    _, best_move = minimax(board, 2, True)
    
    if best_move is None:
        # Fallback if minimax fails
        best_move = our_legal_moves[0]
        
    (fr, fc), (tr, tc), (ar_r, ar_c) = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar_r},{ar_c}"
