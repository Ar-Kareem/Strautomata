
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_line_win(line, player):
        """Check if a line has 3 of player's pieces and 1 empty spot"""
        count_player = line.count(player)
        count_empty = line.count(0)
        return count_player == 3 and count_empty == 1
    
    def find_winning_move(board, player):
        """Find a move that wins the game for the given player"""
        # Check all empty positions
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    # Temporarily place the piece
                    board[i][j] = player
                    
                    # Check if this creates a win
                    if is_winning_position(board, i, j, player):
                        board[i][j] = 0  # Undo
                        return (i, j)
                    
                    board[i][j] = 0  # Undo
        return None
    
    def is_winning_position(board, row, col, player):
        """Check if the last move at (row, col) creates a winning line"""
        # Check row
        if all(board[row][c] == player for c in range(4)):
            return True
        
        # Check column
        if all(board[r][col] == player for r in range(4)):
            return True
        
        # Check main diagonal (top-left to bottom-right)
        if row == col:
            if all(board[i][i] == player for i in range(4)):
                return True
        
        # Check anti-diagonal (top-right to bottom-left)
        if row + col == 3:
            if all(board[i][3-i] == player for i in range(4)):
                return True
        
        return False
    
    def make_strategic_move(board):
        """Make the best strategic move"""
        # Priority order: center, corners, edges
        center_positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
        corner_positions = [(0, 0), (0, 3), (3, 0), (3, 3)]
        edge_positions = [(0, 1), (0, 2), (1, 0), (1, 3), 
                         (2, 0), (2, 3), (3, 1), (3, 2)]
        
        # Try center positions first
        for pos in center_positions:
            if board[pos[0]][pos[1]] == 0:
                return pos
        
        # Try corners
        for pos in corner_positions:
            if board[pos[0]][pos[1]] == 0:
                return pos
        
        # Try edges
        for pos in edge_positions:
            if board[pos[0]][pos[1]] == 0:
                return pos
        
        # Fallback: find any empty position
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    return (i, j)
    
    # Strategy: Win > Block > Strategic
    
    # 1. Check if I can win immediately
    win_move = find_winning_move(board, 1)
    if win_move:
        return win_move
    
    # 2. Check if I need to block opponent from winning
    block_move = find_winning_move(board, -1)
    if block_move:
        return block_move
    
    # 3. Make strategic move
    return make_strategic_move(board)
