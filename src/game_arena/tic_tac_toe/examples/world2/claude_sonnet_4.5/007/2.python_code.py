
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Find all empty positions
    empty_positions = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty_positions.append((i, j))
    
    if not empty_positions:
        return (0, 0)
    
    # Define all possible winning lines (4 in a row)
    lines = []
    
    # Rows
    for i in range(4):
        lines.append([(i, 0), (i, 1), (i, 2), (i, 3)])
    
    # Columns
    for j in range(4):
        lines.append([(0, j), (1, j), (2, j), (3, j)])
    
    # Diagonals
    lines.append([(0, 0), (1, 1), (2, 2), (3, 3)])
    lines.append([(0, 3), (1, 2), (2, 1), (3, 0)])
    
    # Evaluate each possible move
    def evaluate_move(pos):
        r, c = pos
        score = 0
        
        for line in lines:
            if pos in line:
                my_count = 0
                opp_count = 0
                empty_count = 0
                
                for lr, lc in line:
                    if board[lr][lc] == 1:
                        my_count += 1
                    elif board[lr][lc] == -1:
                        opp_count += 1
                    else:
                        empty_count += 1
                
                # After placing at this position
                my_count_after = my_count + 1
                
                # Immediate win
                if my_count_after == 4:
                    score += 10000
                # Block opponent's win
                elif opp_count == 3 and empty_count == 1:
                    score += 5000
                # Create strong threat (3 in a row with no opponent pieces)
                elif my_count_after == 3 and opp_count == 0:
                    score += 100
                # Build position (2 in a row with no opponent pieces)
                elif my_count_after == 2 and opp_count == 0:
                    score += 10
                # Block opponent's developing line
                elif opp_count == 2 and my_count == 0:
                    score += 5
        
        # Prefer center positions
        if r in [1, 2] and c in [1, 2]:
            score += 2
        
        return score
    
    # Find best move
    best_score = -1
    best_move = empty_positions[0]
    
    for pos in empty_positions:
        score = evaluate_move(pos)
        if score > best_score:
            best_score = score
            best_move = pos
    
    return best_move
