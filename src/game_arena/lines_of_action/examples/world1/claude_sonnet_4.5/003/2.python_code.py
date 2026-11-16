
def policy(board) -> str:
    import numpy as np
    from collections import deque
    
    def get_pieces(board, player):
        """Get all positions of pieces for a player."""
        pieces = []
        for r in range(8):
            for c in range(8):
                if board[r][c] == player:
                    pieces.append((r, c))
        return pieces
    
    def count_line(board, r, c, dr, dc):
        """Count pieces in a line (row/col/diagonal) through position (r,c)."""
        count = 0
        # Count in both directions
        for direction in [1, -1]:
            nr, nc = r + direction * dr, c + direction * dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                if board[nr][nc] != 0:
                    count += 1
                nr += direction * dr
                nc += direction * dc
        # Add current position if occupied
        if board[r][c] != 0:
            count += 1
        return count
    
    def is_path_clear(board, r, c, dr, dc, dist, player):
        """Check if path is clear (can jump friendly, not enemy)."""
        for step in range(1, abs(dist)):
            nr = r + step * (1 if dist > 0 else -1) * dr
            nc = c + step * (1 if dist > 0 else -1) * dc
            if board[nr][nc] == -player:  # Enemy piece blocks
                return False
        return True
    
    def get_legal_moves(board, player):
        """Generate all legal moves for the player."""
        moves = []
        pieces = get_pieces(board, player)
        
        for r, c in pieces:
            # 8 directions: horizontal, vertical, and 4 diagonals
            directions = [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
            
            for dr, dc in directions:
                # Count pieces in this line
                line_count = count_line(board, r, c, dr, dc)
                
                # Try moving exactly line_count squares in this direction
                for sign in [1, -1]:
                    nr = r + sign * line_count * dr
                    nc = c + sign * line_count * dc
                    
                    # Check bounds
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        # Can't land on own piece
                        if board[nr][nc] != player:
                            # Check if path is clear
                            if is_path_clear(board, r, c, dr, dc, sign * line_count, player):
                                moves.append((r, c, nr, nc))
        
        return moves
    
    def is_connected(board, player):
        """Check if all player's pieces are connected."""
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
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        if (nr, nc) in pieces and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
        
        return len(visited) == len(pieces)
    
    def evaluate_position(board, player):
        """Evaluate board position for the player."""
        pieces = get_pieces(board, player)
        if len(pieces) == 0:
            return -10000
        
        # Check if won
        if is_connected(board, player):
            return 10000
        
        # Calculate center of mass
        cm_r = sum(r for r, c in pieces) / len(pieces)
        cm_c = sum(c for r, c in pieces) / len(pieces)
        
        # Compactness: average distance to center of mass
        compactness = -sum(abs(r - cm_r) + abs(c - cm_c) for r, c in pieces) / len(pieces)
        
        # Diameter: max distance between any two pieces
        max_dist = 0
        for i, (r1, c1) in enumerate(pieces):
            for r2, c2 in pieces[i+1:]:
                dist = max(abs(r1 - r2), abs(c1 - c2))
                max_dist = max(max_dist, dist)
        diameter = -max_dist * 2
        
        # Centralization: prefer pieces near board center
        centralization = -sum(abs(r - 3.5) + abs(c - 3.5) for r, c in pieces) / len(pieces)
        
        return diameter + compactness + centralization * 0.5
    
    def apply_move(board, r, c, nr, nc, player):
        """Apply a move and return new board."""
        new_board = board.copy()
        new_board[r][c] = 0
        new_board[nr][nc] = player
        return new_board
    
    # Main policy logic
    player = 1
    legal_moves = get_legal_moves(board, player)
    
    if not legal_moves:
        # Should not happen, but return a dummy move
        return "0,0:0,0"
    
    # Evaluate each move
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for r, c, nr, nc in legal_moves:
        new_board = apply_move(board, r, c, nr, nc, player)
        score = evaluate_position(new_board, player)
        
        # Bonus for captures
        if board[nr][nc] == -player:
            score += 5
        
        if score > best_score:
            best_score = score
            best_move = (r, c, nr, nc)
    
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
