
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    """
    Clobber game policy for 5x6 grid.
    Returns best move as 'row,col,dir' string.
    """
    # Position values: corners are most valuable
    POS_VALUES = np.array([
        [3, 1, 1, 1, 1, 3],
        [1, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 1],
        [3, 1, 1, 1, 1, 3]
    ], dtype=int)
    
    # Direction vectors: (dr, dc, name)
    DIRS = [(-1, 0, 'U'), (1, 0, 'D'), (0, -1, 'L'), (0, 1, 'R')]
    
    # Build board representation: 0=empty, 1=our piece, 2=opp piece
    board = np.zeros((5, 6), dtype=np.uint8)
    for i in range(30):
        if you[i]:
            board[i//6, i%6] = 1
        elif opponent[i]:
            board[i//6, i%6] = 2
    
    def get_moves(board, player):
        """Get all legal moves for specified player."""
        moves = []
        opp = 3 - player
        for r in range(5):
            for c in range(6):
                if board[r, c] != player:
                    continue
                for dr, dc, dname in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 5 and 0 <= nc < 6 and board[nr, nc] == opp:
                        moves.append((r, c, dname))
        return moves
    
    def make_move(board, move):
        """Execute move, return new board and captured position."""
        r, c, d = move
        new_board = board.copy()
        
        # Find target coordinates based on direction
        for dr, dc, dname in DIRS:
            if dname == d:
                tr, tc = r + dr, c + dc
                break
        
        # Record capture position for bonus evaluation
        captured = (tr, tc) if board[tr, tc] == 2 else None
        
        # Execute capture: move our piece to target, clear source
        new_board[r, c] = 0
        new_board[tr, tc] = 1
        
        return new_board, captured
    
    def evaluate(board, captured=None):
        """
        Heuristic evaluation of board state.
        Higher score = better for us.
        """
        # Count mobilities for both players
        our_moves = len(get_moves(board, 1))
        opp_moves = len(get_moves(board, 2))
        
        # Terminal states
        if opp_moves == 0:
            return 10000  # Winning position
        if our_moves == 0:
            return -10000  # Losing position
        
        # Score components
        mobility = our_moves - opp_moves  # Most important
        material = np.sum(board == 1) - np.sum(board == 2)
        position = np.sum(POS_VALUES * (board == 1))
        capture_bonus = POS_VALUES[captured] if captured else 0
        
        # Weighted combination
        return 5 * mobility + 2 * material + position + 2 * capture_bonus
    
    # Get our legal moves
    legal_moves = get_moves(board, 1)
    
    if not legal_moves:
        # Fallback (should never happen in valid game state)
        return "0,0,R"
    
    # Find best move through heuristic evaluation
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for move in legal_moves:
        new_board, captured = make_move(board, move)
        score = evaluate(new_board, captured)
        
        # Immediate win takes absolute priority
        if score >= 10000:
            return f"{move[0]},{move[1]},{move[2]}"
        
        # Track highest scoring move
        if score > best_score:
            best_score = score
            best_move = move
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
