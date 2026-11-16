
def policy(board) -> str:
    import numpy as np
    from collections import deque
    
    def get_pieces(board, player):
        """Get all positions of player's pieces."""
        pieces = []
        for r in range(8):
            for c in range(8):
                if board[r][c] == player:
                    pieces.append((r, c))
        return pieces
    
    def count_line_pieces(board, row, col, dr, dc):
        """Count total pieces in a line direction."""
        count = 0
        for mult in range(-7, 8):
            r, c = row + mult * dr, col + mult * dc
            if 0 <= r < 8 and 0 <= c < 8 and board[r][c] != 0:
                count += 1
        return count
    
    def is_valid_move(board, from_r, from_c, to_r, to_c):
        """Check if a move is valid according to LOA rules."""
        if board[from_r][from_c] != 1:
            return False
        if not (0 <= to_r < 8 and 0 <= to_c < 8):
            return False
        if board[to_r][to_c] == 1:
            return False
        
        dr = 0 if to_r == from_r else (1 if to_r > from_r else -1)
        dc = 0 if to_c == from_c else (1 if to_c > from_c else -1)
        
        if dr == 0 and dc == 0:
            return False
        
        distance = max(abs(to_r - from_r), abs(to_c - from_c))
        line_count = count_line_pieces(board, from_r, from_c, dr, dc)
        
        if distance != line_count:
            return False
        
        # Check for enemy pieces blocking the path
        for step in range(1, distance):
            r, c = from_r + step * dr, from_c + step * dc
            if board[r][c] == -1:
                return False
        
        return True
    
    def get_legal_moves(board):
        """Generate all legal moves."""
        moves = []
        pieces = get_pieces(board, 1)
        
        for from_r, from_c in pieces:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                line_count = count_line_pieces(board, from_r, from_c, dr, dc)
                to_r, to_c = from_r + dr * line_count, from_c + dc * line_count
                
                if is_valid_move(board, from_r, from_c, to_r, to_c):
                    moves.append((from_r, from_c, to_r, to_c))
        
        return moves
    
    def is_connected(board, player):
        """Check if all player's pieces form a single connected component."""
        pieces = get_pieces(board, player)
        if len(pieces) <= 1:
            return True
        
        visited = set()
        queue = deque([pieces[0]])
        visited.add(pieces[0])
        
        while queue:
            r, c = queue.popleft()
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in pieces and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
        
        return len(visited) == len(pieces)
    
    def evaluate_position(board):
        """Evaluate the board position for player 1."""
        pieces = get_pieces(board, 1)
        
        if len(pieces) == 0:
            return -10000
        
        if is_connected(board, 1):
            return 10000
        
        # Calculate center of mass
        center_r = sum(r for r, c in pieces) / len(pieces)
        center_c = sum(c for r, c in pieces) / len(pieces)
        
        # Calculate spread (lower is better)
        spread = sum((r - center_r)**2 + (c - center_c)**2 for r, c in pieces)
        
        # Count connectivity
        connectivity = 0
        for r, c in pieces:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == 1:
                        connectivity += 1
        
        return connectivity * 10 - spread
    
    def apply_move(board, from_r, from_c, to_r, to_c):
        """Apply a move and return new board."""
        new_board = board.copy()
        new_board[to_r][to_c] = new_board[from_r][from_c]
        new_board[from_r][from_c] = 0
        return new_board
    
    # Get all legal moves
    moves = get_legal_moves(board)
    
    if not moves:
        # Fallback: return any syntactically valid move
        pieces = get_pieces(board, 1)
        if pieces:
            return f"{pieces[0][0]},{pieces[0][1]}:{pieces[0][0]},{pieces[0][1]}"
        return "0,0:0,0"
    
    # Evaluate each move
    best_move = None
    best_score = -float('inf')
    
    for move in moves:
        from_r, from_c, to_r, to_c = move
        new_board = apply_move(board, from_r, from_c, to_r, to_c)
        
        # Check for immediate win
        if is_connected(new_board, 1):
            return f"{from_r},{from_c}:{to_r},{to_c}"
        
        # Evaluate position
        score = evaluate_position(new_board)
        
        # Bonus for captures
        if board[to_r][to_c] == -1:
            score += 15
        
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move:
        from_r, from_c, to_r, to_c = best_move
        return f"{from_r},{from_c}:{to_r},{to_c}"
    
    # Fallback
    from_r, from_c, to_r, to_c = moves[0]
    return f"{from_r},{from_c}:{to_r},{to_c}"
