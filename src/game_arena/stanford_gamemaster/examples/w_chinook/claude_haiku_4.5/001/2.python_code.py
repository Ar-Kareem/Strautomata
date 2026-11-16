
def policy(state: list[list[object]], role: str) -> str:
    # Extract board state
    board = {}
    for fact in state:
        if fact[0] == "cell":
            col, row, piece_type = fact[1], int(fact[2]), fact[3]
            board[(col, row)] = piece_type
    
    # Column ordering for wrapping
    cols = ['a', 'b', 'c', 'd']
    col_idx = {c: i for i, c in enumerate(cols)}
    rows = list(range(1, 9))
    
    def normalize_col(c):
        """Wrap column around the board"""
        idx = col_idx[c] % 4
        return cols[idx]
    
    def normalize_row(r):
        """Wrap row around the board"""
        return ((r - 1) % 8) + 1
    
    def get_direction(piece_type):
        """Return movement direction: (col_delta, row_delta) for this piece"""
        if piece_type == "red":
            return [(1, 1), (-1, 1)]  # diagonally forward (wrapping)
        else:  # blue
            return [(1, -1), (-1, -1)]  # diagonally forward (wrapping)
    
    def find_moves():
        """Generate all legal moves for current role"""
        moves = []
        
        # Find all pieces of current role
        pieces = [(c, r) for (c, r), p in board.items() if p == role]
        
        for col, row in pieces:
            # Try regular moves
            for dcol, drow in get_direction(role):
                new_col_idx = (col_idx[col] + dcol) % 4
                new_col = cols[new_col_idx]
                new_row = normalize_row(row + drow)
                
                if (new_col, new_row) not in board:
                    moves.append({
                        'type': 'move',
                        'from': (col, row),
                        'to': (new_col, new_row),
                        'action': f"move({col},{row},{new_col},{new_row})",
                        'score': compute_move_score((col, row), (new_col, new_row), role)
                    })
            
            # Try jumps (must jump over own pieces only)
            for dcol, drow in get_direction(role):
                mid_col_idx = (col_idx[col] + dcol) % 4
                mid_col = cols[mid_col_idx]
                mid_row = normalize_row(row + drow)
                
                # Check if there's a piece to jump over (own piece)
                if (mid_col, mid_row) in board and board[(mid_col, mid_row)] == role:
                    # Continue in same direction
                    end_col_idx = (mid_col_idx + dcol) % 4
                    end_col = cols[end_col_idx]
                    end_row = normalize_row(mid_row + drow)
                    
                    if (end_col, end_row) not in board:
                        moves.append({
                            'type': 'jump',
                            'from': (col, row),
                            'to': (end_col, end_row),
                            'action': f"jump({col},{row},{mid_col},{mid_row},{end_col},{end_row})",
                            'score': compute_move_score((col, row), (end_col, end_row), role) + 10
                        })
        
        return moves
    
    def compute_move_score(from_pos, to_pos, piece_role):
        """Score a move: prioritize advancement toward target zone"""
        _, from_row = from_pos
        _, to_row = to_pos
        
        if piece_role == "red":
            # Red targets rows 6-8
            target_bonus = 0
            if to_row in [6, 7, 8]:
                target_bonus = 100
            return to_row - from_row + target_bonus
        else:
            # Blue targets rows 1-3
            target_bonus = 0
            if to_row in [1, 2, 3]:
                target_bonus = 100
            return from_row - to_row + target_bonus
    
    moves = find_moves()
    
    if not moves:
        # No moves found - shouldn't happen in valid game state
        return "pass"
    
    # Sort by score (descending) and return best move
    best_move = max(moves, key=lambda m: m['score'])
    return best_move['action']
