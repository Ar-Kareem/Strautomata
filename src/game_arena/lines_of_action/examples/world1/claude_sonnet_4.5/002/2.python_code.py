
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
    
    def count_line(board, row, col, dr, dc):
        """Count total pieces in a line direction."""
        count = 0
        for r in range(8):
            for c in range(8):
                if dr != 0 and dc != 0:  # diagonal
                    if abs(r - row) == abs(c - col) and (r - row) * dc == (c - col) * dr:
                        if board[r][c] != 0:
                            count += 1
                elif dr != 0:  # vertical
                    if c == col and board[r][c] != 0:
                        count += 1
                elif dc != 0:  # horizontal
                    if r == row and board[r][c] != 0:
                        count += 1
        return count
    
    def is_valid_move(board, from_pos, to_pos):
        """Check if a move is valid according to LoA rules."""
        fr, fc = from_pos
        tr, tc = to_pos
        
        if board[fr][fc] != 1:
            return False
        if not (0 <= tr < 8 and 0 <= tc < 8):
            return False
        if (fr, fc) == (tr, tc):
            return False
        
        dr = 0 if tr == fr else (1 if tr > fr else -1)
        dc = 0 if tc == fc else (1 if tc > fc else -1)
        
        if dr == 0 and dc == 0:
            return False
        
        distance = max(abs(tr - fr), abs(tc - fc))
        line_count = count_line(board, fr, fc, dr, dc)
        
        if distance != line_count:
            return False
        
        # Check for jumping over enemy pieces
        r, c = fr + dr, fc + dc
        while (r, c) != (tr, tc):
            if board[r][c] == -1:
                return False
            r += dr
            c += dc
        
        # Can't land on own piece
        if board[tr][tc] == 1:
            return False
        
        return True
    
    def get_legal_moves(board):
        """Get all legal moves for current player."""
        moves = []
        pieces = get_pieces(board, 1)
        directions = [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
        
        for fr, fc in pieces:
            for dr, dc in directions:
                line_count = count_line(board, fr, fc, dr, dc)
                tr, tc = fr + dr * line_count, fc + dc * line_count
                if is_valid_move(board, (fr, fc), (tr, tc)):
                    moves.append((fr, fc, tr, tc))
        
        return moves
    
    def count_components(board, player):
        """Count connected components using BFS."""
        pieces = set(get_pieces(board, player))
        visited = set()
        components = 0
        
        for piece in pieces:
            if piece in visited:
                continue
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
        
        return components
    
    def evaluate_board(board):
        """Evaluate board state for current player."""
        my_pieces = get_pieces(board, 1)
        opp_pieces = get_pieces(board, -1)
        
        if len(my_pieces) == 0:
            return -10000
        
        my_components = count_components(board, 1)
        if my_components == 1:
            return 10000
        
        # Calculate compactness
        my_centroid = np.mean(my_pieces, axis=0)
        my_compactness = -np.mean([np.sum((np.array(p) - my_centroid)**2) for p in my_pieces])
        
        opp_components = count_components(board, -1) if len(opp_pieces) > 0 else 0
        
        score = -my_components * 1000 + my_compactness * 10 + opp_components * 100
        return score
    
    def apply_move(board, move):
        """Apply move and return new board."""
        new_board = board.copy()
        fr, fc, tr, tc = move
        new_board[tr][tc] = new_board[fr][fc]
        new_board[fr][fc] = 0
        return new_board
    
    # Get all legal moves
    moves = get_legal_moves(board)
    
    if not moves:
        # Should never happen, but return a dummy move
        pieces = get_pieces(board, 1)
        if pieces:
            return f"{pieces[0][0]},{pieces[0][1]}:{pieces[0][0]},{pieces[0][1]}"
        return "0,0:0,0"
    
    # Evaluate each move
    best_move = moves[0]
    best_score = -float('inf')
    
    for move in moves:
        new_board = apply_move(board, move)
        score = evaluate_board(new_board)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
