
def policy(you: list[int], opponent: list[int]) -> str:
    import numpy as np
    
    # Convert to numpy arrays for easier manipulation
    you_arr = np.array(you)
    opp_arr = np.array(opponent)
    
    # Directions: (row_change, col_change, direction_char)
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    
    def get_legal_moves(board, opp_board):
        """Get all legal moves for current player."""
        moves = []
        for r in range(5):
            for c in range(6):
                if board[r, c] == 1:
                    for dr, dc, dchar in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 5 and 0 <= nc < 6:
                            if opp_board[nr, nc] == 1:
                                moves.append((r, c, dchar))
        return moves
    
    def simulate_move(board, opp_board, move):
        """Simulate a move and return resulting boards."""
        r, c, dchar = move
        dr, dc = {'U': (-1, 0), 'R': (0, 1), 'D': (1, 0), 'L': (0, -1)}[dchar]
        nr, nc = r + dr, c + dc
        
        new_board = board.copy()
        new_opp = opp_board.copy()
        
        # Move piece: capture opponent
        new_board[r, c] = 0
        new_board[nr, nc] = 1
        new_opp[nr, nc] = 0
        
        return new_board, new_opp
    
    def evaluate_position(my_board, opp_board, just_moved_piece_pos=None):
        """
        Evaluate the position from current player's perspective.
        Returns a score where higher is better.
        """
        # Get moves for both players
        my_moves = get_legal_moves(my_board, opp_board)
        opp_moves = get_legal_moves(opp_board, my_board)
        
        # If opponent has no moves, we win!
        if len(opp_moves) == 0:
            return float('inf')
        
        # If we have no moves, we lose
        if len(my_moves) == 0:
            return float('-inf')
        
        # Base evaluation: move advantage
        score = len(my_moves) - len(opp_moves) * 1.5
        
        # Piece safety: check if moved piece can be recaptured
        if just_moved_piece_pos:
            mr, mc = just_moved_piece_pos
            safe = True
            for dr, dc, _ in directions:
                nr, nc = mr + dr, mc + dc
                if 0 <= nr < 5 and 0 <= nc < 6:
                    if opp_board[nr, nc] == 1:
                        # Can opponent recapture?
                        # Check if that opponent piece has alternatives
                        can_recapture = False
                        for dr2, dc2, _ in directions:
                            nnr, nnc = nr + dr2, nc + dc2
                            if 0 <= nnr < 5 and 0 <= nnc < 6:
                                if my_board[nnr, nnc] == 1 and not (nnr == mr and nnc == mc):
                                    can_recapture = True
                                    break
                        if not can_recapture:
                            # Opponent must recapture, which might be bad for them
                            score += 2
                        else:
                            # Piece can be recaptured
                            safe = False
                            score -= 3
            
            if safe:
                score += 2
        
        # Center control: pieces in center are more valuable
        center_bonus = 0
        for r in range(5):
            for c in range(6):
                if my_board[r, c] == 1:
                    # Manhattan distance from center (2, 2.5)
                    dist = abs(r - 2) + abs(c - 2.5)
                    center_bonus += (3.5 - dist) * 0.1
        score += center_bonus
        
        # Piece count advantage
        my_count = np.sum(my_board)
        opp_count = np.sum(opp_board)
        score += (my_count - opp_count) * 0.5
        
        # Edge penalty: pieces on edges are more vulnerable
        edge_penalty = 0
        for r in range(5):
            for c in range(6):
                if my_board[r, c] == 1:
                    if r == 0 or r == 4 or c == 0 or c == 5:
                        edge_penalty -= 0.1
        score += edge_penalty
        
        return score
    
    # Get all legal moves
    legal_moves = get_legal_moves(you_arr, opp_arr)
    
    if not legal_moves:
        # No legal moves - should not happen as we lose, but must return something
        return "0,0,U"  # Invalid but required
    
    # Evaluate each move
    best_score = float('-inf')
    best_move = legal_moves[0]
    
    for move in legal_moves:
        # Simulate the move
        new_you, new_opp = simulate_move(you_arr, opp_arr, move)
        
        # Get the position of the moved piece
        r, c, dchar = move
        dr, dc = {'U': (-1, 0), 'R': (0, 1), 'D': (1, 0), 'L': (0, -1)}[dchar]
        new_pos = (r + dr, c + dc)
        
        # Evaluate the resulting position
        score = evaluate_position(new_you, new_opp, new_pos)
        
        # Bonus for moves that capture pieces with fewer options
        r, c, dchar = move
        dr, dc = {'U': (-1, 0), 'R': (0, 1), 'D': (1, 0), 'L': (0, -1)}[dchar]
        nr, nc = r + dr, c + dc
        
        # Count opponent's moves from captured piece's original position
        # (before capture, it had limited moves since we could capture it)
        opp_moves_before = 0
        for dr2, dc2, _ in directions:
            nnr, nnc = nr + dr2, nc + dc2
            if 0 <= nnr < 5 and 0 <= nnc < 6:
                if you_arr[nnr, nnc] == 1:
                    opp_moves_before += 1
        score -= opp_moves_before * 0.2  # Prefer capturing pieces with fewer escape options
        
        if score > best_score:
            best_score = score
            best_move = move
    
    # Return the best move
    r, c, dchar = best_move
    return f"{r},{c},{dchar}"
