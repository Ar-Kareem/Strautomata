
def policy(board) -> str:
    import numpy as np
    from collections import deque
    
    def get_line_count(board, row, col, dr, dc):
        """Count total pieces in a line direction."""
        count = 0
        for i in range(8):
            r, c = row + dr * i, col + dc * i
            if 0 <= r < 8 and 0 <= c < 8 and board[r][c] != 0:
                count += 1
        for i in range(1, 8):
            r, c = row - dr * i, col - dc * i
            if 0 <= r < 8 and 0 <= c < 8 and board[r][c] != 0:
                count += 1
        return count
    
    def is_valid_move(board, r1, c1, r2, c2):
        """Check if move is valid according to LoA rules."""
        if board[r1][c1] != 1:
            return False
        if not (0 <= r2 < 8 and 0 <= c2 < 8):
            return False
        if board[r2][c2] == 1:
            return False
        
        dr = 0 if r2 == r1 else (1 if r2 > r1 else -1)
        dc = 0 if c2 == c1 else (1 if c2 > c1 else -1)
        
        if dr == 0 and dc == 0:
            return False
        
        dist = max(abs(r2 - r1), abs(c2 - c1))
        line_count = get_line_count(board, r1, c1, dr, dc)
        
        if dist != line_count:
            return False
        
        # Check for jumping over enemy pieces
        for i in range(1, dist):
            r, c = r1 + dr * i, c1 + dc * i
            if board[r][c] == -1:
                return False
        
        return True
    
    def get_legal_moves(board):
        """Generate all legal moves."""
        moves = []
        for r1 in range(8):
            for c1 in range(8):
                if board[r1][c1] == 1:
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            line_count = get_line_count(board, r1, c1, dr, dc)
                            r2, c2 = r1 + dr * line_count, c1 + dc * line_count
                            if is_valid_move(board, r1, c1, r2, c2):
                                moves.append((r1, c1, r2, c2))
        return moves
    
    def is_connected(board, player=1):
        """Check if all player pieces are connected."""
        pieces = [(r, c) for r in range(8) for c in range(8) if board[r][c] == player]
        if not pieces:
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
        """Evaluate board position for current player."""
        pieces = [(r, c) for r in range(8) for c in range(8) if board[r][c] == 1]
        if not pieces:
            return -1000
        
        if is_connected(board, 1):
            return 10000
        
        # Compactness: smaller bounding box is better
        rows = [r for r, c in pieces]
        cols = [c for r, c in pieces]
        bbox_area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
        
        # Center of mass
        center_r = sum(rows) / len(pieces)
        center_c = sum(cols) / len(pieces)
        
        # Average distance from center
        avg_dist = sum(abs(r - center_r) + abs(c - center_c) for r, c in pieces) / len(pieces)
        
        # Connectivity estimate via BFS components
        visited = set()
        components = 0
        for piece in pieces:
            if piece not in visited:
                components += 1
                queue = deque([piece])
                visited.add(piece)
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
        
        score = -bbox_area * 2 - avg_dist * 5 - components * 100
        return score
    
    # Get all legal moves
    moves = get_legal_moves(board)
    
    if not moves:
        # Fallback - should not happen with legal positions
        for r in range(8):
            for c in range(8):
                if board[r][c] == 1:
                    return f"{r},{c}:{r},{c}"
    
    # Evaluate each move
    best_move = moves[0]
    best_score = -float('inf')
    
    for r1, c1, r2, c2 in moves:
        # Simulate move
        new_board = board.copy()
        new_board[r2][c2] = new_board[r1][c1]
        new_board[r1][c1] = 0
        
        # Check for immediate win
        if is_connected(new_board, 1):
            return f"{r1},{c1}:{r2},{c2}"
        
        score = evaluate_position(new_board)
        
        if score > best_score:
            best_score = score
            best_move = (r1, c1, r2, c2)
    
    r1, c1, r2, c2 = best_move
    return f"{r1},{c1}:{r2},{c2}"
