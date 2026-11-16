
import numpy as np

MY_PIECE = 1
OPP_PIECE = -1
EMPTY = 0

def count_groups(board, player):
    """
    Counts the number of connected components for the given player.
    Connectivity is checked in 8 directions (horizontal, vertical, diagonal).
    """
    visited = np.zeros((8, 8), dtype=bool)
    groups = 0
    for r in range(8):
        for c in range(8):
            if board[r, c] == player and not visited[r, c]:
                groups += 1
                stack = [(r, c)]
                visited[r, c] = True
                while stack:
                    cr, cc = stack.pop()
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0: continue
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < 8 and 0 <= nc < 8 and not visited[nr, nc] and board[nr, nc] == player:
                                visited[nr, nc] = True
                                stack.append((nr, nc))
    return groups

def get_line_count(board, r, c, dr, dc):
    """
    Counts the total number of pieces in the line defined by direction (dr, dc)
    passing through (r, c). The count includes the piece at (r, c).
    """
    count = 0
    # Forward
    curr_r, curr_c = r + dr, c + dc
    while 0 <= curr_r < 8 and 0 <= curr_c < 8:
        if board[curr_r, curr_c] != EMPTY:
            count += 1
        curr_r += dr
        curr_c += dc
    # Backward
    curr_r, curr_c = r - dr, c - dc
    while 0 <= curr_r < 8 and 0 <= curr_c < 8:
        if board[curr_r, curr_c] != EMPTY:
            count += 1
        curr_r -= dr
        curr_c -= dc
    return count + 1  # Include self

def get_legal_moves(board, player):
    """
    Generates all legal moves for the given player.
    """
    moves = []
    pieces = np.argwhere(board == player)
    opponent = -player
    
    for r, c in pieces:
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                
                dist = get_line_count(board, r, c, dr, dc)
                tr, tc = r + dist * dr, c + dist * dc
                
                if not (0 <= tr < 8 and 0 <= tc < 8):
                    continue
                
                legal = True
                curr_r, curr_c = r + dr, c + dc
                
                # Check path and landing
                for step in range(1, dist + 1):
                    if step == dist:
                        # Landing square
                        if board[tr, tc] == player:
                            legal = False # Cannot land on own piece
                            break
                    else:
                        # Intermediate square
                        if board[curr_r, curr_c] == opponent:
                            legal = False # Cannot jump over opponent
                            break
                    
                    curr_r += dr
                    curr_c += dc
                
                if legal:
                    moves.append((r, c, tr, tc))
    return moves

def evaluate(board):
    """
    Evaluates the board state from the perspective of MY_PIECE.
    Higher score is better.
    """
    my_groups = count_groups(board, MY_PIECE)
    opp_groups = count_groups(board, OPP_PIECE)
    
    # Winning conditions
    if my_groups == 1:
        return 100000
    if opp_groups == 1:
        return -100000
        
    my_pieces = np.sum(board == MY_PIECE)
    opp_pieces = np.sum(board == OPP_PIECE)
    
    # Heuristic weights
    # Primary goal: Minimize my groups
    score = (12 - my_groups) * 5000
    # Secondary goal: Disconnect opponent (slightly lower priority)
    score -= (12 - opp_groups) * 1000
    # Material advantage
    score += (my_pieces - opp_pieces) * 50
    
    return score

def apply_move(board, move, player):
    """Returns a new board with the move applied."""
    new_board = board.copy()
    r1, c1, r2, c2 = move
    new_board[r1, c1] = EMPTY
    new_board[r2, c2] = player
    return new_board

def alphabeta(board, depth, alpha, beta, maximizing):
    if depth == 0:
        return evaluate(board)
        
    player = MY_PIECE if maximizing else OPP_PIECE
    moves = get_legal_moves(board, player)
    
    if not moves:
        return evaluate(board)

    if maximizing:
        max_eval = -float('inf')
        for m in moves:
            b = apply_move(board, m, player)
            eval_score = alphabeta(b, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for m in moves:
            b = apply_move(board, m, player)
            eval_score = alphabeta(b, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board_input):
    """
    Main policy function called by the arena.
    """
    board = np.array(board_input, dtype=int)
    moves = get_legal_moves(board, MY_PIECE)
    
    if not moves:
        # Fallback if no moves found (should not happen in standard game flow)
        return "0,0:0,0"

    # Sort moves by 1-ply evaluation to improve Alpha-Beta pruning
    evaluated_moves = []
    for m in moves:
        b = apply_move(board, m, MY_PIECE)
        score = evaluate(b)
        evaluated_moves.append((m, score))
    
    evaluated_moves.sort(key=lambda x: x[1], reverse=True)
    
    # Iterative deepening could be used here, but fixed depth is reliable for 1s limit
    DEPTH = 3
    
    best_move = evaluated_moves[0][0]
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    for m, _ in evaluated_moves:
        b = apply_move(board, m, MY_PIECE)
        score = alphabeta(b, DEPTH - 1, alpha, beta, False)
        if score > best_score:
            best_score = score
            best_move = m
        alpha = max(alpha, score)
        
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
