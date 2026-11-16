
def policy(state: list[list[object]], role: str) -> str:
    # Parse state to get piece positions
    cells = {}
    for prop in state:
        if prop[0] == 'cell':
            cells[(prop[1], prop[2])] = prop[3]
    
    opponent = 'black' if role == 'white' else 'white'
    
    def col_to_idx(c):
        return ord(c) - ord('a')
    
    def idx_to_col(i):
        return chr(ord('a') + i)
    
    def get_legal_moves(color, board):
        moves = []
        for (col, row_str), piece_color in board.items():
            if piece_color != color:
                continue
            
            col_idx = col_to_idx(col)
            row = int(row_str)
            
            if color == 'white':
                deltas = [(1, 2), (-1, 2), (2, 1), (-2, 1)]
            else:
                deltas = [(1, -2), (-1, -2), (2, -1), (-2, -1)]
            
            for dc, dr in deltas:
                new_col_idx = col_idx + dc
                new_row = row + dr
                
                if not (0 <= new_col_idx < 6 and 1 <= new_row <= 6):
                    continue
                
                new_col = idx_to_col(new_col_idx)
                new_row_str = str(new_row)
                target = (new_col, new_row_str)
                
                is_capture = target in board and board[target] != color
                is_winning = (color == 'white' and new_row == 6) or (color == 'black' and new_row == 1)
                
                if target not in board or is_capture:
                    moves.append((col, row_str, new_col, new_row_str, is_capture, is_winning))
        
        return moves
    
    def make_move(board, move):
        new_board = dict(board)
        from_col, from_row, to_col, to_row, _, _ = move
        color = new_board[(from_col, from_row)]
        del new_board[(from_col, from_row)]
        new_board[(to_col, to_row)] = color
        return new_board
    
    def evaluate(board, my_color):
        score = 0
        for (col, row_str), piece_color in board.items():
            row = int(row_str)
            
            if my_color == 'white':
                advancement = row
            else:
                advancement = 7 - row
            
            value = advancement * 10
            
            if advancement >= 4:
                value += 30
            if advancement >= 5:
                value += 60
            
            if piece_color == my_color:
                score += value
            else:
                score -= value
        
        return score
    
    def minimax(board, depth, alpha, beta, is_maximizing):
        current_color = role if is_maximizing else opponent
        
        moves = get_legal_moves(current_color, board)
        
        if not moves:
            return evaluate(board, role), None
        
        for move in moves:
            if move[5]:
                return (10000 if is_maximizing else -10000), move
        
        if depth == 0:
            return evaluate(board, role), None
        
        def sort_key(m):
            key = 0
            if m[5]:
                key += 10000
            if m[4]:
                key += 100
            row = int(m[3])
            key += row if current_color == 'white' else 7 - row
            return key
        
        moves.sort(key=sort_key, reverse=True)
        
        best_move = moves[0]
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in moves:
                new_board = make_move(board, move)
                eval_score, _ = minimax(new_board, depth - 1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves:
                new_board = make_move(board, move)
                eval_score, _ = minimax(new_board, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    legal_moves = get_legal_moves(role, cells)
    
    if not legal_moves:
        return "noop"
    
    for move in legal_moves:
        if move[5]:
            return f"move({move[0]},{move[1]},{move[2]},{move[3]})"
    
    _, best_move = minimax(cells, 3, float('-inf'), float('inf'), True)
    
    if best_move:
        return f"move({best_move[0]},{best_move[1]},{best_move[2]},{best_move[3]})"
    
    return f"move({legal_moves[0][0]},{legal_moves[0][1]},{legal_moves[0][2]},{legal_moves[0][3]})"
