
def policy(you, opponent):
    # Helper function to count possible moves for a player
    def count_moves(board_you, board_opponent):
        moves = 0
        for r in range(5):
            for c in range(6):
                if board_you[r][c] == 1:
                    for dr, dc in [(-1,0), (0,1), (1,0), (0,-1)]:
                        nr = r + dr
                        nc = c + dc
                        if 0 <= nr < 5 and 0 <= nc < 6:
                            if board_opponent[nr][nc] == 1:
                                moves += 1
        return moves

    # Generate all valid moves
    moves = []
    for r in range(5):
        for c in range(6):
            if you[r][c] == 1:
                for dr, dc, dir_char in [(-1,0,'U'), (0,1,'R'), (1,0,'D'), (0,-1,'L')]:
                    nr = r + dr
                    nc = c + dc
                    if 0 <= nr < 5 and 0 <= nc < 6:
                        if opponent[nr][nc] == 1:
                            moves.append((r, c, dir_char))
    if not moves:
        return "0,0,U"  # Fallback (shouldn't occur in valid game state)
    
    best_move = None
    best_heuristic = -float('inf')
    for (r, c, dir_char) in moves:
        # Create copies of current board state
        new_you = [row[:] for row in you]
        new_opponent = [row[:] for row in opponent]
        
        # Determine destination coordinates
        dr, dc = {'U': (-1,0), 'R': (0,1), 'D': (1,0), 'L': (0,-1)}[dir_char]
        nr = r + dr
        nc = c + dc
        
        # Update board: capture opponent piece
        new_you[r][c] = 0
        new_you[nr][nc] = 1
        new_opponent[nr][nc] = 0
        
        # Calculate mobility difference
        your_moves = count_moves(new_you, new_opponent)
        opponent_moves = count_moves(opponent, new_you)
        heuristic = your_moves - opponent_moves
        
        # Select move with highest heuristic
        if heuristic > best_heuristic:
            best_heuristic = heuristic
            best_move = (r, c, dir_char)
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
