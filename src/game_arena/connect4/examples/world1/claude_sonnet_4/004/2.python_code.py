
def policy(board: list[list[int]]) -> int:
    def is_valid_move(col):
        return board[0][col] == 0
    
    def get_valid_moves():
        return [col for col in range(7) if is_valid_move(col)]
    
    def drop_piece(board_copy, col, player):
        for row in range(5, -1, -1):
            if board_copy[row][col] == 0:
                board_copy[row][col] = player
                return row
        return -1
    
    def check_win(board_state, player):
        # Check all possible 4-in-a-row combinations
        for row in range(6):
            for col in range(7):
                if board_state[row][col] == player:
                    # Horizontal
                    if col + 3 < 7:
                        if all(board_state[row][col+i] == player for i in range(4)):
                            return True
                    # Vertical
                    if row + 3 < 6:
                        if all(board_state[row+i][col] == player for i in range(4)):
                            return True
                    # Diagonal down-right
                    if row + 3 < 6 and col + 3 < 7:
                        if all(board_state[row+i][col+i] == player for i in range(4)):
                            return True
                    # Diagonal down-left
                    if row + 3 < 6 and col - 3 >= 0:
                        if all(board_state[row+i][col-i] == player for i in range(4)):
                            return True
        return False
    
    def count_threats(board_state, player):
        # Count how many 3-in-a-row with 1 empty space (threats) a player has
        threats = 0
        directions = [(0,1), (1,0), (1,1), (1,-1)]  # horizontal, vertical, diag-right, diag-left
        
        for row in range(6):
            for col in range(7):
                for dr, dc in directions:
                    # Check 4-length windows
                    window = []
                    valid_window = True
                    for i in range(4):
                        r, c = row + i * dr, col + i * dc
                        if 0 <= r < 6 and 0 <= c < 7:
                            window.append(board_state[r][c])
                        else:
                            valid_window = False
                            break
                    
                    if valid_window:
                        player_count = window.count(player)
                        empty_count = window.count(0)
                        opponent_count = window.count(-player)
                        
                        # This is a threat if we have 3 pieces and 1 empty, no opponent pieces
                        if player_count == 3 and empty_count == 1 and opponent_count == 0:
                            threats += 1
        
        return threats
    
    def evaluate_move(col):
        # Create a copy of the board and simulate the move
        board_copy = [row[:] for row in board]
        drop_row = drop_piece(board_copy, col, 1)
        
        if drop_row == -1:  # Invalid move
            return float('-inf')
        
        # Immediate win is best
        if check_win(board_copy, 1):
            return 1000
        
        # Check if this move gives opponent an immediate win next turn
        for opp_col in range(7):
            if is_valid_move(opp_col):
                opp_board = [row[:] for row in board_copy]
                if drop_piece(opp_board, opp_col, -1) != -1:
                    if check_win(opp_board, -1):
                        return -500  # Bad move, gives opponent a win
        
        score = 0
        
        # Center column preference
        if col == 3:
            score += 10
        elif col in [2, 4]:
            score += 5
        elif col in [1, 5]:
            score += 2
        
        # Count our threats vs opponent threats
        our_threats = count_threats(board_copy, 1)
        opp_threats = count_threats(board_copy, -1)
        score += our_threats * 20 - opp_threats * 15
        
        return score
    
    valid_moves = get_valid_moves()
    
    # Quick check: can we win immediately?
    for col in valid_moves:
        board_copy = [row[:] for row in board]
        drop_piece(board_copy, col, 1)
        if check_win(board_copy, 1):
            return col
    
    # Quick check: must we block opponent's win?
    for col in valid_moves:
        board_copy = [row[:] for row in board]
        drop_piece(board_copy, col, -1)
        if check_win(board_copy, -1):
            return col
    
    # Evaluate all moves and return the best
    best_col = valid_moves[0]
    best_score = float('-inf')
    
    for col in valid_moves:
        score = evaluate_move(col)
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col
