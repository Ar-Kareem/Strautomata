
def policy(state: list[list[object]], role: str) -> str:
    # Initialize 3x3 board (None represents empty)
    board = [[None for _ in range(3)] for _ in range(3)]
    
    # Parse state propositions
    for prop in state:
        if isinstance(prop, (list, tuple)) and len(prop) >= 4 and prop[0] == "cell":
            try:
                r = int(prop[1]) - 1
                c = int(prop[2]) - 1
                mark = prop[3]
                if 0 <= r < 3 and 0 <= c < 3:
                    if mark != "b":
                        board[r][c] = mark
            except (ValueError, IndexError):
                continue
    
    opponent = "o" if role == "x" else "x"
    
    # Winning lines (rows, cols, diagonals)
    lines = [
        [(0,0),(0,1),(0,2)], [(1,0),(1,1),(1,2)], [(2,0),(2,1),(2,2)],  # rows
        [(0,0),(1,0),(2,0)], [(0,1),(1,1),(2,1)], [(0,2),(1,2),(2,2)],  # cols
        [(0,0),(1,1),(2,2)], [(0,2),(1,1),(2,0)]                       # diagonals
    ]
    
    def is_winner(b, player):
        """Check if player has won on board b"""
        for line in lines:
            if all(b[r][c] == player for r, c in line):
                return True
        return False
    
    # Find empty cells
    empties = [(r, c) for r in range(3) for c in range(3) if board[r][c] is None]
    
    # 1. Check for immediate winning move
    for r, c in empties:
        board[r][c] = role
        if is_winner(board, role):
            return f"mark({r+1},{c+1})"
        board[r][c] = None
    
    # 2. Check for immediate block (opponent win)
    for r, c in empties:
        board[r][c] = opponent
        if is_winner(board, opponent):
            board[r][c] = None
            return f"mark({r+1},{c+1})"
        board[r][c] = None
    
    # 3. Minimax for optimal play
    def minimax(b, depth, is_maximizing):
        # Terminal checks
        if is_winner(b, role):
            return 10 - depth
        if is_winner(b, opponent):
            return depth - 10
        
        # Find remaining moves
        moves = [(r, c) for r in range(3) for c in range(3) if b[r][c] is None]
        if not moves:
            return 0
        
        if is_maximizing:
            best_score = -1000
            for r, c in moves:
                b[r][c] = role
                score = minimax(b, depth + 1, False)
                b[r][c] = None
                best_score = max(best_score, score)
            return best_score
        else:
            best_score = 1000
            for r, c in moves:
                b[r][c] = opponent
                score = minimax(b, depth + 1, True)
                b[r][c] = None
                best_score = min(best_score, score)
            return best_score
    
    best_move = None
    best_score = -1000
    
    for r, c in empties:
        board[r][c] = role
        score = minimax(board, 0, False)  # After our move, it's opponent's turn (minimizing)
        board[r][c] = None
        if score > best_score:
            best_score = score
            best_move = (r, c)
            if score == 10:  # Found a winning line, can't do better
                break
    
    if best_move:
        return f"mark({best_move[0]+1},{best_move[1]+1})"
    
    # Fallback (should never reach here in a legal state)
    return "mark(1,1)"
