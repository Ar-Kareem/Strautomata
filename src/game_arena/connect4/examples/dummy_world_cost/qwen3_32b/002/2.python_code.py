
def policy(board: list[list[int]]) -> int:
    def get_valid_moves():
        return [col for col in range(7) if any(board[row][col] == 0 for row in range(6))]

    def get_next_row(col):
        for row in reversed(range(6)):
            if board[row][col] == 0:
                return row
        return -1

    def simulate_move(col, player):
        new_board = [row[:] for row in board]
        row = get_next_row(col)
        new_board[row][col] = player
        return new_board, row

    def is_win(b, row, col, player):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            for i, sign in ((-1, -1), (1, 1)):
                r, c = row + dr * i, col + dc * i
                while 0 <= r < 6 and 0 <= c < 7 and b[r][c] == player:
                    count += 1
                    r += dr * sign
                    c += dc * sign
            if count >= 4:
                return True
        return False

    def score_segment(segment, player):
        other = -player
        player_count = sum(1 for x in segment if x == player)
        other_count = sum(1 for x in segment if x == other)
        empty = 4 - player_count - other_count
        
        if player_count == 4:
            return 10000
        if player_count == 3 and empty == 1:
            return 100
        if player_count == 2 and empty >= 2:
            return 10
        if player_count == 1 and empty >= 3:
            return 1
            
        if other_count == 4:
            return -10000
        if other_count == 3 and empty == 1:
            return -100
        if other_count == 2 and empty >= 2:
            return -10
        if other_count == 1 and empty >= 3:
            return -1
        return 0

    def evaluate_heuristic(b, player):
        score = 0
        # Horizontal
        for r in range(6):
            for c in range(4):
                segment = [b[r][c + i] for i in range(4)]
                score += score_segment(segment, player)
        # Vertical
        for c in range(7):
            for r in range(3):
                segment = [b[r + i][c] for i in range(4)]
                score += score_segment(segment, player)
        # Diagonal \
        for r in range(3):
            for c in range(4):
                segment = [b[r + i][c + i] for i in range(4)]
                score += score_segment(segment, player)
        # Diagonal /
        for r in range(3):
            for c in range(4, 7):
                segment = [b[r + i][c - i] for i in range(4)]
                score += score_segment(segment, player)
        return score

    valid_moves = get_valid_moves()
    
    # Check for immediate win
    for col in valid_moves:
        new_board, row = simulate_move(col, 1)
        if is_win(new_board, row, col, 1):
            return col
    
    # Block opponent's immediate win
    opponent = -1
    for col in valid_moves:
        new_board, row = simulate_move(col, opponent)
        if is_win(new_board, row, col, opponent):
            return col
    
    # Choose best move based on evaluation
    best_score = -float('inf')
    best_move = valid_moves[0]
    
    for col in valid_moves:
        new_board, row = simulate_move(col, 1)
        current_score = evaluate_heuristic(new_board, 1)
        if current_score > best_score:
            best_score = current_score
            best_move = col
            
    return best_move
