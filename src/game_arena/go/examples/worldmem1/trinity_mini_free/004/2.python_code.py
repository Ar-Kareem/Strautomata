
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Precompute position scores (center is highest)
    position_score = [[0.0] * 19 for _ in range(19)]
    for i in range(19):
        for j in range(19):
            dist = abs(i - 9) + abs(j - 9)
            position_score[i][j] = 1.0 - dist / 18.0
    
    # Initialize board and mark stones
    board = [[0] * 19 for _ in range(19)]
    for stone in me:
        board[stone[0]-1][stone[1]-1] = 1
    for stone in opponent:
        board[stone[0]-1][stone[1]-1] = 2
    
    best_move = None
    best_score = -float('inf')
    
    # Check all empty cells
    for i in range(19):
        for j in range(19):
            if board[i][j] != 0:
                continue
                
            # Place stone temporarily
            board[i][j] = 1
            group_liberties = 0
            captures = False
            
            # Check group liberties
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                ni, nj = i + dx, j + dy
                if 0 <= ni < 19 and 0 <= nj < 19 and board[ni][nj] == 0:
                    group_liberties += 1
            
            # Check captures
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                ni, nj = i + dx, j + dy
                if 0 <= ni < 19 and 0 <= nj < 19 and board[ni][nj] == 2:
                    # Check if opponent's stone has no liberties
                    opp_liberties = 0
                    for odx, ody in [(1,0), (-1,0), (0,1), (0,-1)]:
                        oni, onj = ni + odx, nj + ody
                        if 0 <= oni < 19 and 0 <= onj < 19 and board[oni][onj] == 0:
                            opp_liberties += 1
                    if opp_liberties == 0:
                        captures = True
            
            # Check legality
            if captures or group_liberties > 0:
                score = position_score[i][j] + group_liberties + (10 if captures else 0)
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
            
            # Revert board
            board[i][j] = 0
    
    # Return move or pass
    return (best_move[0]+1, best_move[1]+1) if best_move else (0, 0)
