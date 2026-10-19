
import copy

def get_adjacent(r, c):
    """Return list of adjacent positions within board bounds."""
    adjacent = []
    if r > 1:
        adjacent.append((r-1, c))
    if r < 19:
        adjacent.append((r+1, c))
    if c > 1:
        adjacent.append((r, c-1))
    if c < 19:
        adjacent.append((r, c+1))
    return adjacent

def find_group(board, pos, player):
    """Find all stones in the connected group and their liberties using BFS."""
    visited = set()
    queue = [pos]
    group = set()
    liberties = set()
    while queue:
        r, c = queue.pop(0)
        if (r, c) in visited:
            continue
        visited.add((r, c))
        group.add((r, c))
        for adj in get_adjacent(r, c):
            if board[adj[0]][adj[1]] == 0:
                liberties.add(adj)
            elif board[adj[0]][adj[1]] == player and adj not in visited:
                queue.append(adj)
    return group, liberties

def is_legal_move(board, move, player):
    """Check if placing a stone at move is legal."""
    r, c = move
    if board[r][c] != 0:
        return False
    
    # Create temporary board to simulate move
    temp_board = [row[:] for row in board]
    temp_board[r][c] = player
    
    # Check if new stone has liberties
    group, liberties = find_group(temp_board, (r, c), player)
    if len(liberties) > 0:
        return True
    
    # Check if capturing opponent stones
    opp_player = 3 - player  # 1 <-> 2
    for adj in get_adjacent(r, c):
        if temp_board[adj[0]][adj[1]] == opp_player:
            adj_group, adj_liberties = find_group(temp_board, adj, opp_player)
            if len(adj_liberties) == 0:
                return True
    
    return False  # Suicide move

def get_captures(board, move, player):
    """Calculate number of opponent stones captured by this move."""
    r, c = move
    temp_board = [row[:] for row in board]
    temp_board[r][c] = player
    opp_player = 3 - player
    captures = 0
    
    for adj in get_adjacent(r, c):
        if temp_board[adj[0]][adj[1]] == opp_player:
            adj_group, adj_liberties = find_group(temp_board, adj, opp_player)
            if len(adj_liberties) == 0:
                captures += len(adj_group)
    
    return captures

def get_saved_groups(board, move, player):
    """Calculate value of own groups saved from atari by this move."""
    r, c = move
    saved = 0
    
    for adj in get_adjacent(r, c):
        if board[adj[0]][adj[1]] == player:
            # Check original group status
            original_group, original_liberties = find_group(board, adj, player)
            if len(original_liberties) == 1:
                temp_board = [row[:] for row in board]
                temp_board[r][c] = player
                new_group, new_liberties = find_group(temp_board, adj, player)
                if len(new_liberties) > 0:
                    saved += len(new_group)
    
    return saved

def get_positional_score(move, memory):
    """Score based on board position and game phase."""
    r, c = move
    move_count = memory.get('move_count', 0)
    score = 0
    
    # Star points for opening phase
    star_points = [(4,4), (4,10), (4,16), (10,4), (10,10), 
                   (10,16), (16,4), (16,10), (16,16)]
    
    if move_count < 20:
        if (r, c) in star_points:
            score += 1000  # Maximize star point utilization
        # Prefer edges/corners early
        d_edge = min(r-1, 19-r, c-1, 19-c)
        score += (10 - d_edge) * 2
    else:
        # Middlegame: prefer center influence
        dist_center = abs(r-10) + abs(c-10)
        score += max(0, 15 - dist_center)
    
    return score

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Initialize 19x19 board (1-based indexing)
    board = [[0]*20 for _ in range(20)]  # Rows 0 and 20 unused
    for r, c in me:
        board[r][c] = 1  # Current player stones
    for r, c in opponent:
        board[r][c] = 2  # Opponent stones
    
    # Generate all empty points
    empty_points = [(r, c) for r in range(1, 20) for c in range(1, 20) if board[r][c] == 0]
    
    # Filter legal moves
    legal_moves = [move for move in empty_points if is_legal_move(board, move, 1)]
    if not legal_moves:
        return (0, 0), memory
    
    # Score each legal move
    scores = {}
    for move in legal_moves:
        score = 0
        # Capture potential
        captures = get_captures(board, move, 1)
        score += captures * 150
        
        # Defense potential
        saved = get_saved_groups(board, move, 1)
        score += saved * 100
        
        # Positional value
        score += get_positional_score(move, memory)
        
        scores[move] = score
    
    # Select best move
    best_move = max(scores, key=lambda m: scores[m])
    
    # Update game state memory
    memory['move_count'] = memory.get('move_count', 0) + 1
    return (best_move, memory)
