
def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    """
    Smart policy for Phantom Tic Tac Toe that balances information gathering,
    winning threats, and strategic placement.
    """
    # Flatten board for easier access
    flat_board = [board[i][j] for i in range(3) for j in range(3)]
    
    # Convert to a set for fast lookup
    legal_set = set(legal_moves)
    
    # 1. Check for immediate win opportunities
    # We consider 0 cells as potentially empty for winning purposes
    def could_win_with_move(move):
        r, c = move // 3, move % 3
        # Temporarily assume this is our move
        temp_board = [row[:] for row in board]
        temp_board[r][c] = 1
        
        # Check all lines passing through (r,c)
        # Rows
        if all(temp_board[r][col] == 1 for col in range(3)):
            return True
        # Columns
        if all(temp_board[row][c] == 1 for row in range(3)):
            return True
        # Diagonals
        if r == c and all(temp_board[i][i] == 1 for i in range(3)):
            return True
        if r + c == 2 and all(temp_board[i][2-i] == 1 for i in range(3)):
            return True
        return False
    
    # 2. Check for opponent win threats (assuming 0 cells could be opponent)
    def could_opp_win_with_move(move):
        r, c = move // 3, move % 3
        # Temporarily assume this is opponent's cell
        temp_board = [row[:] for row in board]
        temp_board[r][c] = 2  # Mark as opponent
        
        # Check if opponent would have 3 in a row (considering existing 0 as potentially theirs)
        # This is heuristic: we only care about our 1's and this new placement
        # For a real block, we need to see if there are 2 other 0 cells in line
        for line in get_all_lines():
            cells = [(i, j) for i, j in line]
            if (r, c) not in cells:
                continue
            # Count our marks in this line
            our_count = sum(1 for i, j in cells if board[i][j] == 1)
            # If we have 2 marks, we win
            if our_count == 2:
                return True
        return False
    
    # Get all winning lines
    def get_all_lines():
        lines = []
        # Rows
        for i in range(3):
            lines.append([(i, 0), (i, 1), (i, 2)])
        # Columns
        for j in range(3):
            lines.append([(0, j), (1, j), (2, j)])
        # Diagonals
        lines.append([(0, 0), (1, 1), (2, 2)])
        lines.append([(0, 2), (1, 1), (2, 0)])
        return lines
    
    # Check if a move would complete a line for us
    def is_winning_move(move):
        r, c = move // 3, move % 3
        for line in get_all_lines():
            cells = [(i, j) for i, j in line]
            if (r, c) not in cells:
                continue
            # Count our marks in the line
            our_count = sum(1 for i, j in cells if board[i][j] == 1)
            # Count unknown cells in the line (0s)
            unknown_count = sum(1 for i, j in cells if board[i][j] == 0 and (i, j) != (r, c))
            # If we have 2 marks and 1 unknown (which could be empty), it's a winning move
            if our_count == 2 and unknown_count == 1:
                return True
            # If we have 1 mark and 2 unknowns, it's not a sure win
        return False
    
    # Check if a move would block an opponent's win
    # Opponent wins if they have 2 cells in a line and the third is 0
    def is_blocking_move(move):
        r, c = move // 3, move % 3
        for line in get_all_lines():
            cells = [(i, j) for i, j in line]
            if (r, c) not in cells:
                continue
            # Count our marks (we block them)
            our_count = sum(1 for i, j in cells if board[i][j] == 1)
            # Count unknown cells (opponent could have 2)
            unknown_count = sum(1 for i, j in cells if board[i][j] == 0 and (i, j) != (r, c))
            # If we have 0 marks and 2 unknowns, opponent could have 2, so we should block
            if our_count == 0 and unknown_count == 2:
                return True
        return False
    
    # 3. Scoring moves
    def score_move(move):
        score = 0
        r, c = move // 3, move % 3
        
        # Center bonus (highest strategic value)
        if r == 1 and c == 1:
            score += 10
        
        # Corner bonus
        elif (r, c) in [(0, 0), (0, 2), (2, 0), (2, 2)]:
            score += 8
        
        # Edge bonus
        else:
            score += 5
        
        # Winning move bonus (highest priority)
        if is_winning_move(move):
            score += 1000
        
        # Blocking move bonus (second priority)
        if is_blocking_move(move):
            score += 500
        
        # Information gathering bonus (for 0 cells)
        # We know 1 cells are ours, so 0 cells are unknown - exploring them gives info
        if board[r][c] == 0:
            score += 2
        
        return score
    
    # Score all legal moves
    best_score = -1
    best_move = None
    
    for move in legal_moves:
        r, c = move // 3, move % 3
        # Skip cells already confirmed as ours (shouldn't happen but just in case)
        if board[r][c] == 1:
            continue
            
        score = score_move(move)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    # Fallback: if no move found, return first legal move
    if best_move is None:
        best_move = legal_moves[0]
    
    # Convert to (row, col) format
    row = best_move // 3
    col = best_move % 3
    return row, col
