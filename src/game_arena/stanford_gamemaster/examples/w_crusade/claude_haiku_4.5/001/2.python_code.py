
def policy(state: list[list[object]], role: str) -> str:
    # Parse the board state
    my_pieces = {}
    opponent_pieces = {}
    opponent_role = "black" if role == "white" else "white"
    
    for fact in state:
        if fact[0] == "cell":
            col, row, piece_color = fact[1], int(fact[2]), fact[3]
            if piece_color == role:
                my_pieces[(col, row)] = True
            elif piece_color == opponent_role:
                opponent_pieces[(col, row)] = True
    
    # Knight move offsets
    knight_moves = [
        (2, 1), (2, -1), (-2, 1), (-2, -1),
        (1, 2), (1, -2), (-1, 2), (-1, -2)
    ]
    
    # Convert column letter to number and back
    def col_to_num(col):
        return ord(col) - ord('a')
    
    def num_to_col(num):
        return chr(ord('a') + num)
    
    def is_valid_pos(col, row):
        return 0 <= col <= 7 and 1 <= row <= 8
    
    best_move = None
    best_score = -1
    
    # Evaluate all possible moves
    for (col, row), _ in my_pieces.items():
        col_num = col_to_num(col)
        
        for dc, dr in knight_moves:
            new_col_num = col_num + dc
            new_row = row + dr
            
            if not is_valid_pos(new_col_num, new_row):
                continue
            
            new_col = num_to_col(new_col_num)
            new_pos = (new_col, new_row)
            
            # Check if target is empty or contains opponent piece
            if new_pos in my_pieces:
                continue
            
            move_str = f"move({col},{row},{new_col},{new_row})"
            score = 0
            
            # Prioritize captures
            if new_pos in opponent_pieces:
                score += 1000
            
            # Reward moving toward opponent side
            if role == "white":
                score += new_row  # Moving up (toward row 8)
            else:
                score -= new_row  # Moving down (toward row 1)
            
            # Reward center control (columns c-f, rows 3-6)
            if 2 <= new_col_num <= 5 and 3 <= new_row <= 6:
                score += 100
            
            if score > best_score:
                best_score = score
                best_move = move_str
    
    # Fallback: if no move found, pick any legal move
    if best_move is None:
        for (col, row), _ in my_pieces.items():
            col_num = col_to_num(col)
            for dc, dr in knight_moves:
                new_col_num = col_num + dc
                new_row = row + dr
                if is_valid_pos(new_col_num, new_row):
                    new_col = num_to_col(new_col_num)
                    new_pos = (new_col, new_row)
                    if new_pos not in my_pieces:
                        best_move = f"move({col},{row},{new_col},{new_row})"
                        break
            if best_move:
                break
    
    return best_move if best_move else "move(a,1,b,3)"
