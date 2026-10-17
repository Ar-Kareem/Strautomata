
def policy(board):
    # Helper function to check if a path is clear between two points
    def is_path_clear(start, end):
        dr = end[0] - start[0]
        dc = end[1] - start[1]
        steps = max(abs(dr), abs(dc))
        if steps == 0:
            return True
        step_r = dr // steps
        step_c = dc // steps
        for i in range(1, steps):
            r = start[0] + i * step_r
            c = start[1] + i * step_c
            if board[r][c] != 0:
                return False
        return True

    # Helper function to evaluate move score
    def evaluate_move(move_str):
        parts = move_str.split(':')
        from_pos = tuple(map(int, parts[0].split(',')))
        to_pos = tuple(map(int, parts[1].split(',')))
        arrow_pos = tuple(map(int, parts[2].split(',')))
        score = 0
        if board[arrow_pos[0]][arrow_pos[1]] == 2:
            score += 100  # Capture opponent's amazon
        if board[arrow_pos[0]][arrow_pos[1]] == 0:
            # Block opponent's amazons
            for i in range(6):
                for j in range(6):
                    if board[i][j] == 2:
                        # Check if arrow shot blocks opponent's amazons
                        if is_path_clear(arrow_pos, (i, j)):
                            score += 10
        # Central positioning bonus
        center = (2.5, 2.5)
        score += 5 * (1 / max(1, (abs(to_pos[0] - center[0]) + abs(to_pos[1] - center[1]))))
        return score

    # Find all your amazons
    my_amazons = []
    for i in range(6):
        for j in range(6):
            if board[i][j] == 1:
                my_amazons.append((i, j))
    
    # Directions for movement and arrow shots
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    best_move = None
    best_score = -1

    for (r, c) in my_amazons:
        for dr, dc in directions:
            for step in range(1, 6):
                nr = r + dr * step
                nc = c + dc * step
                if nr < 0 or nr >= 6 or nc < 0 or nc >= 6:
                    break
                if board[nr][nc] != 0:
                    break
                if not is_path_clear((r, c), (nr, nc)):
                    break
                for adr, adc in directions:
                    ar = nr + adr * step
                    ac = nc + adc * step
                    if ar < 0 or ar >= 6 or ac < 0 or ac >= 6:
                        continue
                    if board[ar][ac] != 0:
                        continue
                    if not is_path_clear((nr, nc), (ar, ac)):
                        continue
                    move_str = f"{r},{c}:{nr},{nc}:{ar},{ac}"
                    score = evaluate_move(move_str)
                    if score > best_score:
                        best_score = score
                        best_move = move_str
    return best_move or "0,0:0,0:0,0"
