
import time
from typing import List

def policy(board: List[List[int]]) -> int:
    """Main policy function that selects the best move."""
    start_time = time.time()
    MAX_TIME = 0.95  # Leave some buffer
    
    # Convert to numpy for faster operations if available
    try:
        import numpy as np
        board_arr = np.array(board)
        use_numpy = True
    except ImportError:
        board_arr = board
        use_numpy = False
    
    # Get valid moves
    valid_moves = _get_valid_moves(board_arr, use_numpy)
    if not valid_moves:
        return 3  # Should never happen, but fallback
    
    # 1. Check for immediate win
    for col in valid_moves:
        if _check_immediate_win(board_arr, col, 1, use_numpy):
            return col
    
    # 2. Check for immediate block
    for col in valid_moves:
        if _check_immediate_win(board_arr, col, -1, use_numpy):
            return col
    
    # 3. Iterative deepening minimax
    best_move = valid_moves[len(valid_moves)//2]  # Start with center-ish move
    depth = 1
    best_score = float('-inf')
    
    while time.time() - start_time < MAX_TIME and depth <= 7:
        try:
            current_best_move = None
            current_best_score = float('-inf')
            
            # Sort moves by heuristic for better alpha-beta
            ordered_moves = _order_moves(board_arr, valid_moves, use_numpy)
            
            for col in ordered_moves:
                row = _get_next_open_row(board_arr, col, use_numpy)
                if row is None:
                    continue
                
                # Make move
                temp_board = _copy_board(board_arr, use_numpy)
                _make_move(temp_board, row, col, 1, use_numpy)
                
                # Minimax
                score = _minimax(temp_board, depth-1, float('-inf'), float('inf'), False, use_numpy)
                
                if score > current_best_score:
                    current_best_score = score
                    current_best_move = col
            
            if current_best_move is not None:
                best_move = current_best_move
                best_score = current_best_score
            
            depth += 1
            
        except Exception:
            # If anything fails, break and return last best move
            break
    
    return best_move if best_move in valid_moves else valid_moves[len(valid_moves)//2]

def _get_valid_moves(board, use_numpy: bool) -> List[int]:
    """Return list of columns that are not full."""
    valid = []
    for col in range(7):
        if use_numpy:
            if board[0, col] == 0:
                valid.append(col)
        else:
            if board[0][col] == 0:
                valid.append(col)
    return valid

def _get_next_open_row(board, col: int, use_numpy: bool):
    """Get the next open row in a column."""
    if use_numpy:
        for row in range(5, -1, -1):
            if board[row, col] == 0:
                return row
    else:
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                return row
    return None

def _make_move(board, row: int, col: int, player: int, use_numpy: bool):
    """Place a piece on the board."""
    if use_numpy:
        board[row, col] = player
    else:
        board[row][col] = player

def _copy_board(board, use_numpy: bool):
    """Create a copy of the board."""
    if use_numpy:
        return board.copy()
    else:
        return [row[:] for row in board]

def _check_immediate_win(board, col: int, player: int, use_numpy: bool) -> bool:
    """Check if placing a piece in col results in a win."""
    row = _get_next_open_row(board, col, use_numpy)
    if row is None:
        return False
    
    temp_board = _copy_board(board, use_numpy)
    _make_move(temp_board, row, col, player, use_numpy)
    return _is_win(temp_board, player, use_numpy)

def _is_win(board, player: int, use_numpy: bool) -> bool:
    """Check if player has won."""
    if use_numpy:
        import numpy as np
        
        # Horizontal
        for c in range(4):
            for r in range(6):
                if all(board[r, c:c+4] == player):
                    return True
        
        # Vertical
        for c in range(7):
            for r in range(3):
                if all(board[r:r+4, c] == player):
                    return True
        
        # Diagonal positive slope
        for c in range(4):
            for r in range(3):
                if board[r, c] == player and board[r+1, c+1] == player and \
                   board[r+2, c+2] == player and board[r+3, c+3] == player:
                    return True
        
        # Diagonal negative slope
        for c in range(4):
            for r in range(3, 6):
                if board[r, c] == player and board[r-1, c+1] == player and \
                   board[r-2, c+2] == player and board[r-3, c+3] == player:
                    return True
    else:
        # Horizontal
        for c in range(4):
            for r in range(6):
                if (board[r][c] == player and board[r][c+1] == player and
                    board[r][c+2] == player and board[r][c+3] == player):
                    return True
        
        # Vertical
        for c in range(7):
            for r in range(3):
                if (board[r][c] == player and board[r+1][c] == player and
                    board[r+2][c] == player and board[r+3][c] == player):
                    return True
        
        # Diagonal positive
        for c in range(4):
            for r in range(3):
                if (board[r][c] == player and board[r+1][c+1] == player and
                    board[r+2][c+2] == player and board[r+3][c+3] == player):
                    return True
        
        # Diagonal negative
        for c in range(4):
            for r in range(3, 6):
                if (board[r][c] == player and board[r-1][c+1] == player and
                    board[r-2][c+2] == player and board[r-3][c+3] == player):
                    return True
    
    return False

def _order_moves(board, moves: List[int], use_numpy: bool) -> List[int]:
    """Order moves by heuristic value for better alpha-beta pruning."""
    move_scores = []
    for col in moves:
        score = _heuristic_score_of_col(board, col, use_numpy)
        move_scores.append((score, col))
    
    # Sort by score descending
    move_scores.sort(reverse=True)
    return [col for score, col in move_scores]

def _heuristic_score_of_col(board, col: int, use_numpy: bool) -> int:
    """Quick heuristic score for a column."""
    board_copy = _copy_board(board, use_numpy)
    row = _get_next_open_row(board_copy, col, use_numpy)
    if row is None:
        return -1000000
    
    _make_move(board_copy, row, col, 1, use_numpy)
    
    # Bonus for center
    center_bonus = 10 - abs(col - 3) * 2
    
    # Check for 3 in a row threats
    threat_score = 0
    if _count_pattern(board_copy, 1, 3, use_numpy) > 0:
        threat_score += 50
    
    return center_bonus + threat_score

def _count_pattern(board, player: int, length: int, use_numpy: bool) -> int:
    """Count patterns of given length for a player."""
    count = 0
    # Horizontal
    for c in range(7-length):
        for r in range(6):
            pattern = True
            for i in range(length):
                if use_numpy:
                    if board[r, c+i] != player:
                        pattern = False
                        break
                else:
                    if board[r][c+i] != player:
                        pattern = False
                        break
            if pattern:
                count += 1
    
    # Vertical
    for c in range(7):
        for r in range(6-length):
            pattern = True
            for i in range(length):
                if use_numpy:
                    if board[r+i, c] != player:
                        pattern = False
                        break
                else:
                    if board[r+i][c] != player:
                        pattern = False
                        break
            if pattern:
                count += 1
    
    # Diagonal positive
    for c in range(7-length):
        for r in range(6-length):
            pattern = True
            for i in range(length):
                if use_numpy:
                    if board[r+i, c+i] != player:
                        pattern = False
                        break
                else:
                    if board[r+i][c+i] != player:
                        pattern = False
                        break
            if pattern:
                count += 1
    
    # Diagonal negative
    for c in range(7-length):
        for r in range(length-1, 6):
            pattern = True
            for i in range(length):
                if use_numpy:
                    if board[r-i, c+i] != player:
                        pattern = False
                        break
                else:
                    if board[r-i][c+i] != player:
                        pattern = False
                        break
            if pattern:
                count += 1
    
    return count

def _evaluate_position(board, use_numpy: bool) -> int:
    """Static evaluation of board position for AI player."""
    if _is_win(board, 1, use_numpy):
        return 1000000
    if _is_win(board, -1, use_numpy):
        return -1000000
    
    score = 0
    
    # Center control - major strategic advantage
    center_count = 0
    if use_numpy:
        center_arr = board[:, 3]
        center_count = np.sum(center_arr == 1) - np.sum(center_arr == -1)
    else:
        for row in range(6):
            if board[row][3] == 1:
                center_count += 1
            elif board[row][3] == -1:
                center_count -= 1
    score += center_count * 30
    
    # Count 3-in-a-rows (threats)
    ai_threats = _count_pattern(board, 1, 3, use_numpy)
    opp_threats = _count_pattern(board, -1, 3, use_numpy)
    score += ai_threats * 50
    score -= opp_threats * 60  # Slightly higher penalty for opponent threats
    
    # Count 2-in-a-rows (potential)
    ai_potential = _count_pattern(board, 1, 2, use_numpy)
    opp_potential = _count_pattern(board, -1, 2, use_numpy)
    score += ai_potential * 10
    score -= opp_potential * 12
    
    return score

def _minimax(board, depth: int, alpha: float, beta: float, maximizing: bool, use_numpy: bool):
    """Minimax with alpha-beta pruning."""
    if depth == 0:
        return _evaluate_position(board, use_numpy)
    
    valid_moves = _get_valid_moves(board, use_numpy)
    if not valid_moves:
        return 0  # Draw
    
    if maximizing:
        max_eval = float('-inf')
        for col in valid_moves:
            row = _get_next_open_row(board, col, use_numpy)
            if row is None:
                continue
            
            temp_board = _copy_board(board, use_numpy)
            _make_move(temp_board, row, col, 1, use_numpy)
            
            # Check for immediate win
            if _is_win(temp_board, 1, use_numpy):
                return 1000000
            
            eval = _minimax(temp_board, depth-1, alpha, beta, False, use_numpy)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for col in valid_moves:
            row = _get_next_open_row(board, col, use_numpy)
            if row is None:
                continue
            
            temp_board = _copy_board(board, use_numpy)
            _make_move(temp_board, row, col, -1, use_numpy)
            
            # Check for opponent win
            if _is_win(temp_board, -1, use_numpy):
                return -1000000
            
            eval = _minimax(temp_board, depth-1, alpha, beta, True, use_numpy)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval
