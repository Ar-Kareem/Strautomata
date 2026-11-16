
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    Smart Go policy that evaluates board state and selects optimal moves.
    
    Priority:
    1. Capture opponent stones in atari
    2. Avoid self-atari
    3. Play strategic moves with best overall evaluation
    """
    
    # Build board: 0=empty, 1=me, 2=opponent
    board = [[0] * 19 for _ in range(19)]
    for r, c in me:
        board[r-1][c-1] = 1
    for r, c in opponent:
        board[r-1][c-1] = 2
    
    # 1. Check for opponent capture opportunities (atari)
    for r, c in opponent:
        if count_liberties_single((r-1, c-1), board, 2) == 1:
            move = (r, c)
            if is_legal(move, board, 1):
                return move, memory
    
    # 2. Check for self-atari moves and skip them
    # 3. Evaluate all legal moves and pick best
    best_move = None
    best_score = -float('inf')
    
    for r in range(19):
        for c in range(19):
            if board[r][c] != 0:
                continue
                
            move = (r+1, c+1)
            if not is_legal(move, board, 1):
                continue
            
            score = evaluate_move(move, board, me, opponent)
            if score > best_score:
                best_score = score
                best_move = move
    
    # If no legal moves, pass
    if best_move is None:
        return (0, 0), memory
    
    return best_move, memory


def count_liberties_single(pos, board, player):
    """Count liberties of a single stone using BFS flood fill"""
    if board[pos[0]][pos[1]] != player:
        return 0
    
    queue = [pos]
    visited = set([pos])
    liberties = set()
    
    while queue:
        r, c = queue.pop(0)
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board[nr][nc] == 0:
                    liberties.add((nr, nc))
                elif board[nr][nc] == player and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
    
    return len(liberties)


def count_liberties_group(start_pos, board, player):
    """Count liberties of entire connected group containing start_pos"""
    if board[start_pos[0]][start_pos[1]] != player:
        return 0
    
    queue = [start_pos]
    visited = set([start_pos])
    liberties = set()
    
    while queue:
        r, c = queue.pop(0)
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board[nr][nc] == 0:
                    liberties.add((nr, nc))
                elif board[nr][nc] == player and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
    
    return len(liberties), visited


def is_legal(move, board, player):
    """Check if move is legal (not suicide unless captures)"""
    r, c = move[0]-1, move[1]-1
    
    if not (0 <= r < 19 and 0 <= c < 19):
        return False
    if board[r][c] != 0:
        return False
    
    # Make temporary board
    test_board = [row[:] for row in board]
    test_board[r][c] = player
    
    # Check if this move captures opponent stones
    opponent = 3 - player
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19:
            if test_board[nr][nc] == opponent:
                if count_liberties_single((nr, nc), test_board, opponent) == 0:
                    return True  # Legal - captures opponent
    
    # Check if move is suicide (no liberties after move)
    if count_liberties_single((r, c), test_board, player) == 0:
        return False  # Illegal suicide
    
    return True


def evaluate_move(move, board, me, opponent):
    """Evaluate move quality with weighted scoring system"""
    r, c = move[0]-1, move[1]-1
    player = 1
    opponent_player = 2
    
    score = 0
    
    # 1. Check capture opportunities
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19:
            if board[nr][nc] == opponent_player:
                libs = count_liberties_single((nr, nc), board, opponent_player)
                if libs == 1:
                    score += 100  # Capture!
                elif libs == 2:
                    score += 50   # Potential capture next move
    
    # 2. Self-group protection
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19:
            if board[nr][nc] == player:
                libs, _ = count_liberties_group((nr, nc), board, player)
                if libs <= 2:
                    score += 30  # Protect weak groups
    
    # 3. Eye potential
    eye_score = 0
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19:
            if board[nr][nc] == 0:
                eye_score += 1
    if eye_score >= 3:
        score += 15
    
    # 4. Location value (center > edges > corners)
    center_dist = max(abs(r-9), abs(c-9))
    if center_dist <= 4:
        score += 10  # Center
    elif r == 0 or r == 18 or c == 0 or c == 18:
        score += 5   # Edge
    else:
        score += 2   # Elsewhere
    
    # 5. Proximity to own stones (influence)
    proximity_score = 0
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19:
            if board[nr][nc] == player:
                proximity_score += 2
            elif board[nr][nc] == 0:
                proximity_score += 1
    score += proximity_score
    
    # 6. Distance from opponent stones (avoid overconcentration)
    opp_proximity = 0
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19:
            if board[nr][nc] == opponent_player:
                opp_proximity -= 1
    score += opp_proximity
    
    return score


def count_group_size_and_liberties(start_pos, board, player):
    """Get both size and liberties of a group"""
    if board[start_pos[0]][start_pos[1]] != player:
        return 0, 0
    
    queue = [start_pos]
    visited = set([start_pos])
    liberties = set()
    
    while queue:
        r, c = queue.pop(0)
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board[nr][nc] == 0:
                    liberties.add((nr, nc))
                elif board[nr][nc] == player and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
    
    return len(visited), len(liberties)
