
def policy(you, opponent):
    # Generate all possible moves for the current player
    possible_moves = []
    for row in range(5):
        for col in range(6):
            if you[row][col]:
                for dr, dc, direction in [(-1, 0, 'U'), (1, 0, 'D'), (0, 1, 'R'), (0, -1, 'L')]:
                    new_row = row + dr
                    new_col = col + dc
                    if 0 <= new_row < 5 and 0 <= new_col < 6 and opponent[new_row][new_col]:
                        possible_moves.append((row, col, direction))
    
    # Check if any move immediately wins by leaving no moves for the opponent
    for move in possible_moves:
        r, c, d = move
        nr = r + (-1 if d == 'U' else 1 if d == 'D' else 0)
        nc = c + (1 if d == 'R' else -1 if d == 'L' else 0)
        
        new_you = [row[:] for row in you]
        new_opponent = [row[:] for row in opponent]
        new_you[r][c] = 0
        new_you[nr][nc] = 1
        new_opponent[nr][nc] = 0
        
        # Check if opponent has any moves left
        opponent_has_move = False
        for r2 in range(5):
            for c2 in range(6):
                if new_opponent[r2][c2]:
                    for dr2, dc2, _ in [(-1, 0, 'U'), (1, 0, 'D'), (0, 1, 'R'), (0, -1, 'L')]:
                        nr2 = r2 + dr2
                        nc2 = c2 + dc2
                        if 0 <= nr2 < 5 and 0 <= nc2 < 6 and new_you[nr2][nc2]:
                            opponent_has_move = True
                            break
                    if opponent_has_move:
                        break
            if opponent_has_move:
                break
        if not opponent_has_move:
            return f"{r},{c},{d}"
    
    # Evaluate each move by the minimal moves the opponent has afterward
    best_move = possible_moves[0]
    best_score = float('inf')
    
    for move in possible_moves:
        r, c, d = move
        # Apply the move to get new board states
        new_you = [row[:] for row in you]
        new_opponent = [row[:] for row in opponent]
        new_you[r][c] = 0
        if d == 'U':
            nr, nc = r - 1, c
        elif d == 'D':
            nr, nc = r + 1, c
        elif d == 'R':
            nr, nc = r, c + 1
        elif d == 'L':
            nr, nc = r, c - 1
        new_you[nr][nc] = 1
        new_opponent[nr][nc] = 0
        
        # Generate all opponent's possible moves
        opp_moves_count = 0
        for r2 in range(5):
            for c2 in range(6):
                if new_opponent[r2][c2]:
                    for dr2, dc2, _ in [(-1, 0, 'U'), (1, 0, 'D'), (0, 1, 'R'), (0, -1, 'L')]:
                        nr2 = r2 + dr2
                        nc2 = c2 + dc2
                        if 0 <= nr2 < 5 and 0 <= nc2 < 6 and new_you[nr2][nc2]:
                            opp_moves_count += 1
                            break
        if opp_moves_count < best_score:
            best_score = opp_moves_count
            best_move = move
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
