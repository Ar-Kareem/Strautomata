
def policy(board) -> str:
    import numpy as np
    from collections import deque
    
    def get_connected_components(board, player):
        """Count connected components for a player using 8-direction connectivity."""
        visited = set()
        components = 0
        pieces = [(r, c) for r in range(8) for c in range(8) if board[r][c] == player]
        
        if not pieces:
            return 0
        
        for start_r, start_c in pieces:
            if (start_r, start_c) in visited:
                continue
            
            components += 1
            queue = deque([(start_r, start_c)])
            visited.add((start_r, start_c))
            
            while queue:
                r, c = queue.popleft()
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == player:
                            if (nr, nc) not in visited:
                                visited.add((nr, nc))
                                queue.append((nr, nc))
        
        return components
    
    def get_legal_moves(board, player):
        """Generate all legal moves for the player."""
        moves = []
        
        for r in range(8):
            for c in range(8):
                if board[r][c] != player:
                    continue
                
                # Check all 8 directions
                for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                    # Count pieces in this line
                    count = 0
                    for dist in range(-7, 8):
                        nr, nc = r + dist * dr, c + dist * dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] != 0:
                            count += 1
                    
                    if count == 0:
                        continue
                    
                    # Try to move exactly 'count' squares
                    to_r, to_c = r + count * dr, c + count * dc
                    
                    if not (0 <= to_r < 8 and 0 <= to_c < 8):
                        continue
                    
                    if board[to_r][to_c] == player:
                        continue
                    
                    # Check if we can reach without jumping over enemy
                    can_move = True
                    for step in range(1, count):
                        check_r, check_c = r + step * dr, c + step * dc
                        if 0 <= check_r < 8 and 0 <= check_c < 8:
                            if board[check_r][check_c] == -player:
                                can_move = False
                                break
                    
                    if can_move:
                        moves.append((r, c, to_r, to_c))
        
        return moves
    
    def evaluate_move(board, move, player):
        """Evaluate the quality of a move."""
        r, c, to_r, to_c = move
        
        # Simulate the move
        new_board = board.copy()
        new_board[r][c] = 0
        new_board[to_r][to_c] = player
        
        # Check if this wins
        components = get_connected_components(new_board, player)
        if components == 1:
            return 1000000  # Winning move
        
        # Calculate center of mass
        my_pieces = [(r, c) for r in range(8) for c in range(8) if new_board[r][c] == player]
        if my_pieces:
            cm_r = sum(r for r, c in my_pieces) / len(my_pieces)
            cm_c = sum(c for r, c in my_pieces) / len(my_pieces)
            
            # Average distance to center of mass
            avg_dist = sum(abs(r - cm_r) + abs(c - cm_c) for r, c in my_pieces) / len(my_pieces)
        else:
            avg_dist = 100
        
        # Check if opponent can win next turn
        opp_moves = get_legal_moves(new_board, -player)
        for opp_move in opp_moves:
            opp_board = new_board.copy()
            or_, oc, oto_r, oto_c = opp_move
            opp_board[or_][oc] = 0
            opp_board[oto_r][oto_c] = -player
            if get_connected_components(opp_board, -player) == 1:
                return -1000000  # Opponent wins next
        
        # Bonus for capturing
        capture_bonus = 50 if board[to_r][to_c] == -player else 0
        
        # Score: prefer fewer components, smaller avg distance
        score = -components * 1000 - avg_dist * 10 + capture_bonus
        
        return score
    
    # Get all legal moves
    moves = get_legal_moves(board, 1)
    
    if not moves:
        # Fallback: return any piece move (shouldn't happen)
        for r in range(8):
            for c in range(8):
                if board[r][c] == 1:
                    return f"{r},{c}:{r},{c}"
    
    # Evaluate and select best move
    best_move = None
    best_score = float('-inf')
    
    for move in moves:
        score = evaluate_move(board, move, 1)
        if score > best_score:
            best_score = score
            best_move = move
    
    r, c, to_r, to_c = best_move
    return f"{r},{c}:{to_r},{to_c}"
