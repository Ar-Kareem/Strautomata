
def policy(you: list[list[int]], opponent: list[list[int]]) -> str:
    center_r = 2
    center_c = 2.5
    captures = []
    non_captures = []
    
    for r in range(5):
        for c in range(6):
            if you[r][c] == 1:
                # Check up
                if r - 1 >= 0 and opponent[r-1][c] == 1:
                    captures.append((r, c, 'U'))
                # Check right
                if c + 1 < 6 and opponent[r][c+1] == 1:
                    captures.append((r, c, 'R'))
                # Check down
                if r + 1 < 5 and opponent[r+1][c] == 1:
                    captures.append((r, c, 'D'))
                # Check left
                if c - 1 >= 0 and opponent[r][c-1] == 1:
                    captures.append((r, c, 'L'))
    
    if captures:
        best_move = None
        best_distance = float('inf')
        for move in captures:
            r, c, dir = move
            dr, dc = 0, 0
            if dir == 'U':
                dr = -1
            elif dir == 'R':
                dc = 1
            elif dir == 'D':
                dr = 1
            elif dir == 'L':
                dc = -1
            captured_r = r + dr
            captured_c = c + dc
            distance = abs(captured_r - center_r) + abs(captured_c - center_c)
            if distance < best_distance:
                best_distance = distance
                best_move = (r, c, dir)
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"
    else:
        for r in range(5):
            for c in range(6):
                if you[r][c] == 1:
                    # Check up
                    if r - 1 >= 0 and you[r-1][c] == 0 and opponent[r-1][c] == 0:
                        non_captures.append((r, c, 'U'))
                    # Check right
                    if c + 1 < 6 and you[r][c+1] == 0 and opponent[r][c+1] == 0:
                        non_captures.append((r, c, 'R'))
                    # Check down
                    if r + 1 < 5 and you[r+1][c] == 0 and opponent[r+1][c] == 0:
                        non_captures.append((r, c, 'D'))
                    # Check left
                    if c - 1 >= 0 and you[r][c-1] == 0 and opponent[r][c-1] == 0:
                        non_captures.append((r, c, 'L'))
        
        if not non_captures:
            return "0,0,U"  # Fallback (should not occur per game rules)
        
        best_move = None
        best_distance = float('inf')
        for move in non_captures:
            r, c, dir = move
            dr, dc = 0, 0
            if dir == 'U':
                dr = -1
            elif dir == 'R':
                dc = 1
            elif dir == 'D':
                dr = 1
            elif dir == 'L':
                dc = -1
            dest_r = r + dr
            dest_c = c + dc
            distance = abs(dest_r - center_r) + abs(dest_c - center_c)
            if distance < best_distance:
                best_distance = distance
                best_move = (r, c, dir)
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"
