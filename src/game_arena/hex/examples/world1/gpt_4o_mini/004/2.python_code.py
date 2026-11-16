
def policy(me, opp, color):
    # Create an 11x11 board representation
    board = [['.' for _ in range(11)] for _ in range(11)]
    
    # Place stones on the board
    for r, c in me:
        board[r][c] = color
    for r, c in opp:
        board[r][c] = 'w' if color == 'b' else 'b'
    
    # Directions for neighboring hex cells
    directions = [(-1, 0), (1, 0), (-1, 1), (1, -1), (0, -1), (0, 1)]
    
    def is_within_board(x, y):
        return 0 <= x < 11 and 0 <= y < 11
    
    def evaluate_move(row, col):
        # Evaluation function to assess the potential of a move
        score = 0
        
        # If the move connects to my existing stones, increase the score
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if is_within_board(nr, nc) and board[nr][nc] == color:
                score += 1
        
        # If the move blocks the opponent's potential wins, increase the score
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if is_within_board(nr, nc) and board[nr][nc] == ('w' if color == 'b' else 'b'):
                score -= 1
        
        return score

    best_move = None
    best_score = -float('inf')

    # Iterate through all possible moves
    for r in range(11):
        for c in range(11):
            if board[r][c] == '.':
                score = evaluate_move(r, c)
                if score > best_score:
                    best_score = score
                    best_move = (r, c)

    # Always return a legal move
    return best_move
