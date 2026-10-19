
def policy(state: list[list[object]], role: str) -> str:
    # Parse state into board dictionary: (row, col) -> mark
    board = {}
    for prop in state:
        if prop[0] == "cell":
            r, c, m = str(prop[1]), str(prop[2]), str(prop[3])
            board[(r, c)] = m
    
    # Find legal moves (blank cells)
    legal_moves = []
    for r in ['1', '2', '3']:
        for c in ['1', '2', '3']:
            if board.get((r, c)) == 'b':
                legal_moves.append((r, c))
    
    if not legal_moves:
        return "mark(1,1)"  # Fallback (should not occur during play)
    
    opponent = 'o' if role == 'x' else 'x'
    
    # All winning lines
    lines = [
        [('1','1'),('1','2'),('1','3')],
        [('2','1'),('2','2'),('2','3')],
        [('3','1'),('3','2'),('3','3')],
        [('1','1'),('2','1'),('3','1')],
        [('1','2'),('2','2'),('3','2')],
        [('1','3'),('2','3'),('3','3')],
        [('1','1'),('2','2'),('3','3')],
        [('1','3'),('2','2'),('3','1')]
    ]
    
    def check_winner(b):
        """Return winner ('x' or 'o') or None"""
        for line in lines:
            vals = [b.get(pos) for pos in line]
            if vals[0] != 'b' and vals[0] == vals[1] == vals[2]:
                return vals[0]
        return None
    
    # 1. Check for immediate win
    for r, c in legal_moves:
        board[(r, c)] = role
        if check_winner(board) == role:
            return f"mark({r},{c})"
        board[(r, c)] = 'b'
    
    # 2. Check for immediate block (opponent win next turn)
    for r, c in legal_moves:
        board[(r, c)] = opponent
        if check_winner(board) == opponent:
            board[(r, c)] = 'b'
            return f"mark({r},{c})"
        board[(r, c)] = 'b'
    
    # 3. Minimax with alpha-beta pruning for optimal play
    def minimax(b, player, alpha, beta, depth):
        winner = check_winner(b)
        if winner == role:
            return 10 - depth
        if winner == opponent:
            return depth - 10
        
        # Check for draw (no blanks)
        has_blank = any(b.get((r,c)) == 'b' for r in ['1','2','3'] for c in ['1','2','3'])
        if not has_blank:
            return 0
        
        if player == role:
            max_eval = -float('inf')
            for r in ['1','2','3']:
                for c in ['1','2','3']:
                    if b.get((r,c)) == 'b':
                        b[(r,c)] = player
                        eval_score = minimax(b, opponent, alpha, beta, depth + 1)
                        b[(r,c)] = 'b'
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r in ['1','2','3']:
                for c in ['1','2','3']:
                    if b.get((r,c)) == 'b':
                        b[(r,c)] = player
                        eval_score = minimax(b, role, alpha, beta, depth + 1)
                        b[(r,c)] = 'b'
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return min_eval
    
    # Select best move using minimax
    best_move = legal_moves[0]
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    for r, c in legal_moves:
        board[(r,c)] = role
        score = minimax(board, opponent, alpha, beta, 0)
        board[(r,c)] = 'b'
        if score > best_score:
            best_score = score
            best_move = (r, c)
            alpha = max(alpha, score)
    
    return f"mark({best_move[0]},{best_move[1]})"
