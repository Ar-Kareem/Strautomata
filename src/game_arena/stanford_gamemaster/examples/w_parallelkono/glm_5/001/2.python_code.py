
def policy(state: list[list[object]], role: str) -> str:
    # Parse state
    cells = {}
    played = set()
    
    for prop in state:
        if not prop:
            continue
        if prop[0] == "cell" and len(prop) >= 5:
            board, row, col, color = prop[1], int(prop[2]), int(prop[3]), prop[4]
            cells[(board, row, col)] = color
        elif prop[0] == "played" and len(prop) >= 2:
            played.add(prop[1])
    
    opponent = "black" if role == "red" else "red"
    
    # Must tick if both boards played
    if "a" in played and "b" in played:
        return "tick"
    
    # Available boards
    available_boards = [b for b in ["a", "b"] if b not in played]
    
    if not available_boards:
        return "tick"
    
    def is_vulnerable(board, r, c):
        """Check if piece at (r,c) can be captured by opponent"""
        jump_dirs = [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (-2, 2), (2, -2), (2, 2)]
        for dr, dc in jump_dirs:
            from_r, from_c = r - dr, c - dc
            over_r, over_c = r - dr//2, c - dc//2
            if 1 <= from_r <= 4 and 1 <= from_c <= 4:
                from_piece = cells.get((board, from_r, from_c))
                over_piece = cells.get((board, over_r, over_c))
                if from_piece == opponent and over_piece == opponent:
                    return True
        return False
    
    def find_jumps(board):
        jumps = []
        for (b, r, c), color in cells.items():
            if b != board or color != role:
                continue
            jump_dirs = [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (-2, 2), (2, -2), (2, 2)]
            for dr, dc in jump_dirs:
                over_r, over_c = r + dr//2, c + dc//2
                to_r, to_c = r + dr, c + dc
                if 1 <= to_r <= 4 and 1 <= to_c <= 4:
                    over_piece = cells.get((board, over_r, over_c))
                    to_piece = cells.get((board, to_r, to_c))
                    if over_piece == role and to_piece == opponent:
                        jumps.append((board, r, c, over_r, over_c, to_r, to_c))
        return jumps
    
    def find_moves(board):
        moves = []
        for (b, r, c), color in cells.items():
            if b != board or color != role:
                continue
            move_dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in move_dirs:
                to_r, to_c = r + dr, c + dc
                if 1 <= to_r <= 4 and 1 <= to_c <= 4:
                    to_piece = cells.get((board, to_r, to_c))
                    if to_piece == "blank":
                        moves.append((board, r, c, to_r, to_c))
        return moves
    
    # Collect all actions
    all_jumps = []
    all_moves = []
    
    for board in available_boards:
        all_jumps.extend(find_jumps(board))
        all_moves.extend(find_moves(board))
    
    # Prioritize jumps (captures are worth 12 points)
    if all_jumps:
        best_score = -float('inf')
        best_jump = all_jumps[0]
        for j in all_jumps:
            board, fr, fc, or_, oc, tr, tc = j
            score = 100  # Base score for capture
            # Penalize vulnerable landing positions
            if is_vulnerable(board, tr, tc):
                score -= 30
            # Bonus for forward jumps
            if role == "red" and tr < fr:
                score += 15
            elif role == "black" and tr > fr:
                score += 15
            if score > best_score:
                best_score = score
                best_jump = j
        return f"jump({best_jump[0]},{best_jump[1]},{best_jump[2]},{best_jump[3]},{best_jump[4]},{best_jump[5]},{best_jump[6]})"
    
    # Then evaluate moves
    if all_moves:
        best_score = -float('inf')
        best_move = all_moves[0]
        for m in all_moves:
            board, fr, fc, tr, tc = m
            score = 0
            # Forward moves are better
            if role == "red" and tr < fr:
                score += 20
            elif role == "black" and tr > fr:
                score += 20
            # Penalize vulnerable positions
            if is_vulnerable(board, tr, tc):
                score -= 10
            # Slight bonus for center control
            if 2 <= tr <= 3 and 2 <= tc <= 3:
                score += 5
            if score > best_score:
                best_score = score
                best_move = m
        return f"move({best_move[0]},{best_move[1]},{best_move[2]},{best_move[3]},{best_move[4]})"
    
    return "tick"
