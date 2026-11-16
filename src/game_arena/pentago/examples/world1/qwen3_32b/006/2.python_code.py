
def policy(you, opponent) -> str:
    from copy import deepcopy

    def quad_to_coords(quad):
        if quad == 0:
            return (0, 0)
        elif quad == 1:
            return (0, 3)
        elif quad == 2:
            return (3, 0)
        elif quad == 3:
            return (3, 3)

    def rotate_quadrant(original_quad, direction):
        rotated = [[0]*3 for _ in range(3)]
        for new_x in range(3):
            for new_y in range(3):
                if direction == 'R':
                    original_x = (2 - new_y)
                    original_y = new_x
                else:
                    original_x = new_y
                    original_y = (2 - new_x)
                rotated[new_x][new_y] = original_quad[original_x][original_y]
        return rotated

    def check_win(board):
        for r in range(6):
            for c in range(2):
                if sum(board[r][c:c+5]) >= 5:
                    return True
        for c in range(6):
            for r in range(2):
                total = 0
                for i in range(5):
                    total += board[r+i][c]
                if total >=5:
                    return True
        for r in range(2):
            for c in range(2):
                total = 0
                for i in range(5):
                    total += board[r+i][c+i]
                if total >=5:
                    return True
        for r in range(2):
            for c in range(4, 6):
                total = 0
                for i in range(5):
                    total += board[r+i][c-i]
                if total >=5:
                    return True
        return False

    def get_legal_moves():
        moves = []
        for r in range(6):
            for c in range(6):
                if you[r][c] == 0 and opponent[r][c] == 0:
                    for quad in range(4):
                        for d in ['L', 'R']:
                            moves.append((r, c, quad, d))
        return moves

    legal_moves = get_legal_moves()

    # 1. Immediate win check
    for move in legal_moves:
        r_move, c_move, quad_move, dir_move = move
        new_you = [row[:] for row in you]
        new_opp = [row[:] for row in opponent]
        new_you[r_move][c_move] = 1
        sr, sc = quad_to_coords(quad_move)
        for board in [new_you, new_opp]:
            orig_quad = [[board[sr+x][sc+y] for y in range(3)] for x in range(3)]
            rotated = rotate_quadrant(orig_quad, dir_move)
            for x in range(3):
                for y in range(3):
                    board[sr+x][sc+y] = rotated[x][y]
        if check_win(new_you):
            return f"{r_move+1},{c_move+1},{quad_move},{dir_move}"
    
    # 2. Block opponent win
    def is_opponent_win_after(move):
        r_move, c_move, quad_move, dir_move = move
        new_you = [row[:] for row in you]
        new_opp = [row[:] for row in opponent]
        new_you[r_move][c_move] = 1
        sr, sc = quad_to_coords(quad_move)
        for board in [new_you, new_opp]:
            orig_quad = [[board[sr+x][sc+y] for y in range(3)] for x in range(3)]
            rotated = rotate_quadrant(orig_quad, dir_move)
            for x in range(3):
                for y in range(3):
                    board[sr+x][sc+y] = rotated[x][y]
        empty_cells = [(r, c) for r in range(6) for c in range(6) if new_you[r][c]==0 and new_opp[r][c]==0]
        for er, ec in empty_cells:
            for o_quad in range(4):
                for od in ['L', 'R']:
                    sim_you = [row[:] for row in new_you]
                    sim_opp = [row[:] for row in new_opp]
                    sim_opp[er][ec] = 1
                    osr, osc = quad_to_coords(o_quad)
                    for b in [sim_you, sim_opp]:
                        oquad = [[b[osr+x][osc+y] for y in range(3)] for x in range(3)]
                        rot = rotate_quadrant(oquad, od)
                        for x in range(3):
                            for y in range(3):
                                b[osr+x][osc+y] = rot[x][y]
                    if check_win(sim_opp):
                        return True
        return False

    safe_moves = []
    for move in legal_moves:
        if not is_opponent_win_after(move):
            safe_moves.append(move)
    if safe_moves:
        legal_moves = safe_moves
    
    # 3. Heuristic evaluation
    def evaluate(board):
        score = 0
        directions = [(0,1), (1,0), (1,1), (1,-1)]
        for dr, dc in directions:
            for r in range(6):
                for c in range(6):
                    valid = all(0 <= r + dr*i <6 and 0 <= c + dc*i <6 for i in range(4))
                    if not valid:
                        continue
                    count = sum(board[r+dr*i][c+dc*i] for i in range(4))
                    if count == 4:
                        score += 100
                    elif count == 3:
                        score += 10
                    elif count == 2:
                        score += 1
        return score

    best_score = -1
    best_move = legal_moves[0]
    for move in legal_moves:
        r_move, c_move, quad_move, dir_move = move
        new_you = [row[:] for row in you]
        new_opp = [row[:] for row in opponent]
        new_you[r_move][c_move] = 1
        sr, sc = quad_to_coords(quad_move)
        for board in [new_you, new_opp]:
            orig_quad = [[board[sr+x][sc+y] for y in range(3)] for x in range(3)]
            rotated = rotate_quadrant(orig_quad, dir_move)
            for x in range(3):
                for y in range(3):
                    board[sr+x][sc+y] = rotated[x][y]
        current_score = evaluate(new_you)
        if current_score > best_score:
            best_score = current_score
            best_move = move

    r, c, quad, direction = best_move
    return f"{r+1},{c+1},{quad},{direction}"
