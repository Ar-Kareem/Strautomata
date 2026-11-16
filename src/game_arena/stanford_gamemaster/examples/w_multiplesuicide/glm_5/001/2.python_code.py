
def policy(state: list[list[object]], role: str) -> str:
    # Parse state to extract board information
    # cell(board_row, board_col, cell_row, cell_col, content)
    
    opponent = 'o' if role == 'x' else 'x'
    
    # Build board representation
    boards = {}  # (br, bc) -> {(cr, cc): content}
    blank_cells = []
    
    for prop in state:
        if prop[0] == 'cell':
            br, bc, cr, cc, content = int(prop[1]), int(prop[2]), int(prop[3]), int(prop[4]), prop[5]
            key = (br, bc)
            if key not in boards:
                boards[key] = {}
            boards[key][(cr, cc)] = content
            if content == 'b':
                blank_cells.append((br, bc, cr, cc))
    
    # All possible winning lines on a 3x3 board
    lines = [
        [(1,1), (1,2), (1,3)],
        [(2,1), (2,2), (2,3)],
        [(3,1), (3,2), (3,3)],
        [(1,1), (2,1), (3,1)],
        [(1,2), (2,2), (3,2)],
        [(1,3), (2,3), (3,3)],
        [(1,1), (2,2), (3,3)],
        [(1,3), (2,2), (3,1)]
    ]
    
    def count_suicide_lines(board_key, pos, player):
        """Count lines that would be completed by placing player's mark at pos"""
        board = boards.get(board_key, {})
        count = 0
        for line in lines:
            if pos in line:
                player_count = sum(1 for p in line if board.get(p, 'b') == player)
                if player_count == 2:  # Would complete a line
                    count += 1
        return count
    
    def get_danger_score(board_key, pos, player):
        """Higher score = more dangerous (creates more line threats)"""
        board = boards.get(board_key, {})
        score = 0
        for line in lines:
            if pos in line:
                my_count = sum(1 for p in line if board.get(p, 'b') == player)
                opp_count = sum(1 for p in line if board.get(p, 'b') != 'b' and board.get(p, 'b') != player)
                blanks = sum(1 for p in line if board.get(p, 'b') == 'b')
                
                if my_count == 2:  # Would complete our line - WORST
                    score += 1000
                elif my_count == 1 and opp_count == 0 and blanks == 2:  # Start of our line
                    score += 10
                elif my_count == 0 and opp_count == 0:  # Fresh line - slight danger
                    score += 1
        return score
    
    def can_force_opponent_suicide(board_key, pos, player):
        """Check if this move creates a trap for opponent on their next move on this board"""
        board = boards.get(board_key, {})
        # Simulate placing our mark
        temp_board = dict(board)
        temp_board[pos] = player
        
        # Check if opponent has any safe moves left
        safe_moves_for_opp = 0
        for cr in range(1, 4):
            for cc in range(1, 4):
                if temp_board.get((cr, cc), 'b') == 'b':
                    opp_suicide = count_suicide_lines(board_key, (cr, cc), opponent)
                    if opp_suicide == 0:
                        safe_moves_for_opp += 1
        
        return safe_moves_for_opp == 0  # Opponent forced to commit suicide
    
    # Middle board is the only one that matters
    middle_board = (2, 2)
    
    # Separate blank cells
    middle_blanks = [c for c in blank_cells if (c[0], c[1]) == middle_board]
    other_blanks = [c for c in blank_cells if (c[0], c[1]) != middle_board]
    
    # Strategy: Prefer other boards (they don't matter), play carefully on middle board
    
    # If other boards have empty cells, use them first
    if other_blanks:
        # Group by board
        board_vacancy = {}
        for br, bc, cr, cc in other_blanks:
            key = (br, bc)
            if key not in board_vacancy:
                board_vacancy[key] = []
            board_vacancy[key].append((br, bc, cr, cc))
        
        # Prefer boards with more empty cells (more flexibility for future)
        best_boards = sorted(board_vacancy.keys(), key=lambda k: -len(board_vacancy[k]))
        
        # Pick the board with most vacancies, then pick safest cell there
        for board_key in best_boards:
            cells = board_vacancy[board_key]
            # Sort by danger (lowest first)
            cells_sorted = sorted(cells, key=lambda c: get_danger_score(board_key, (c[2], c[3]), role))
            if cells_sorted:
                br, bc, cr, cc = cells_sorted[0]
                return f"mark({br},{bc},{cr},{cc})"
    
    # Must play on middle board - be very strategic
    if middle_blanks:
        # Categorize moves
        safe_moves = []
        suicide_moves = []
        
        for br, bc, cr, cc in middle_blanks:
            pos = (cr, cc)
            suicide_count = count_suicide_lines(middle_board, pos, role)
            danger = get_danger_score(middle_board, pos, role)
            
            if suicide_count == 0:
                # Check if this creates a trap for opponent
                creates_trap = can_force_opponent_suicide(middle_board, pos, role)
                safe_moves.append((br, bc, cr, cc, danger, creates_trap))
            else:
                suicide_moves.append((br, bc, cr, cc, suicide_count, danger))
        
        # Among safe moves, prefer those that trap opponent, then lowest danger
        if safe_moves:
            safe_moves.sort(key=lambda x: (-x[5], x[4]))  # Trap first, then low danger
            best = safe_moves[0]
            return f"mark({best[0]},{best[1]},{best[2]},{best[3]})"
        
        # No safe moves - pick least damaging suicide move
        if suicide_moves:
            suicide_moves.sort(key=lambda x: (x[4], x[5]))  # Fewest completions, then lowest danger
            best = suicide_moves[0]
            return f"mark({best[0]},{best[1]},{best[2]},{best[3]})"
    
    # Fallback - return any blank cell
    if blank_cells:
        br, bc, cr, cc = blank_cells[0]
        return f"mark({br},{bc},{cr},{cc})"
    
    return "mark(1,1,1,1)"
