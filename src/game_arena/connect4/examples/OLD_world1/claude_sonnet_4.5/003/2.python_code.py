
import random

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 AI policy that prioritizes winning moves, blocking opponent wins,
    and strategic positioning.
    """
    rows = 6
    cols = 7
    
    def get_next_open_row(col):
        """Find the next open row in a column (bottom-up)."""
        for row in range(rows - 1, -1, -1):
            if board[row][col] == 0:
                return row
        return None
    
    def is_valid_move(col):
        """Check if a column has space."""
        return board[0][col] == 0
    
    def check_window(window, player):
        """Count potential in a 4-cell window."""
        player_count = window.count(player)
        empty_count = window.count(0)
        opponent_count = window.count(-player)
        
        if player_count == 4:
            return 1000000  # Win
        elif player_count == 3 and empty_count == 1:
            return 100  # Strong threat
        elif player_count == 2 and empty_count == 2:
            return 10  # Potential
        elif opponent_count == 0 and player_count > 0:
            return 1
        return 0
    
    def evaluate_position(test_board, player):
        """Evaluate board position for a player."""
        score = 0
        
        # Horizontal
        for row in range(rows):
            for col in range(cols - 3):
                window = [test_board[row][col + i] for i in range(4)]
                score += check_window(window, player)
        
        # Vertical
        for col in range(cols):
            for row in range(rows - 3):
                window = [test_board[row + i][col] for i in range(4)]
                score += check_window(window, player)
        
        # Diagonal (positive slope)
        for row in range(rows - 3):
            for col in range(cols - 3):
                window = [test_board[row + i][col + i] for i in range(4)]
                score += check_window(window, player)
        
        # Diagonal (negative slope)
        for row in range(3, rows):
            for col in range(cols - 3):
                window = [test_board[row - i][col + i] for i in range(4)]
                score += check_window(window, player)
        
        # Prefer center columns
        center_array = [test_board[row][cols // 2] for row in range(rows)]
        center_count = center_array.count(player)
        score += center_count * 3
        
        return score
    
    def simulate_move(col, player):
        """Simulate dropping a disc and return the new board state."""
        row = get_next_open_row(col)
        if row is None:
            return None
        
        # Create a copy of the board
        new_board = [row[:] for row in board]
        new_board[row][col] = player
        return new_board
    
    def check_winning_move(col, player):
        """Check if a move in this column wins the game."""
        test_board = simulate_move(col, player)
        if test_board is None:
            return False
        
        row = get_next_open_row(col)
        
        # Check horizontal
        for c in range(max(0, col - 3), min(cols - 3, col) + 1):
            if all(test_board[row][c + i] == player for i in range(4)):
                return True
        
        # Check vertical
        if row <= rows - 4:
            if all(test_board[row + i][col] == player for i in range(4)):
                return True
        
        # Check diagonals
        for dr, dc in [(1, 1), (1, -1)]:
            for offset in range(-3, 1):
                r, c = row + offset * dr, col + offset * dc
                if 0 <= r <= rows - 4 * dr and 0 <= c < cols and c + 3 * dc < cols and c + 3 * dc >= 0:
                    if all(0 <= r + i * dr < rows and 0 <= c + i * dc < cols and 
                           test_board[r + i * dr][c + i * dc] == player for i in range(4)):
                        return True
        
        return False
    
    # Get valid moves
    valid_moves = [col for col in range(cols) if is_valid_move(col)]
    
    if not valid_moves:
        return 0
    
    # 1. Check for immediate winning move
    for col in valid_moves:
        if check_winning_move(col, 1):
            return col
    
    # 2. Block opponent's winning move
    for col in valid_moves:
        if check_winning_move(col, -1):
            return col
    
    # 3. Evaluate all moves and choose the best
    best_score = float('-inf')
    best_moves = []
    
    for col in valid_moves:
        test_board = simulate_move(col, 1)
        if test_board is not None:
            my_score = evaluate_position(test_board, 1)
            opp_score = evaluate_position(test_board, -1)
            total_score = my_score - opp_score
            
            if total_score > best_score:
                best_score = total_score
                best_moves = [col]
            elif total_score == best_score:
                best_moves.append(col)
    
    # Prefer center among equally good moves
    if best_moves:
        center = cols // 2
        best_moves.sort(key=lambda c: abs(c - center))
        return best_moves[0]
    
    return random.choice(valid_moves)
