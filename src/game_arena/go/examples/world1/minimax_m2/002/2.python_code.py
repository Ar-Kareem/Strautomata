
def find_group_and_liberties(board, r, c, color):
    directions = [(-1,0), (1,0), (0,-1), (0,1)]
    stack = [(r, c)]
    group = set()
    liberties = set()
    visited = set()
    while stack:
        cr, cc = stack.pop()
        if (cr, cc) in visited:
            continue
        visited.add((cr, cc))
        group.add((cr, cc))
        for dr, dc in directions:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board[nr][nc] == color:
                    stack.append((nr, nc))
                elif board[nr][nc] == 0:
                    liberties.add((nr, nc))
    return group, liberties

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    directions = [(-1,0), (1,0), (0,-1), (0,1)]
    
    # Convert to 0-based indices
    me0 = [(r-1, c-1) for r, c in me]
    opponent0 = [(r-1, c-1) for r, c in opponent]
    
    # Initialize board
    board = [[0 for _ in range(19)] for _ in range(19)]
    for r, c in me0:
        board[r][c] = 1
    for r, c in opponent0:
        board[r][c] = 2
    
    # Find all empty points
    empty_points = []
    for i in range(19):
        for j in range(19):
            if board[i][j] == 0:
                empty_points.append((i, j))
    
    capture_moves = []
    non_capture_moves = []
    
    for i, j in empty_points:
        captured_groups = 0
        # Check for captures
        for dr, dc in directions:
            nr, nc = i + dr, j + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] == 2:
                group, liberties = find_group_and_liberties(board, nr, nc, 2)
                if len(liberties) == 1 and (i, j) in liberties:
                    captured_groups += 1
        
        if captured_groups > 0:
            capture_moves.append((i, j, captured_groups))
        else:
            # Check if has liberty
            has_liberty = False
            for dr, dc in directions:
                nr, nc = i + dr, j + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] == 0:
                    has_liberty = True
                    break
            if has_liberty:
                non_capture_moves.append((i, j))
    
    # Choose move
    if capture_moves:
        # Choose move with most captures
        max_captures = max(move[2] for move in capture_moves)
        candidates = [move for move in capture_moves if move[2] == max_captures]
        chosen = candidates[0]
        i, j = chosen[0], chosen[1]
        return (i+1, j+1)
    
    elif non_capture_moves:
        # Define 3-3 points
        corners = [(3,3), (3,15), (15,3), (15,15)]
        for corner in corners:
            if corner in non_capture_moves:
                i, j = corner
                return (i+1, j+1)
        center = (9,9)
        if center in non_capture_moves:
            i, j = center
            return (i+1, j+1)
        i, j = non_capture_moves[0]
        return (i+1, j+1)
    
    else:
        return (0, 0)
