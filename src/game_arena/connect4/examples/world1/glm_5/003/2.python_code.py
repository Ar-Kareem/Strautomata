
import math

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 AI policy using Minimax with Alpha-Beta Pruning.
    """
    ROW_COUNT = 6
    COL_COUNT = 7
    PLAYER = 1
    OPPONENT = -1
    EMPTY = 0
    
    def is_valid_location(col: int) -> bool:
        return board[0][col] == 0

    def get_next_open_row(col: int) -> int:
        for r in range(ROW_COUNT - 1, -1, -1):
            if board[r][col] == 0:
                return r
        return -1

    def is_winning_move(row: int, col: int, piece: int) -> bool:
        """Checks if placing a piece at (row, col) results in a win."""
        # Check Horizontal
        count = 0
        for c in range(max(0, col - 3), min(COL_COUNT, col + 4)):
            if board[row][c] == piece:
                count += 1
                if count == 4: return True
            else:
                count = 0
        
        # Check Vertical
        count = 0
        for r in range(max(0, row - 3), min(ROW_COUNT, row + 4)):
            if board[r][col] == piece:
                count += 1
                if count == 4: return True
            else:
                count = 0
        
        # Check Positive Diagonal (/)
        count = 0
        for i in range(-3, 4):
            r, c = row + i, col + i
            if 0 <= r < ROW_COUNT and 0 <= c < COL_COUNT:
                if board[r][c] == piece:
                    count += 1
                    if count == 4: return True
                else:
                    count = 0
            else:
                count = 0

        # Check Negative Diagonal (\)
        count = 0
        for i in range(-3, 4):
            r, c = row - i, col + i
            if 0 <= r < ROW_COUNT and 0 <= c < COL_COUNT:
                if board[r][c] == piece:
                    count += 1
                    if count == 4: return True
                else:
                    count = 0
        
        return False

    def evaluate_window(window: list[int], piece: int) -> int:
        score = 0
        opp_piece = OPPONENT if piece == PLAYER else PLAYER
        
        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(EMPTY) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(EMPTY) == 2:
            score += 2
        
        if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
            score -= 4
            
        return score

    def score_position(piece: int) -> int:
        score = 0
        
        # Score Center column
        center_array = [row[COL_COUNT // 2] for row in board]
        center_count = center_array.count(piece)
        score += center_count * 3
        
        # Score Horizontal
        for r in range(ROW_COUNT):
            row_array = board[r]
            for c in range(COL_COUNT - 3):
                window = row_array[c:c+4]
                score += evaluate_window(window, piece)
                
        # Score Vertical
        for c in range(COL_COUNT):
            col_array = [board[r][c] for r in range(ROW_COUNT)]
            for r in range(ROW_COUNT - 3):
                window = col_array[r:r+4]
                score += evaluate_window(window, piece)
        
        # Score Positive Diagonal
        for r in range(ROW_COUNT - 3):
            for c in range(COL_COUNT - 3):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
                
        # Score Negative Diagonal
        for r in range(ROW_COUNT - 3):
            for c in range(COL_COUNT - 3):
                window = [board[r+3-i][c+i] for i in range(4)]
                score += evaluate_window(window, piece)
                
        return score

    def minimax(depth: int, alpha: float, beta: float, maximizingPlayer: bool, last_r: int, last_c: int) -> tuple[int, int]:
        # Check terminal state from the last move made
        if last_r != -1:
            # The previous move was made by the opposing player
            prev_piece = OPPONENT if maximizingPlayer else PLAYER
            if is_winning_move(last_r, last_c, prev_piece):
                if prev_piece == PLAYER:
                    return (None, 10000000000)
                else:
                    return (None, -10000000000)
        
        valid_locations = [c for c in range(COL_COUNT) if is_valid_location(c)]
        
        if depth == 0:
            return (None, score_position(PLAYER))
        if len(valid_locations) == 0:
            return (None, 0)
            
        # Move ordering: prioritize center columns
        move_order = [3, 2, 4, 1, 5, 0, 6]
        valid_locations.sort(key=lambda x: move_order.index(x))
        
        if maximizingPlayer:
            value = -math.inf
            column = valid_locations[0]
            for col in valid_locations:
                row = get_next_open_row(col)
                board[row][col] = PLAYER
                new_score = minimax(depth - 1, alpha, beta, False, row, col)[1]
                board[row][col] = EMPTY
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value = math.inf
            column = valid_locations[0]
            for col in valid_locations:
                row = get_next_open_row(col)
                board[row][col] = OPPONENT
                new_score = minimax(depth - 1, alpha, beta, True, row, col)[1]
                board[row][col] = EMPTY
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    # Main logic
    valid_locations = [c for c in range(COL_COUNT) if is_valid_location(c)]
    
    # 1. Immediate Win Check
    for col in valid_locations:
        row = get_next_open_row(col)
        board[row][col] = PLAYER
        if is_winning_move(row, col, PLAYER):
            board[row][col] = EMPTY
            return col
        board[row][col] = EMPTY

    # 2. Block Opponent Win Check
    for col in valid_locations:
        row = get_next_open_row(col)
        board[row][col] = OPPONENT
        if is_winning_move(row, col, OPPONENT):
            board[row][col] = EMPTY
            return col
        board[row][col] = EMPTY
        
    # 3. Minimax Search (Depth 6)
    col, _ = minimax(6, -math.inf, math.inf, True, -1, -1)
    return col
