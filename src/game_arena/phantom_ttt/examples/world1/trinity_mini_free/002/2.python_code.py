
def policy(board, legal_moves):
    # Precompute static line counts for each cell (0-8)
    static_counts = [0] * 9
    for idx in range(9):
        row = idx // 3
        col = idx % 3
        count = 0
        # Check rows
        if row == 0:
            count += 1
        elif row == 1:
            count += 1
        elif row == 2:
            count += 1
        # Check columns
        if col == 0:
            count += 1
        elif col == 1:
            count += 1
        elif col == 2:
            count += 1
        # Check diagonals
        if row == col:
            count += 1
        if row + col == 2:
            count += 1
        static_counts[idx] = count

    best_move = None
    best_count = -1
    for move in legal_moves:
        row = move // 3
        col = move % 3
        # Skip if already confirmed as mine (though legal_moves shouldn't include these)
        if board[row][col] == 1:
            continue
        count = static_counts[move]
        if count > best_count:
            best_count = count
            best_move = (row, col)
    
    # Fallback if no valid move found (unlikely)
    if best_move is None:
        best_move = (legal_moves[0] // 3, legal_moves[0] % 3)
    
    return best_move
