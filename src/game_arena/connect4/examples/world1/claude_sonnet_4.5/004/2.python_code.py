
def policy(board: list[list[int]]) -> int:
    def is_valid_move(board, col):
        return board[0][col] == 0
    
    def get_valid_moves(board):
        return [col for col in range(7) if is_valid_move(board, col)]
    
    def drop_piece(board, col, player):
        """Drop a piece and return the row where it landed."""
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                board[row][col] = player
                return row
        return -1
    
    def check_win(board, player):
        # Horizontal
        for row in range(6):
            for col in range(4):
                if all(board[row][col+i] == player for i in range(4)):
                    return True
        # Vertical
        for row in range(3):
            for col in range(7):
                if all(board[row+i][col] == player for i in range(4)):
                    return True
        # Diagonal /
        for row in range(3, 6):
            for col in range(4):
                if all(board[row-i][col+i] == player for i in range(4)):
                    return True
        # Diagonal \
        for row in range(3):
            for col in range(4):
                if all(board[row+i][col+i] == player for i in range(4)):
                    return True
        return False
    
    def copy_board(board):
        return [row[:] for row in board]
    
    def count_threats(board, player):
        """Count potential 4-in-a-row opportunities."""
        count = 0
        # Check all possible 4-in-a-row positions
        # Horizontal
        for row in range(6):
            for col in range(4):
                window = [board[row][col+i] for i in range(4)]
                if window.count(player) == 3 and window.count(0) == 1:
                    count += 1
        # Vertical
        for row in range(3):
            for col in range(7):
                window = [board[row+i][col] for i in range(4)]
                if window.count(player) == 3 and window.count(0) == 1:
                    count += 1
        # Diagonals
        for row in range(3, 6):
            for col in range(4):
                window = [board[row-i][col+i] for i in range(4)]
                if window.count(player) == 3 and window.count(0) == 1:
                    count += 1
        for row in range(3):
            for col in range(4):
                window = [board[row+i][col+i] for i in range(4)]
                if window.count(player) == 3 and window.count(0) == 1:
                    count += 1
        return count
    
    # 1. Win immediately if possible
    for col in get_valid_moves(board):
        test_board = copy_board(board)
        drop_piece(test_board, col, 1)
        if check_win(test_board, 1):
            return col
    
    # 2. Block opponent's winning move
    for col in get_valid_moves(board):
        test_board = copy_board(board)
        drop_piece(test_board, col, -1)
        if check_win(test_board, -1):
            return col
    
    # 3. Evaluate moves and avoid giving opponent a win
    valid_moves = get_valid_moves(board)
    move_scores = []
    
    for col in valid_moves:
        test_board = copy_board(board)
        row = drop_piece(test_board, col, 1)
        
        # Check if this gives opponent an immediate win opportunity
        opponent_can_win = False
        for opp_col in get_valid_moves(test_board):
            opp_board = copy_board(test_board)
            drop_piece(opp_board, opp_col, -1)
            if check_win(opp_board, -1):
                opponent_can_win = True
                break
        
        if opponent_can_win:
            score = -1000
        else:
            # Evaluate position
            my_threats = count_threats(test_board, 1)
            opp_threats = count_threats(test_board, -1)
            center_bonus = 4 - abs(col - 3)
            score = my_threats * 10 - opp_threats * 5 + center_bonus
        
        move_scores.append((score, col))
    
    # Choose best move
    move_scores.sort(reverse=True)
    return move_scores[0][1]
