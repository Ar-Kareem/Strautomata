
import time
from collections import deque
import numpy as np

def policy(board):
    """
    Returns the next move in format "row,col:row,col"
    """
    start_time = time.time()
    
    # Ensure board is list of lists for fast indexing
    if isinstance(board, np.ndarray):
        board = board.tolist()
    
    # Iterative deepening search
    best_move = None
    max_depth = 4
    
    for depth in range(1, max_depth + 1):
        if time.time() - start_time > 0.85:
            break
        try:
            score, move = alpha_beta_search(board, depth, 1, -float('inf'), float('inf'), start_time)
            if move is not None:
                best_move = move
        except TimeoutError:
            break
    
    # Fallback: if search didn't finish depth 1, pick first legal move
    if best_move is None:
        moves = generate_moves(board, 1)
        if moves:
            best_move = moves[0]
        else:
            # Should not happen in a valid game, but return a dummy to avoid crash
            return "0,0:0,0"
    
    (r1, c1), (r2, c2) = best_move
    return f"{r1},{c1}:{r2},{c2}"

def alpha_beta_search(board, depth, player, alpha, beta, start_time):
    """Alpha-beta search with timeout check"""
    if time.time() - start_time > 0.95:
        raise TimeoutError
    
    # Check terminal states (win/loss)
    my_comp = count_components(board, player)
    if my_comp == 1:
        return (10000 if player == 1 else -10000), None
    
    opp_comp = count_components(board, -player)
    if opp_comp == 1:
        return (-10000 if player == 1 else 10000), None
    
    if depth == 0:
        return evaluate_board(board), None
    
    moves = generate_moves(board, player)
    
    if not moves:
        # No legal moves is a loss
        return (-10000 if player == 1 else 10000), None
    
    # Move ordering: captures first (likely good moves)
    moves.sort(key=lambda m: 1 if board[m[1][0]][m[1][1]] == -player else 0, reverse=True)
    
    best_move = moves[0]
    
    if player == 1:
        max_eval = -float('inf')
        for move in moves:
            new_board = make_move(board, move, 1)
            eval_score, _ = alpha_beta_search(new_board, depth - 1, -1, alpha, beta, start_time)
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            
            alpha = max(alpha, eval_score)
            if alpha >= beta:
                break
        
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            new_board = make_move(board, move, -1)
            eval_score, _ = alpha_beta_search(new_board, depth - 1, 1, alpha, beta, start_time)
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        
        return min_eval, best_move

def make_move(board, move, player):
    """Execute move on board copy"""
    (r1, c1), (r2, c2) = move
    new_board = [row[:] for row in board]
    new_board[r1][c1] = 0
    new_board[r2][c2] = player
    return new_board

def count_components(board, player):
    """Count connected components using 8-connectivity"""
    visited = [[False] * 8 for _ in range(8)]
    count = 0
    
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and not visited[r][c]:
                count += 1
                # BFS
                queue = deque([(r, c)])
                visited[r][c] = True
                while queue:
                    cr, cc = queue.popleft()
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < 8 and 0 <= nc < 8 and not visited[nr][nc] and board[nr][nc] == player:
                                visited[nr][nc] = True
                                queue.append((nr, nc))
    return count

def generate_moves(board, player):
    """Generate all legal moves for player"""
    moves = []
    opponent = -player
    
    for r in range(8):
        for c in range(8):
            if board[r][c] != player:
                continue
            
            # Check all 8 directions
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                # Count pieces in the line of movement
                if dr == 0:  # Horizontal
                    count = sum(1 for cc in range(8) if board[r][cc] != 0)
                elif dc == 0:  # Vertical
                    count = sum(1 for rr in range(8) if board[rr][c] != 0)
                elif dr == dc:  # Main diagonal (r-c constant)
                    diff = r - c
                    count = sum(1 for rr in range(8) for cc in range(8) if rr - cc == diff and board[rr][cc] != 0)
                else:  # Anti-diagonal (r+c constant)
                    s = r + c
                    count = sum(1 for rr in range(8) for cc in range(8) if rr + cc == s and board[rr][cc] != 0)
                
                if count == 0:
                    continue
                
                nr = r + dr * count
                nc = c + dc * count
                
                # Check bounds
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    continue
                
                # Cannot land on own piece
                if board[nr][nc] == player:
                    continue
                
                # Check path for enemy pieces (cannot jump over them)
                valid = True
                for k in range(1, count):
                    cr = r + dr * k
                    cc = c + dc * k
                    if board[cr][cc] == opponent:
                        valid = False
                        break
                
                if valid:
                    moves.append(((r, c), (nr, nc)))
    
    return moves

def evaluate_board(board):
    """
    Evaluate from perspective of player 1.
    Higher is better for player 1.
    """
    # Check win/loss
    my_comp = count_components(board, 1)
    if my_comp == 1:
        return 10000
    
    opp_comp = count_components(board, -1)
    if opp_comp == 1:
        return -10000
    
    score = 0
    
    # Component difference (fewer components is better)
    score += (opp_comp - my_comp) * 100
    
    # Material and position analysis
    my_pieces = []
    opp_pieces = []
    
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1:
                my_pieces.append((r, c))
            elif board[r][c] == -1:
                opp_pieces.append((r, c))
    
    # Material balance
    score += (len(my_pieces) - len(opp_pieces)) * 10
    
    # Compactness for player 1 (smaller spread is better)
    if len(my_pieces) > 0:
        min_r = min(r for r, c in my_pieces)
        max_r = max(r for r, c in my_pieces)
        min_c = min(c for r, c in my_pieces)
        max_c = max(c for r, c in my_pieces)
        spread = (max_r - min_r) + (max_c - min_c)
        score -= spread * 5
    
    return score
