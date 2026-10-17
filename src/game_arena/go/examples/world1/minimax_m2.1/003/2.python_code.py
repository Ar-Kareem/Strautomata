
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Create board representation: 0=empty, 1=me, -1=opponent
    board = [[0 for _ in range(19)] for _ in range(19)]
    for row, col in me:
        if 1 <= row <= 19 and 1 <= col <= 19:
            board[row-1][col-1] = 1
    for row, col in opponent:
        if 1 <= row <= 19 and 1 <= col <= 19:
            board[row-1][col-1] = -1
    
    # Helper functions
    def get_group_liberties(board_state, row, col, player):
        """Count liberties of a group containing (row, col) for given player"""
        if not (1 <= row <= 19 and 1 <= col <= 19):
            return 0
        if board_state[row-1][col-1] != player:
            return 0
        
        visited = set()
        stack = [(row-1, col-1)]
        liberties = 0
        group = []
        
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            group.append((r, c))
            
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19:
                    if board_state[nr-1][nc-1] == 0:
                        liberties += 1
                    elif board_state[nr-1][nc-1] == player and (nr, nc) not in visited:
                        stack.append((nr, nc))
        
        return liberties, set(group)
    
    def would_capture(board_state, opponent_list, move):
        """Check if placing stone at move would capture any opponent groups"""
        row, col = move
        temp_board = [row[:] for row in board_state]
        temp_board[row-1][col-1] = 1
        
        captures = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if temp_board[nr-1][nc-1] == -1:
                    liberties, group = get_group_liberties(temp_board, nr, nc, -1)
                    if liberties == 0:
                        for gr, gc in group:
                            if temp_board[gr][gc] != 0:
                                captures.append((gr+1, gc+1))
                                temp_board[gr][gc] = 0
        
        return len(captures) > 0, captures
    
    def would_be_in_atari(board_state, move):
        """Check if placing stone at move would result in atari (1 liberty)"""
        row, col = move
        if board_state[row-1][col-1] != 0:
            return False
        
        temp_board = [row[:] for row in board_state]
        temp_board[row-1][col-1] = 1
        
        liberties, _ = get_group_liberties(temp_board, row, col, 1)
        return liberties == 1
    
    def count_adjacent_stones(board_state, row, col, player):
        """Count adjacent stones of given player"""
        count = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if board_state[nr-1][nc-1] == player:
                    count += 1
        return count
    
    def evaluate_position(row, col):
        """Evaluate a position and return a score"""
        score = 0
        
        # Check if position is legal
        if board[row-1][col-1] != 0:
            return -float('inf')
        
        # Check for captures (highest priority)
        can_capture, captured = would_capture(board, opponent, (row, col))
        if can_capture:
            score += 1000 + len(captured) * 100
        
        # Check if move is self-atari (avoid unless capturing)
        if not can_capture and would_be_in_atari(board, (row, col)):
            score -= 500
        
        # Check if we're defending against capture
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if board[nr-1][nc-1] == 1:
                    liberties, group = get_group_liberties(board, nr, nc, 1)
                    if liberties <= 2:
                        score += 100 - liberties * 30
        
        # Build influence - prefer playing near our own stones
        adjacent_own = count_adjacent_stones(board, row, col, 1)
        adjacent_opp = count_adjacent_stones(board, row, col, -1)
        score += adjacent_own * 10
        score -= adjacent_opp * 5
        
        # Positional bonuses
        # Corner points are valuable (3-3, 4-4)
        if (row, col) in [(3, 3), (3, 17), (17, 3), (17, 17)]:
            score += 50
        # Side points
        if row in [3, 17] or col in [3, 17]:
            score += 20
        
        # Proximity to center (center is less valuable early game, more later)
        center_dist = abs(row - 10) + abs(col - 10)
        if center_dist > 5:  # Edge/center opening preference
            score += 5
        
        return score
    
    # Evaluate all legal moves
    best_move = (0, 0)  # Default pass
    best_score = -float('inf')
    
    for row in range(1, 20):
        for col in range(1, 20):
            if board[row-1][col-1] == 0:
                score = evaluate_position(row, col)
                if score > best_score:
                    best_score = score
                    best_move = (row, col)
    
    return best_move
