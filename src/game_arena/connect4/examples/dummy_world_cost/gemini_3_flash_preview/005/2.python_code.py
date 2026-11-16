
import random

def policy(board: list[list[int]]) -> int:
    import time
    
    ROWS = 6
    COLS = 7
    EMPTY = 0
    PLAYER = 1
    OPPONENT = -1

    def get_valid_locations(grid):
        return [c for c in range(COLS) if grid[0][c] == EMPTY]

    def get_next_open_row(grid, col):
        for r in range(ROWS-1, -1, -1):
            if grid[r][col] == EMPTY:
                return r
        return None

    def drop_piece(grid, row, col, piece):
        new_board = [row[:] for row in grid]
        new_board[row][col] = piece
        return new_board

    def evaluate_window(window, piece):
        score = 0
        opp_piece = -piece
        
        if window.count(piece) == 4:
            score += 10000
        elif window.count(piece) == 3 and window.count(EMPTY) == 1:
            score += 100
        elif window.count(piece) == 2 and window.count(EMPTY) == 2:
            score += 10

        if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
            score -= 80
            
        return score

    def score_position(grid, piece):
        score = 0
        
        # Center column preference
        center_array = [grid[i][COLS//2] for i in range(ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 6

        # Horizontal
        for r in range(ROWS):
            row_array = grid[r]
            for c in range(COLS - 3):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)

        # Vertical 
        for c in range(COLS):
            col_array = [grid[r][c] for r in range(ROWS)]
            for r in range(ROWS - 3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)

        # Positive Diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [grid[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        # Negative Diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [grid[r+3-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)

        return score

    def is_terminal_node(grid):
        # Quick check for win
        def check_win(p):
            for r in range(ROWS):
                for c in range(COLS-3):
                    if all(grid[r][c+i] == p for i in range(4)): return True
            for r in range(ROWS-3):
                for c in range(COLS):
                    if all(grid[r+i][c] == p for i in range(4)): return True
            for r in range(ROWS-3):
                for c in range(COLS-3):
                    if all(grid[r+i][c+i] == p for i in range(4)): return True
                    if all(grid[r+3-i][c+i] == p for i in range(4)): return True
            return False

        if check_win(PLAYER): return (True, 1000000)
        if check_win(OPPONENT): return (True, -1000000)
        if len(get_valid_locations(grid)) == 0: return (True, 0)
        return (False, 0)

    def minimax(grid, depth, alpha, beta, maximizingPlayer):
        valid_locations = get_valid_locations(grid)
        is_terminal, term_score = is_terminal_node(grid)
        if depth == 0 or is_terminal:
            if is_terminal:
                return (None, term_score)
            else:
                return (None, score_position(grid, PLAYER))

        if maximizingPlayer:
            value = -float('inf')
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(grid, col)
                b_copy = drop_piece(grid, row, col, PLAYER)
                new_score = minimax(b_copy, depth-1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value

        else:
            value = float('inf')
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = get_next_open_row(grid, col)
                b_copy = drop_piece(grid, row, col, OPPONENT)
                new_score = minimax(b_copy, depth-1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    # Main policy logic
    valid_cols = get_valid_locations(board)
    
    # Check for immediate win or block
    for col in valid_cols:
        r = get_next_open_row(board, col)
        # Can I win?
        if is_terminal_node(drop_piece(board, r, col, PLAYER))[0]:
            return col
            
    col, _ = minimax(board, 4, -float('inf'), float('inf'), True)
    return col if col is not None else valid_cols[0]
