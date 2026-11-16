
import numpy as np
from typing import List, Tuple, Optional
import time

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Othello policy that uses minimax with alpha-beta pruning.
    
    Args:
        you: 8x8 numpy array representing your discs (1 for disc, 0 for empty)
        opponent: 8x8 numpy array representing opponent's discs (1 for disc, 0 for empty)
    
    Returns:
        A move string like "d3" or "pass" if no legal moves available
    """
    
    # Direction vectors for the 8 possible directions
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    def is_valid_pos(r: int, c: int) -> bool:
        return 0 <= r < 8 and 0 <= c < 8
    
    def get_legal_moves(board_you: np.ndarray, board_opponent: np.ndarray) -> List[Tuple[int, int]]:
        """Get all legal moves for the current player."""
        legal_moves = []
        
        for r in range(8):
            for c in range(8):
                if board_you[r][c] == 0 and board_opponent[r][c] == 0:
                    # Check if this is a legal move
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        if is_valid_pos(nr, nc) and board_opponent[nr][nc] == 1:
                            # Found opponent disc, check if it leads to our disc
                            while is_valid_pos(nr, nc) and board_opponent[nr][nc] == 1:
                                nr += dr
                                nc += dc
                            if is_valid_pos(nr, nc) and board_you[nr][nc] == 1:
                                legal_moves.append((r, c))
                                break
                                
        return legal_moves
    
    def make_move(board_you: np.ndarray, board_opponent: np.ndarray, 
                  r: int, c: int) -> Tuple[np.ndarray, np.ndarray]:
        """Make a move and return new board states."""
        new_you = board_you.copy()
        new_opponent = board_opponent.copy()
        
        new_you[r][c] = 1
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            discs_to_flip = []
            
            while is_valid_pos(nr, nc) and new_opponent[nr][nc] == 1:
                discs_to_flip.append((nr, nc))
                nr += dr
                nc += dc
                
            if is_valid_pos(nr, nc) and new_you[nr][nc] == 1:
                # Flip all discs
                for fr, fc in discs_to_flip:
                    new_opponent[fr][fc] = 0
                    new_you[fr][fc] = 1
        
        return new_you, new_opponent
    
    def evaluate(board_you: np.ndarray, board_opponent: np.ndarray) -> float:
        """Evaluate board position using heuristic."""
        score = 0.0
        
        # Corner weights (highest priority)
        corners = [(0,0), (0,7), (7,0), (7,7)]
        corner_weight = 1000
        
        for r, c in corners:
            if board_you[r][c] == 1:
                score += corner_weight
            elif board_opponent[r][c] == 1:
                score -= corner_weight
        
        # Edge weights (second highest priority)
        edge_weight = 100
        for r in range(8):
            for c in range(8):
                if (r == 0 or r == 7 or c == 0 or c == 7):
                    if r not in [0, 7] and c not in [0, 7]:
                        continue
                    if board_you[r][c] == 1:
                        score += edge_weight
                    elif board_opponent[r][c] == 1:
                        score -= edge_weight
        
        # Mobility (number of legal moves)
        you_moves = len(get_legal_moves(board_you, board_opponent))
        opp_moves = len(get_legal_moves(board_opponent, board_you))
        
        if you_moves + opp_moves > 0:
            score += 10 * (you_moves - opp_moves)
        
        # Disc count
        you_count = np.sum(board_you)
        opp_count = np.sum(board_opponent)
        
        # Late game - prioritize disc count more
        total_discs = you_count + opp_count
        if total_discs > 50:
            score += (you_count - opp_count) * 5
        
        return score
    
    def minimax(board_you: np.ndarray, board_opponent: np.ndarray, 
                depth: int, alpha: float, beta: float, 
                maximizing: bool, start_time: float, time_limit: float) -> float:
        """Minimax with alpha-beta pruning."""
        
        # Time check
        if time.time() - start_time > time_limit:
            return evaluate(board_you, board_opponent)
        
        if depth == 0:
            return evaluate(board_you, board_opponent)
        
        if maximizing:
            max_eval = float('-inf')
            legal_moves = get_legal_moves(board_you, board_opponent)
            
            if not legal_moves:
                # Pass move
                return minimax(board_opponent, board_you, depth-1, alpha, beta, False, start_time, time_limit)
            
            # Sort moves by potential value (corners first, then edges)
            legal_moves.sort(key=lambda pos: (
                pos in [(0,0), (0,7), (7,0), (7,7)],  # corners first
                pos[0] in [0, 7] or pos[1] in [0, 7],  # edges second
            ), reverse=True)
            
            for r, c in legal_moves[:15]:  # Limit branching factor
                new_you, new_opponent = make_move(board_you, board_opponent, r, c)
                eval_score = minimax(new_opponent, new_you, depth-1, alpha, beta, False, start_time, time_limit)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            legal_moves = get_legal_moves(board_opponent, board_you)
            
            if not legal_moves:
                # Pass move
                return minimax(board_you, board_opponent, depth-1, alpha, beta, True, start_time, time_limit)
            
            legal_moves.sort(key=lambda pos: (
                pos in [(0,0), (0,7), (7,0), (7,7)],
                pos[0] in [0, 7] or pos[1] in [0, 7],
            ), reverse=True)
            
            for r, c in legal_moves[:15]:
                new_opponent, new_you = make_move(board_opponent, board_you, r, c)
                eval_score = minimax(new_you, new_opponent, depth-1, alpha, beta, True, start_time, time_limit)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def get_best_move() -> Optional[Tuple[int, int]]:
        """Get the best move using minimax."""
        legal_moves = get_legal_moves(you, opponent)
        
        if not legal_moves:
            return None
        
        # Time limit based on game phase
        total_discs = np.sum(you) + np.sum(opponent)
        if total_discs < 30:
            time_limit = 0.8  # Early game: 0.8 seconds
            depth = 4
        elif total_discs < 55:
            time_limit = 0.9  # Mid game: 0.9 seconds  
            depth = 5
        else:
            time_limit = 1.0  # End game: 1.0 seconds
            depth = 6
        
        start_time = time.time()
        
        best_move = None
        best_value = float('-inf')
        
        # Sort moves to try best ones first
        legal_moves.sort(key=lambda pos: (
            pos in [(0,0), (0,7), (7,0), (7,7)],  # corners first
            pos[0] in [0, 7] or pos[1] in [0, 7],  # edges second
        ), reverse=True)
        
        for r, c in legal_moves:
            new_you, new_opponent = make_move(you, opponent, r, c)
            move_value = minimax(new_opponent, new_you, depth-1, float('-inf'), float('inf'), False, start_time, time_limit)
            
            if move_value > best_value:
                best_value = move_value
                best_move = (r, c)
            
            # Break if time is running out
            if time.time() - start_time > time_limit * 0.95:
                break
        
        return best_move
    
    # Get the best move
    best_move = get_best_move()
    
    if best_move is None:
        return "pass"
    
    r, c = best_move
    # Convert to algebraic notation
    col_letter = chr(ord('a') + c)
    row_number = str(r + 1)
    
    return col_letter + row_number
