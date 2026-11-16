
def policy(you, opponent):
    board = [[0]*6 for _ in range(6)]
    for i in range(6):
        for j in range(6):
            if you[i][j] == 1:
                board[i][j] = 1
            elif opponent[i][j] == 1:
                board[i][j] = -1

    best_score = -20000
    best_move = None

    for r in range(6):
        for c in range(6):
            if you[r][c] == 0 and opponent[r][c] == 0:
                for quad in range(4):
                    for dir in ['L', 'R']:
                        new_board = [row[:] for row in board]
                        new_board[r][c] = 1
                        rotate_board(new_board, quad, dir)
                        
                        win_us = check_win(new_board, 1)
                        win_opp = check_win(new_board, -1)
                        
                        if win_us:
                            return f"{r+1},{c+1},{quad},{dir}"
                        if win_opp:
                            score = -20000
                        else:
                            score = heuristic_score(new_board)
                        
                        if score > best_score:
                            best_score = score
                            best_move = (r+1, c+1, quad, dir)
                            
    if best_move is None:
        return "1,1,0,L"  # Fallback move, though should not happen
    return f"{best_move[0]},{best_move[1]},{best_move[2]},{best_move[3]}"

def rotate_board(board, quad, dir):
    if quad == 0:
        r0, c0 = 0, 0
    elif quad == 1:
        r0, c0 = 0, 3
    elif quad == 2:
        r0, c0 = 3, 0
    elif quad == 3:
        r0, c0 = 3, 3
    else:
        return
    
    block = [board[r0+i][c0:c0+3] for i in range(3)]
    
    if dir == 'R':
        new_block = [list(row) for row in zip(*block[::-1])]
    elif dir == 'L':
        new_block = [list(row) for row in zip(*block)][::-1]
    else:
        return
    
    for i in range(3):
        for j in range(3):
            board[r0+i][c0+j] = new_block[i][j]

def check_win(board, player):
    for i in range(6):
        for j in range(0, 2):
            if all(board[i][j+k] == player for k in range(5)):
                return True
                
    for j in range(6):
        for i in range(0, 2):
            if all(board[i+k][j] == player for k in range(5)):
                return True
                
    for i in range(0, 2):
        for j in range(0, 2):
            if all(board[i+k][j+k] == player for k in range(5)):
                return True
                
    for i in range(0, 2):
        for j in range(4, 6):
            if all(board[i+k][j-k] == player for k in range(5)):
                return True
                
    return False

def heuristic_score(board):
    score = 0
    for i in range(6):
        for j in range(0, 2):
            line = [board[i][j+k] for k in range(5)]
            our = sum(1 for x in line if x == 1)
            opp = sum(1 for x in line if x == -1)
            if our == 4:
                score += 100
            if our == 3:
                score += 10
            if opp == 4:
                score -= 100
            if opp == 3:
                score -= 10
                
    for j in range(6):
        for i in range(0, 2):
            line = [board[i+k][j] for k in range(5)]
            our = sum(1 for x in line if x == 1)
            opp = sum(1 for x in line if x == -1)
            if our == 4:
                score += 100
            if our == 3:
                score += 10
            if opp == 4:
                score -= 100
            if opp == 3:
                score -= 10
                
    for i in range(0, 2):
        for j in range(0, 2):
            line = [board[i+k][j+k] for k in range(5)]
            our = sum(1 for x in line if x == 1)
            opp = sum(1 for x in line if x == -1)
            if our == 4:
                score += 100
            if our == 3:
                score += 10
            if opp == 4:
                score -= 100
            if opp == 3:
                score -= 10
                
    for i in range(0, 2):
        for j in range(4, 6):
            line = [board[i+k][j-k] for k in range(5)]
            our = sum(1 for x in line if x == 1)
            opp = sum(1 for x in line if x == -1)
            if our == 4:
                score += 100
            if our == 3:
                score += 10
            if opp == 4:
                score -= 100
            if opp == 3:
                score -= 10
                
    return score
