
def policy(state, role):
    board = {}
    for prop in state:
        if prop[0] == "cell":
            row, col, piece = int(prop[1]), int(prop[2]), prop[3]
            board[(row, col)] = piece
    
    opponent = "black" if role == "red" else "red"
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    def valid(r, c):
        return 1 <= r <= 4 and 1 <= c <= 4
    
    def pieces(color, b):
        return [(r, c) for (r, c), p in b.items() if p == color]
    
    def is_vulnerable(pos, b, my_color):
        r, c = pos
        opp = "black" if my_color == "red" else "red"
        for dr, dc in directions:
            adj_r, adj_c = r + dr, c + dc
            far_r, far_c = r + 2*dr, c + 2*dc
            if valid(adj_r, adj_c) and valid(far_r, far_c):
                if b.get((adj_r, adj_c)) == opp and b.get((far_r, far_c)) == opp:
                    return True
        return False
    
    def count_jumps(b, color):
        opp = "black" if color == "red" else "red"
        count = 0
        for r, c in pieces(color, b):
            for dr, dc in directions:
                mid_r, mid_c = r + dr, c + dc
                end_r, end_c = r + 2*dr, c + 2*dc
                if valid(mid_r, mid_c) and valid(end_r, end_c):
                    if b.get((mid_r, mid_c)) == color and b.get((end_r, end_c)) == opp:
                        count += 1
        return count
    
    def count_vulnerable(b, color):
        return sum(1 for pos in pieces(color, b) if is_vulnerable(pos, b, color))
    
    # Collect all jumps
    jumps = []
    for r, c in pieces(role, board):
        for dr, dc in directions:
            mid_r, mid_c = r + dr, c + dc
            end_r, end_c = r + 2*dr, c + 2*dc
            if valid(mid_r, mid_c) and valid(end_r, end_c):
                if board.get((mid_r, mid_c)) == role and board.get((end_r, end_c)) == opponent:
                    jumps.append((r, c, mid_r, mid_c, end_r, end_c))
    
    if jumps:
        def score_j(j):
            r, c, mid_r, mid_c, end_r, end_c = j
            new_board = board.copy()
            new_board[(r, c)] = "blank"
            new_board[(end_r, end_c)] = role
            s = 100
            if is_vulnerable((end_r, end_c), new_board, role):
                s -= 30
            if is_vulnerable((mid_r, mid_c), new_board, role):
                s -= 20
            s += count_jumps(new_board, role) * 5
            s -= count_vulnerable(new_board, role) * 5
            if role == "red":
                s += (r - end_r) * 3
            else:
                s += (end_r - r) * 3
            return s
        
        best_jump = max(jumps, key=score_j)
        return f"jump({best_jump[0]},{best_jump[1]},{best_jump[2]},{best_jump[3]},{best_jump[4]},{best_jump[5]})"
    
    # Collect all moves
    moves = []
    for r, c in pieces(role, board):
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if valid(nr, nc) and board.get((nr, nc)) == "blank":
                moves.append((r, c, nr, nc))
    
    if moves:
        def score_m(m):
            r1, c1, r2, c2 = m
            new_board = board.copy()
            new_board[(r1, c1)] = "blank"
            new_board[(r2, c2)] = role
            s = 0
            if is_vulnerable((r2, c2), new_board, role):
                s -= 50
            if role == "red":
                s += (r1 - r2) * 10
            else:
                s += (r2 - r1) * 10
            s += count_jumps(new_board, role) * 5
            s -= count_vulnerable(new_board, role) * 5
            return s
        
        best_move = max(moves, key=score_m)
        return f"move({best_move[0]},{best_move[1]},{best_move[2]},{best_move[3]})"
    
    return "kerchunk"
