
import numpy as np
import itertools

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Static board weights (8x8)
    WEIGHTS = np.array([
        [100, -20, 10,  5,  5, 10, -20, 100],
        [-20, -50, -2, -2, -2, -2, -50, -20],
        [ 10,  -2,  0,  0,  0,  0,  -2,  10],
        [  5,  -2,  0,  0,  0,  0,  -2,   5],
        [  5,  -2,  0,  0,  0,  0,  -2,   5],
        [ 10,  -2,  0,  0,  0,  0,  -2,  10],
        [-20, -50, -2, -2, -2, -2, -50, -20],
        [100, -20, 10,  5,  5, 10, -20, 100]
    ])
    
    DIRECTIONS = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
    
    def get_legal_moves(board_you, board_opp):
        moves = []
        for r in range(8):
            for c in range(8):
                if board_you[r,c] == 0 and board_opp[r,c] == 0:
                    for dr, dc in DIRECTIONS:
                        nr, nc = r + dr, c + dc
                        if nr < 0 or nr >= 8 or nc < 0 or nc >= 8:
                            continue
                        if board_opp[nr,nc] == 1:
                            while 0 <= nr < 8 and 0 <= nc < 8:
                                if board_you[nr,nc] == 1:
                                    moves.append((r,c))
                                    break
                                if board_opp[nr,nc] == 0 and board_you[nr,nc] == 0:
                                    break
                                nr += dr
                                nc += dc
                            if moves and moves[-1] == (r,c):
                                break
        return list(set(moves))
    
    def apply_move(board_you, board_opp, move):
        r, c = move
        new_you = board_you.copy()
        new_opp = board_opp.copy()
        new_you[r,c] = 1
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            flips = []
            while 0 <= nr < 8 and 0 <= nc < 8:
                if board_opp[nr,nc] == 1:
                    flips.append((nr,nc))
                elif board_you[nr,nc] == 1:
                    for fr, fc in flips:
                        new_you[fr,fc] = 1
                        new_opp[fr,fc] = 0
                    break
                else:
                    break
                nr += dr
                nc += dc
        return new_you, new_opp
    
    def evaluate(board_you, board_opp, my_turn):
        # Material score
        my_discs = np.sum(board_you)
        opp_discs = np.sum(board_opp)
        total_discs = my_discs + opp_discs
        empty = 64 - total_discs
        
        # Position weights
        pos_score = np.sum(board_you * WEIGHTS) - np.sum(board_opp * WEIGHTS)
        
        # Mobility
        my_moves = len(get_legal_moves(board_you, board_opp))
        opp_moves = len(get_legal_moves(board_opp, board_you))
        mobility = 0
        if my_moves + opp_moves > 0:
            mobility = 20 * (my_moves - opp_moves) / (my_moves + opp_moves)
        
        # Corner control
        corners = [(0,0), (0,7), (7,0), (7,7)]
        corner_score = 0
        for cr, cc in corners:
            if board_you[cr,cc] == 1:
                corner_score += 25
            elif board_opp[cr,cc] == 1:
                corner_score -= 25
        
        # Endgame: maximize disc difference
        if empty < 12:
            disc_diff = my_discs - opp_discs
            return disc_diff * 10 + pos_score + corner_score + mobility
        
        # Midgame: position + mobility
        return pos_score + corner_score * 0.8 + mobility
    
    def alphabeta(board_you, board_opp, depth, alpha, beta, maximizing):
        if depth == 0:
            return evaluate(board_you, board_opp, maximizing), None
        
        moves = get_legal_moves(board_you, board_opp)
        if not moves:
            # Pass
            opp_moves = get_legal_moves(board_opp, board_you)
            if not opp_moves:
                # Terminal
                disc_diff = np.sum(board_you) - np.sum(board_opp)
                return disc_diff * 100, None
            # Only opponent can move
            val, _ = alphabeta(board_opp, board_you, depth-1, -beta, -alpha, not maximizing)
            return -val, None
        
        best_move = moves[0]
        if maximizing:
            value = -float('inf')
            # Move ordering: try corners first
            corners = [(0,0), (0,7), (7,0), (7,7)]
            ordered_moves = []
            for m in moves:
                if m in corners:
                    ordered_moves.insert(0, m)
                else:
                    ordered_moves.append(m)
            
            for move in ordered_moves:
                new_you, new_opp = apply_move(board_you, board_opp, move)
                val, _ = alphabeta(new_opp, new_you, depth-1, alpha, beta, False)
                if val > value:
                    value = val
                    best_move = move
                alpha = max(alpha, value)
                if value >= beta:
                    break
            return value, best_move
        else:
            value = float('inf')
            for move in moves:
                new_you, new_opp = apply_move(board_you, board_opp, move)
                val, _ = alphabeta(new_opp, new_you, depth-1, alpha, beta, True)
                if val < value:
                    value = val
                    best_move = move
                beta = min(beta, value)
                if value <= alpha:
                    break
            return value, best_move
    
    # Get legal moves for current state
    moves = get_legal_moves(you, opponent)
    if not moves:
        return "pass"
    
    # If only one move, return immediately
    if len(moves) == 1:
        r, c = moves[0]
        return f"{chr(c + 97)}{r + 1}"
    
    # Determine search depth based on game stage
    empty = 64 - (np.sum(you) + np.sum(opponent))
    depth = 5 if empty > 20 else 6 if empty > 10 else 8
    
    # Alpha-beta search
    _, best_move = alphabeta(you, opponent, depth, -float('inf'), float('inf'), True)
    
    if best_move is None:
        # Fallback: highest weight move
        best_move = max(moves, key=lambda m: WEIGHTS[m[0], m[1]])
    
    r, c = best_move
    return f"{chr(c + 97)}{r + 1}"
