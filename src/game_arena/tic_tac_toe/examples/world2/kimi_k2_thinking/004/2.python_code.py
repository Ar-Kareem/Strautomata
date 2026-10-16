
def policy(board):
    """
    Smart policy for 4x4 Tic Tac Toe with optimal move prioritization:
    1. Win immediately
    2. Block opponent's win
    3. Create a fork (multiple threats)
    4. Block opponent's fork
    5. Best heuristic move (line value + positional control)
    """
    
    # Define all winning lines: 4 rows, 4 columns, 2 diagonals
    LINES = [
        # Rows
        [(0,0), (0,1), (0,2), (0,3)],
        [(1,0), (1,1), (1,2), (1,3)],
        [(2,0), (2,1), (2,2), (2,3)],
        [(3,0), (3,1), (3,2), (3,3)],
        # Columns
        [(0,0), (1,0), (2,0), (3,0)],
        [(0,1), (1,1), (2,1), (3,1)],
        [(0,2), (1,2), (2,2), (3,2)],
        [(0,3), (1,3), (2,3), (3,3)],
        # Diagonals
        [(0,0), (1,1), (2,2), (3,3)],
        [(0,3), (1,2), (2,1), (3,0)]
    ]
    
    # Map each cell to the indices of lines it belongs to
    CELL_LINES = {
        (0,0): [0,4,8], (0,1): [0,5], (0,2): [0,6], (0,3): [0,7,9],
        (1,0): [1,4], (1,1): [1,5,8,9], (1,2): [1,6,8,9], (1,3): [1,7],
        (2,0): [2,4], (2,1): [2,5,8,9], (2,2): [2,6,8,9], (2,3): [2,7],
        (3,0): [3,4,9], (3,1): [3,5], (3,2): [3,6], (3,3): [3,7,8]
    }
    
    # Positional scores: prioritize center, then corners, then edges
    POSITIONAL_SCORE = {
        (0,0): 30, (0,1): 10, (0,2): 10, (0,3): 30,
        (1,0): 10, (1,1): 50, (1,2): 50, (1,3): 10,
        (2,0): 10, (2,1): 50, (2,2): 50, (2,3): 10,
        (3,0): 30, (3,1): 10, (3,2): 10, (3,3): 30
    }
    
    def is_winning_move(move, player):
        """Check if playing at (r,c) would complete a line of 4 for player"""
        r, c = move
        for line_idx in CELL_LINES[(r,c)]:
            # Count player's marks in this line (excluding the move cell)
            count = sum(1 for rr, cc in LINES[line_idx] 
                       if (rr, cc) != (r, c) and board[rr][cc] == player)
            if count == 3:  # This move would be the 4th
                return True
        return False
    
    def count_threats(move, player):
        """
        Count lines that would have exactly 3 of player's marks and 1 empty
        after playing at move. A threat is a line that can be won next turn.
        """
        r, c = move
        opponent = -player
        threats = 0
        
        for line_idx in CELL_LINES[(r,c)]:
            player_count = 0
            empty_count = 0
            has_opponent = False
            
            for rr, cc in LINES[line_idx]:
                if (rr, cc) == (r, c):
                    continue
                val = board[rr][cc]
                if val == player:
                    player_count += 1
                elif val == 0:
                    empty_count += 1
                elif val == opponent:
                    has_opponent = True
            
            # After playing: player_count+1 marks, empty_count empties
            # Must be 3 marks and 1 empty to be a threat
            if not has_opponent and player_count == 2 and empty_count == 1:
                threats += 1
        
        return threats
    
    def evaluate_board():
        """Evaluate board state for player 1 using line completion scoring"""
        score = 0
        
        for line in LINES:
            ours = 0
            theirs = 0
            
            for r, c in line:
                cell = board[r][c]
                if cell == 1:
                    ours += 1
                elif cell == -1:
                    theirs += 1
            
            # Skip blocked lines (contain both players)
            if ours > 0 and theirs > 0:
                continue
            
            # Score open lines exponentially (0->1, 1->10, 2->100, 3->1000)
            if theirs == 0:
                score += 10 ** ours
            else:  # ours == 0, line is open for opponent
                score -= 10 ** theirs
        
        return score
    
    # Get all legal moves
    moves = [(r,c) for r in range(4) for c in range(4) if board[r][c] == 0]
    
    # 1. Win immediately if possible
    for move in moves:
        if is_winning_move(move, 1):
            return move
    
    # 2. Block opponent's winning move
    for move in moves:
        if is_winning_move(move, -1):
            return move
    
    # 3. Create a fork (2+ threats)
    best_fork = None
    max_threats = 0
    
    for move in moves:
        t = count_threats(move, 1)
        if t > max_threats:
            max_threats = t
            best_fork = move
    
    if max_threats >= 2:
        return best_fork
    
    # 4. Block opponent's fork
    opp_fork = None
    opp_max_threats = 0
    
    for move in moves:
        t = count_threats(move, -1)
        if t > opp_max_threats:
            opp_max_threats = t
            opp_fork = move
    
    if opp_max_threats >= 2:
        # Block by taking the fork cell
        return opp_fork
    
    # 5. Choose best move by heuristic evaluation
    best_move = moves[0]
    best_score = -float('inf')
    
    for move in moves:
        r, c = move
        # Temporarily make move and evaluate
        board[r][c] = 1
        score = evaluate_board()
        board[r][c] = 0  # Undo
        
        # Add positional bonus
        score += POSITIONAL_SCORE[move]
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
