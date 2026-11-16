
import math
import time
import random
from typing import List, Tuple, Optional

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Create board state
    board = [[None for _ in range(8)] for _ in range(8)]
    for r, c in me:
        board[r][c] = color
    for r, c in opp:
        board[r][c] = 'b' if color == 'w' else 'w'
    
    # Determine forward direction
    forward = 1 if color == 'w' else -1
    home_row = 7 if color == 'w' else 0
    opponent_home_row = 0 if color == 'w' else 7
    
    # Generate all legal moves
    def generate_moves(board_state, player_color, is_maximizing):
        moves = []
        forward_dir = 1 if player_color == 'w' else -1
        player_pieces = []
        
        # Find all pieces for this player
        for r in range(8):
            for c in range(8):
                if board_state[r][c] == player_color:
                    player_pieces.append((r, c))
        
        # For each piece, generate possible moves
        for r, c in player_pieces:
            # Straight forward
            new_r = r + forward_dir
            if 0 <= new_r < 8:
                if board_state[new_r][c] is None:
                    moves.append(((r, c), (new_r, c)))
            
            # Diagonal captures/forward
            for dc in [-1, 1]:
                new_c = c + dc
                if 0 <= new_r < 8 and 0 <= new_c < 8:
                    target = board_state[new_r][new_c]
                    if target is None:
                        moves.append(((r, c), (new_r, new_c)))
                    elif target != player_color:
                        moves.append(((r, c), (new_r, new_c)))
        
        # Sort moves for better alpha-beta pruning
        def move_score(move):
            (fr, fc), (tr, tc) = move
            score = 0
            # Prioritize captures
            if board_state[tr][tc] is not None and board_state[tr][tc] != player_color:
                score += 1000
            # Prioritize moves to opponent's home row
            if (player_color == 'w' and tr == 7) or (player_color == 'b' and tr == 0):
                score += 500
            # Prioritize forward movement
            score += abs(tr - fr) * 10
            return score
        
        moves.sort(key=move_score, reverse=is_maximizing)
        return moves
    
    # Evaluation function
    def evaluate(board_state, maximizing_color):
        score = 0
        opponent_color = 'b' if maximizing_color == 'w' else 'w'
        
        # Material evaluation
        for r in range(8):
            for c in range(8):
                if board_state[r][c] == maximizing_color:
                    # Base piece value
                    score += 100
                    
                    # Advancement bonus (closer to opponent's home row)
                    if maximizing_color == 'w':
                        advancement = r  # white wants high row numbers
                    else:
                        advancement = 7 - r  # black wants low row numbers
                    score += advancement * 3
                    
                    # Center control bonus
                    if 2 <= c <= 5:
                        score += 2
                    
                    # Penalize doubled pieces in same column
                    column_count = 0
                    for rr in range(8):
                        if board_state[rr][c] == maximizing_color:
                            column_count += 1
                    if column_count > 1:
                        score -= 5
                    
                    # Bonus for protecting home row
                    home_r = 0 if maximizing_color == 'b' else 7
                    if r == home_r:
                        # Check if protected from diagonal attacks
                        protect_bonus = 0
                        for dc in [-1, 1]:
                            attack_r = home_r + (-forward if maximizing_color == 'w' else forward)
                            attack_c = c + dc
                            if 0 <= attack_r < 8 and 0 <= attack_c < 8:
                                if board_state[attack_r][attack_c] == maximizing_color:
                                    protect_bonus += 3
                        score += protect_bonus
                
                elif board_state[r][c] == opponent_color:
                    # Same evaluation but negative for opponent
                    score -= 100
                    if opponent_color == 'w':
                        advancement = r
                    else:
                        advancement = 7 - r
                    score -= advancement * 3
                    
                    if 2 <= c <= 5:
                        score -= 2
        
        # Encourage connected pieces
        for r in range(8):
            for c in range(8):
                if board_state[r][c] == maximizing_color:
                    # Check adjacent same-color pieces
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            if board_state[nr][nc] == maximizing_color:
                                score += 1
        
        return score
    
    # Minimax with alpha-beta pruning
    def minimax(board_state, depth, alpha, beta, maximizing_player, max_color):
        # Terminal conditions
        # Check if max player wins
        for c in range(8):
            if (max_color == 'w' and board_state[7][c] == max_color) or \
               (max_color == 'b' and board_state[0][c] == max_color):
                return 10000 if maximizing_player else -10000
        
        # Check if min player wins
        min_color = 'b' if max_color == 'w' else 'w'
        for c in range(8):
            if (min_color == 'w' and board_state[7][c] == min_color) or \
               (min_color == 'b' and board_state[0][c] == min_color):
                return -10000 if maximizing_player else 10000
        
        if depth == 0:
            return evaluate(board_state, max_color)
        
        current_color = max_color if maximizing_player else min_color
        moves = generate_moves(board_state, current_color, maximizing_player)
        
        if not moves:
            # No moves available
            return -10000 if maximizing_player else 10000
        
        if maximizing_player:
            max_eval = -math.inf
            for move in moves:
                (fr, fc), (tr, tc) = move
                
                # Make move
                captured = board_state[tr][tc]
                board_state[tr][tc] = board_state[fr][fc]
                board_state[fr][fc] = None
                
                eval_score = minimax(board_state, depth - 1, alpha, beta, False, max_color)
                
                # Undo move
                board_state[fr][fc] = board_state[tr][tc]
                board_state[tr][tc] = captured
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for move in moves:
                (fr, fc), (tr, tc) = move
                
                # Make move
                captured = board_state[tr][tc]
                board_state[tr][tc] = board_state[fr][fc]
                board_state[fr][fc] = None
                
                eval_score = minimax(board_state, depth - 1, alpha, beta, True, max_color)
                
                # Undo move
                board_state[fr][fc] = board_state[tr][tc]
                board_state[tr][tc] = captured
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Determine search depth based on game phase
    total_pieces = len(me) + len(opp)
    if total_pieces <= 8:
        search_depth = 5
    elif total_pieces <= 16:
        search_depth = 4
    else:
        search_depth = 3
    
    # Get all legal moves for the current player
    legal_moves = generate_moves(board, color, True)
    
    # If we can win immediately, do it
    for move in legal_moves:
        (fr, fc), (tr, tc) = move
        if (color == 'w' and tr == 7) or (color == 'b' and tr == 0):
            return move
    
    # Find best move using minimax
    best_move = None
    best_value = -math.inf
    
    for move in legal_moves:
        (fr, fc), (tr, tc) = move
        
        # Make move
        captured = board[tr][tc]
        board[tr][tc] = board[fr][fc]
        board[fr][fc] = None
        
        # Evaluate position
        move_value = minimax(board, search_depth - 1, -math.inf, math.inf, False, color)
        
        # Undo move
        board[fr][fc] = board[tr][tc]
        board[tr][tc] = captured
        
        if move_value > best_value:
            best_value = move_value
            best_move = move
    
    # Fallback: return first legal move if something went wrong
    if best_move is None and legal_moves:
        best_move = legal_moves[0]
    
    return best_move
