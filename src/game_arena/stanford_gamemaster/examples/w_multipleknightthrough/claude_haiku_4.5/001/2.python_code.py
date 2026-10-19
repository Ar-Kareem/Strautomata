
def policy(state: list[list[object]], role: str) -> str:
    # Parse state to find all pieces
    pieces = {}  # (board, col, row) -> color
    for proposition in state:
        if proposition[0] == "cell":
            board, col, row, color = proposition[1], proposition[2], int(proposition[3]), proposition[4]
            pieces[(board, col, int(row))] = color
    
    # Find all pieces of our role
    our_pieces = [(board, col, row) for (board, col, row), color in pieces.items() if color == role]
    
    # Knight move offsets (row_delta, col_delta, board_delta)
    # Forward moves for white (increasing row), backward moves for black (decreasing row)
    if role == "white":
        knight_moves = [
            (2, 1, 0), (2, -1, 0),  # +2 rows, ±1 col, same board
            (1, 2, 0), (1, -2, 0),  # +1 row, ±2 col, same board
            (2, 1, 1), (2, -1, 1), (2, 0, 1),  # +2 rows, col change, next board
            (1, 2, 1), (1, -2, 1), (1, 0, 1), (1, 1, 1), (1, -1, 1),  # +1 row, col change, next board
        ]
    else:  # black
        knight_moves = [
            (-2, 1, 0), (-2, -1, 0),  # -2 rows, ±1 col, same board
            (-1, 2, 0), (-1, -2, 0),  # -1 row, ±2 col, same board
            (-2, 1, 1), (-2, -1, 1), (-2, 0, 1),  # -2 rows, col change, next board
            (-1, 2, 1), (-1, -2, 1), (-1, 0, 1), (-1, 1, 1), (-1, -1, 1),  # -1 row, col change, next board
        ]
    
    best_move = None
    best_score = -float('inf')
    
    def col_to_num(col):
        return ord(col) - ord('a')
    
    def num_to_col(num):
        return chr(ord('a') + num)
    
    def board_to_num(board):
        return ord(board) - ord('a')
    
    def num_to_board(num):
        return chr(ord('a') + num)
    
    for board, col, row in our_pieces:
        for row_delta, col_delta, board_delta in knight_moves:
            new_row = row + row_delta
            new_col_num = col_to_num(col) + col_delta
            new_board_num = board_to_num(board) + board_delta
            
            # Check bounds
            if not (1 <= new_row <= 8):
                continue
            if not (0 <= new_col_num <= 3):
                continue
            if not (0 <= new_board_num <= 2):
                continue
            
            new_board = num_to_board(new_board_num)
            new_col = num_to_col(new_col_num)
            
            # Check if target is occupied by our piece
            if (new_board, new_col, new_row) in pieces and pieces[(new_board, new_col, new_row)] == role:
                continue
            
            # Score the move
            score = 0
            
            # Winning move
            if role == "white" and new_board == "b" and new_row == 8:
                score = 10000
            elif role == "black" and new_board == "b" and new_row == 1:
                score = 10000
            
            # Progress toward goal
            if role == "white":
                if new_board == "b":
                    score += 100 + new_row  # Closer to row 8 is better
                elif new_board == "a":
                    score += 50
            else:  # black
                if new_board == "b":
                    score += 100 + (9 - new_row)  # Closer to row 1 is better
                elif new_board == "a":
                    score += 50
            
            if score > best_score:
                best_score = score
                best_move = f"move({board},{col},{row},{new_board},{new_col},{new_row})"
    
    # Fallback: return any legal move
    if best_move is None and our_pieces:
        board, col, row = our_pieces[0]
        for row_delta, col_delta, board_delta in knight_moves:
            new_row = row + row_delta
            new_col_num = col_to_num(col) + col_delta
            new_board_num = board_to_num(board) + board_delta
            
            if 1 <= new_row <= 8 and 0 <= new_col_num <= 3 and 0 <= new_board_num <= 2:
                new_board = num_to_board(new_board_num)
                new_col = num_to_col(new_col_num)
                if (new_board, new_col, new_row) not in pieces or pieces[(new_board, new_col, new_row)] != role:
                    best_move = f"move({board},{col},{row},{new_board},{new_col},{new_row})"
                    break
    
    return best_move if best_move else "move(a,a,1,b,a,3)"
