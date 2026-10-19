
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Find all available cells (0s)
    available = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
    
    # Check for immediate winning moves
    winning_moves = []
    for r, c in available:
        row_sum = sum(board[r])
        col_sum = sum(board[i][c] for i in range(3))
        diag_sum, anti_diag_sum = 0, 0
        if r == c:
            diag_sum = sum(board[i][i] for i in range(3))
        if r + c == 2:
            anti_diag_sum = sum(board[i][2-i] for i in range(3))
        if row_sum == 2 or col_sum == 2 or diag_sum == 2 or anti_diag_sum == 2:
            winning_moves.append((r, c))
    if winning_moves:
        return winning_moves[0]
    
    # Calculate scores for each available cell
    scores = {}
    for r, c in available:
        score = sum(board[r])  # Row score
        score += sum(board[i][c] for i in range(3))  # Column score
        if r == c:
            score += sum(board[i][i] for i in range(3))  # Main diagonal score
        if r + c == 2:
            score += sum(board[i][2-i] for i in range(3))  # Anti diagonal score
        scores[(r, c)] = score
    
    max_score = max(scores.values())
    best_cells = [cell for cell, score in scores.items() if score == max_score]
    
    # Priority order: center, corners, edges
    priority_order = [
        (1, 1),          # Center
        (0, 0), (0, 2), (2, 2), (2, 0),  # Corners
        (0, 1), (1, 2), (2, 1), (1, 0)   # Edges
    ]
    
    # Return the first cell in priority_order that is in best_cells
    for cell in priority_order:
        if cell in best_cells:
            return cell
    
    # Fallback (should not reach here if available is non-empty)
    return available[0]
