
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    Go playing policy for 19x19 board.
    Returns a move as (row, col) or (0, 0) to pass.
    """
    import numpy as np
    
    BOARD_SIZE = 19
    
    # Create board representation: 0=empty, 1=me, 2=opponent
    board = np.zeros((BOARD_SIZE + 1, BOARD_SIZE + 1), dtype=int)  # 1-indexed
    
    for r, c in me:
        board[r, c] = 1
    for r, c in opponent:
        board[r, c] = 2
    
    def get_neighbors(r, c):
        """Get valid neighboring coordinates."""
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + c
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                neighbors.append((nr, nc))
        return neighbors
    
    def get_liberties(r, c, player):
        """Get liberties of a stone/group at position."""
        visited = set()
        stack = [(r, c)]
        liberties = set()
        
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in visited:
                continue
            visited.add((cr, cc))
            
            for nr, nc in get_neighbors(cr, cc):
                if board[nr, nc] == 0:
                    liberties.add((nr, nc))
                elif board[nr, nc] == player and (nr, nc) not in visited:
                    stack.append((nr, nc))
        
        return liberties
    
    def get_group_at(r, c, player):
        """Get all stones in the group containing (r, c)."""
        if board[r, c] != player:
            return set()
        
        visited = set()
        stack = [(r, c)]
        group = set()
        
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in visited:
                continue
            visited.add((cr, cc))
            group.add((cr, cc))
            
            for nr, nc in get_neighbors(cr, cc):
                if board[nr, nc] == player and (nr, nc) not in visited:
                    stack.append((nr, nc))
        
        return group
    
    def is_suicidal(r, c, player):
        """Check if playing at (r, c) is suicidal (no liberties after move)."""
        board[r, c] = player
        # Check if move captures opponent stones first
        opponent_player = 3 - player
        for nr, nc in get_neighbors(r, c):
            if board[nr, nc] == opponent_player:
                opp_liberties = get_liberties(nr, nc, opponent_player)
                if len(opp_liberties) == 0:
                    board[r, c] = 0
                    return False
        
        # Check if our group has liberties
        my_liberties = get_liberties(r, c, player)
        board[r, c] = 0
        
        if len(my_liberties) == 0:
            return True
        return False
    
    def count_adjacent_stones(r, c, player):
        """Count adjacent stones of given player."""
        count = 0
        for nr, nc in get_neighbors(r, c):
            if board[nr, nc] == player:
                count += 1
        return count
    
    # Find all empty points
    empty_points = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r, c] == 0:
                empty_points.append((r, c))
    
    if not empty_points:
        return (0, 0)
    
    # Priority 1: Check for captures (opponent stones in atari)
    for r, c in empty_points:
        for nr, nc in get_neighbors(r, c):
            if board[nr, nc] == 2:  # opponent stone
                group = get_group_at(nr, nc, 2)
                liberties = set()
                for gr, gc in group:
                    for lr, lc in get_neighbors(gr, gc):
                        if board[lr, lc] == 0:
                            liberties.add((lr, lc))
                if len(liberties) == 1:
                    return (r, c)
    
    # Priority 2: Check for self-atari escape
    for r, c in me:
        group = get_group_at(r, c, 1)
        liberties = set()
        for gr, gc in group:
            for lr, lc in get_neighbors(gr, gc):
                if board[lr, lc] == 0:
                    liberties.add((lr, lc))
        if len(liberties) == 1:
            escape_move = list(liberties)[0]
            if not is_suicidal(escape_move[0], escape_move[1], 1):
                return escape_move
    
    # Priority 3: Check for self-atari with 2 liberties (approach move)
    for r, c in me:
        group = get_group_at(r, c, 1)
        liberties = set()
        for gr, gc in group:
            for lr, lc in get_neighbors(gr, gc):
                if board[lr, lc] == 0:
                    liberties.add((lr, lc))
        if len(liberties) == 2:
            for lib in liberties:
                if not is_suicidal(lib[0], lib[1], 1):
                    return lib
    
    # Priority 4: Evaluate and rank empty points
    scored_moves = []
    for r, c in empty_points:
        if is_suicidal(r, c, 1):
            continue
        
        score = 0
        
        # Corner bonus (corners are most valuable)
        corner_bonus = 0
        if r <= 3 and c <= 3:  # Top-left corner region
            corner_bonus = 30 - (r + c) * 2
        elif r <= 3 and c >= BOARD_SIZE - 2:  # Top-right corner region
            corner_bonus = 30 - (r + (BOARD_SIZE - c + 1)) * 2
        elif r >= BOARD_SIZE - 2 and c <= 3:  # Bottom-left corner region
            corner_bonus = 30 - ((BOARD_SIZE - r + 1) + c) * 2
        elif r >= BOARD_SIZE - 2 and c >= BOARD_SIZE - 2:  # Bottom-right corner region
            corner_bonus = 30 - ((BOARD_SIZE - r + 1) + (BOARD_SIZE - c + 1)) * 2
        score += corner_bonus
        
        # Proximity to our stones (extension/connection)
        my_adjacent = count_adjacent_stones(r, c, 1)
        if my_adjacent > 0:
            score += my_adjacent * 5
        
        # Proximity to opponent stones (influence/counter)
        opp_adjacent = count_adjacent_stones(r, c, 2)
        if opp_adjacent > 0:
            score += opp_adjacent * 3
        
        # Center control (tengen potential)
        center_distance = abs(r - 10) + abs(c - 10)
        score += (20 - center_distance) * 0.5
        
        # Joseki patterns (common opening moves)
        joseki_moves = [
            (4, 4), (4, 16), (16, 4), (16, 16),  # 4-4 points
            (4, 3), (4, 5), (16, 3), (16, 5),    # 3-4 points  
            (3, 4), (5, 4), (3, 16), (5, 16),    # 4-3 points
            (3, 3), (3, 17), (17, 3), (17, 17),  # 3-3 points
        ]
        if (r, c) in joseki_moves:
            score += 10
        
        scored_moves.append((score, r, c))
    
    if not scored_moves:
        return (0, 0)
    
    # Sort by score (descending) and return best move
    scored_moves.sort(reverse=True)
    return (scored_moves[0][1], scored_moves[0][2])
