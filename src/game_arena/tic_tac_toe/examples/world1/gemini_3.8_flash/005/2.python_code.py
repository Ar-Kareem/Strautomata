
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Computes the optimal move for player 1 using Minimax with Alpha-Beta pruning.
    
    Args:
        board: 3x3 list of lists where 0 is empty, 1 is our move, -1 is opponent's move.
        
    Returns:
        tuple[int, int]: (row, col) representing the chosen move.
    """
    b = [list(row) for row in board]
    empty_cells = [(r, c) for r in range(3) for c in range(3) if b[r][c] == 0]
    
    if not empty_cells:
        return (0, 0)
    
    # Fast path: Center is always optimal on an empty board
    if len(empty_cells) == 9:
        return (1, 1)

    def check_winner(grid: list[list[int]]) -> int:
        for i in range(3):
            # Check row i
            row_sum = grid[i][0] + grid[i][1] + grid[i][2]
            if row_sum == 3:
                return 1
            if row_sum == -3:
                return -1
            # Check column i
            col_sum = grid[0][i] + grid[1][i] + grid[2][i]
            if col_sum == 3:
                return 1
            if col_sum == -3:
                return -1

        # Check diagonals
        diag1 = grid[0][0] + grid[1][1] + grid[2][2]
        if diag1 == 3:
            return 1
        if diag1 == -3:
            return -1

        diag2 = grid[0][2] + grid[1][1] + grid[2][0]
        if diag2 == 3:
            return 1
        if diag2 == -3:
            return -1

        return 0

    memo = {}

    def minimax(grid: list[list[int]], depth: int, is_maximizing: bool, alpha: float, beta: float) -> int:
        winner = check_winner(grid)
        if winner == 1:
            return 10 - depth
        if winner == -1:
            return depth - 10

        grid_key = (tuple(tuple(r) for r in grid), is_maximizing)
        if grid_key in memo:
            return memo[grid_key]

        available = [(r, c) for r in range(3) for c in range(3) if grid[r][c] == 0]
        if not available:
            return 0

        if is_maximizing:
            max_eval = -float("inf")
            for r, c in available:
                grid[r][c] = 1
                ev = minimax(grid, depth + 1, False, alpha, beta)
                grid[r][c] = 0
                if ev > max_eval:
                    max_eval = ev
                alpha = max(alpha, ev)
                if beta <= alpha:
                    break
            memo[grid_key] = max_eval
            return max_eval
        else:
            min_eval = float("inf")
            for r, c in available:
                grid[r][c] = -1
                ev = minimax(grid, depth + 1, True, alpha, beta)
                grid[r][c] = 0
                if ev < min_eval:
                    min_eval = ev
                beta = min(beta, ev)
                if beta <= alpha:
                    break
            memo[grid_key] = min_eval
            return min_eval

    best_score = -float("inf")
    best_move = empty_cells[0]

    for r, c in empty_cells:
        b[r][c] = 1
        move_score = minimax(b, 1, False, -float("inf"), float("inf"))
        b[r][c] = 0
        if move_score > best_score:
            best_score = move_score
            best_move = (r, c)

    return best_move
