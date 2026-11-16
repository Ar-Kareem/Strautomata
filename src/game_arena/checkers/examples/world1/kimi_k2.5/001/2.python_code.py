
def policy(my_men, my_kings, opp_men, opp_kings, color):
    import time
    
    start_time = time.time()
    opp = 'w' if color == 'b' else 'b'
    
    # Board representation: dict of (r,c) -> (owner, is_king)
    board = {}
    for p in my_men:
        board[p] = (color, False)
    for p in my_kings:
        board[p] = (color, True)
    for p in opp_men:
        board[p] = (opp, False)
    for p in opp_kings:
        board[p] = (opp, True)
    
    def opponent(c):
        return 'w' if c == 'b' else 'b'
    
    def get_captures(board, pos, is_king, color):
        """Generate all capture sequences from pos. Returns list of (end, captured_list, promoted).
        captured_list contains (pos, (owner, is_king)) for each captured piece."""
        r, c = pos
        drs = [-1, 1] if is_king else ([-1] if color == 'b' else [1])
        results = []
        
        for dr in drs:
            for dc in (-1, 1):
                mid = (r + dr, c + dc)
                end = (r + 2*dr, c + 2*dc)
                if 0 <= end[0] < 8 and 0 <= end[1] < 8:
                    if mid in board and board[mid][0] != color and end not in board:
                        mid_info = board[mid]
                        step_promoted = (not is_king and 
                                       ((color == 'w' and end[0] == 7) or (color == 'b' and end[0] == 0)))
                        
                        # Copy board for recursion
                        new_board = board.copy()
                        del new_board[mid]
                        del new_board[pos]
                        new_board[end] = (color, is_king or step_promoted)
                        
                        sub = get_captures(new_board, end, is_king or step_promoted, color)
                        if sub:
                            for final_end, caps, final_prom in sub:
                                results.append((final_end, [(mid, mid_info)] + caps, final_prom))
                        else:
                            results.append((end, [(mid, mid_info)], step_promoted))
        return results
    
    def get_regular(board, pos, is_king, color):
        """Generate regular moves. Returns list of (end, [], promoted)."""
        r, c = pos
        drs = [-1, 1] if is_king else ([-1] if color == 'b' else [1])
        results = []
        for dr in drs:
            for dc in (-1, 1):
                end = (r + dr, c + dc)
                if 0 <= end[0] < 8 and 0 <= end[1] < 8 and end not in board:
                    promoted = (not is_king and 
                              ((color == 'w' and end[0] == 7) or (color == 'b' and end[0] == 0)))
                    results.append((end, [], promoted))
        return results
    
    def generate_moves(board, color):
        """Generate all legal moves as list of (start, end, captured, promoted)."""
        moves = []
        # Captures are mandatory
        for pos, (owner, is_king) in board.items():
            if owner == color:
                caps = get_captures(board, pos, is_king, color)
                for end, caps_list, promoted in caps:
                    moves.append((pos, end, caps_list, promoted))
        
        if moves:
            # Prefer captures with more pieces
            moves.sort(key=lambda x: -len(x[2]))
            return moves
        
        # Regular moves
        for pos, (owner, is_king) in board.items():
            if owner == color:
                regs = get_regular(board, pos, is_king, color)
                for end, _, promoted in regs:
                    moves.append((pos, end, [], promoted))
        return moves
    
    def evaluate(board, my_color):
        """Evaluate board state from perspective of my_color."""
        score = 0
        for pos, (owner, is_king) in board.items():
            val = 300 if is_king else 100
            if not is_king:
                # Advancement bonus: encourage reaching promotion
                if owner == 'w':
                    val += pos[0] * 5
                else:
                    val += (7 - pos[0]) * 5
            # Center control bonus
            val += (3.5 - abs(pos[1] - 3.5)) * 2
            
            if owner == my_color:
                score += val
            else:
                score -= val
        return score
    
    # Get initial legal moves
    legal = generate_moves(board, color)
    if not legal:
        return ((0,0), (0,0))  # No moves available
    
    best_move = (legal[0][0], legal[0][1])
    
    def alphabeta(board, depth, alpha, beta, current_color):
        """Alpha-beta search with in-place board modifications."""
        if time.time() - start_time > 0.9:
            raise TimeoutError()
        
        if depth == 0:
            return evaluate(board, color), None
        
        moves = generate_moves(board, current_color)
        if not moves:
            # Loss for current player
            val = -100000 if current_color == color else 100000
            return val, None
        
        if current_color == color:
            # Maximize
            max_val = -float('inf')
            best = None
            for start, end, captured, promoted in moves:
                # Apply move
                was_king = board[start][1]
                del board[start]
                saved_captured = []
                for cap_pos, cap_info in captured:
                    saved_captured.append((cap_pos, board.pop(cap_pos)))
                board[end] = (color, was_king or promoted)
                
                score, _ = alphabeta(board, depth-1, alpha, beta, opponent(current_color))
                
                # Undo move
                del board[end]
                board[start] = (color, was_king)
                for cap_pos, cap_info in saved_captured:
                    board[cap_pos] = cap_info
                
                if score > max_val:
                    max_val = score
                    best = (start, end)
                alpha = max(alpha, max_val)
                if alpha >= beta:
                    break
            return max_val, best
        else:
            # Minimize
            min_val = float('inf')
            for start, end, captured, promoted in moves:
                was_king = board[start][1]
                del board[start]
                saved_captured = []
                for cap_pos, cap_info in captured:
                    saved_captured.append((cap_pos, board.pop(cap_pos)))
                board[end] = (current_color, was_king or promoted)
                
                score, _ = alphabeta(board, depth-1, alpha, beta, opponent(current_color))
                
                del board[end]
                board[start] = (current_color, was_king)
                for cap_pos, cap_info in saved_captured:
                    board[cap_pos] = cap_info
                
                if score < min_val:
                    min_val = score
                beta = min(beta, min_val)
                if alpha >= beta:
                    break
            return min_val, None
    
    # Iterative deepening
    depth = 1
    try:
        while depth <= 20:
            val, move = alphabeta(board, depth, -float('inf'), float('inf'), color)
            if move:
                best_move = move
            depth += 1
    except TimeoutError:
        pass
    
    return best_move
