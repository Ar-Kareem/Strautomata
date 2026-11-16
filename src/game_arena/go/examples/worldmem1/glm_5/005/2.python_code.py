
import random
from collections import deque

BOARD_SIZE = 19

def neighbors(pos):
    """Get adjacent positions within board bounds."""
    r, c = pos
    result = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
            result.append((nr, nc))
    return result

def get_group(board, start):
    """Get connected group and its liberties starting from a stone."""
    color = board[start]
    stones = set()
    liberties = set()
    queue = deque([start])
    seen = {start}
    
    while queue:
        pos = queue.popleft()
        stones.add(pos)
        for nb in neighbors(pos):
            if nb in board:
                if board[nb] == color and nb not in seen:
                    seen.add(nb)
                    queue.append(nb)
            else:
                liberties.add(nb)
    return stones, liberties

def find_groups(board, color):
    """Find all groups of a given color with their liberties."""
    groups = []
    visited = set()
    for pos, col in board.items():
        if col == color and pos not in visited:
            stones, libs = get_group(board, pos)
            groups.append((stones, libs))
            visited.update(stones)
    return groups

def play_move(board, pos, color):
    """Simulate playing a move. Returns new board and captured stones."""
    new_board = dict(board)
    new_board[pos] = color
    opp = 'opponent' if color == 'me' else 'me'
    captures = set()
    
    for nb in neighbors(pos):
        if nb in new_board and new_board[nb] == opp:
            stones, libs = get_group(new_board, nb)
            if not libs:
                captures.update(stones)
                for s in stones:
                    del new_board[s]
    return new_board, captures

def is_legal(board, pos, color):
    """Check if a move is legal."""
    if pos in board:
        return False
    
    r, c = pos
    if not (1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE):
        return False
    
    opp = 'opponent' if color == 'me' else 'me'
    
    # Check for captures
    for nb in neighbors(pos):
        if nb in board and board[nb] == opp:
            _, libs = get_group(board, nb)
            if libs == {pos}:
                return True
    
    # Check for liberty or connection
    for nb in neighbors(pos):
        if nb not in board:
            return True
        if board[nb] == color:
            _, libs = get_group(board, nb)
            if len(libs) > 1 or (len(libs) == 1 and pos not in libs):
                return True
    return False

def get_legal_moves(board, color):
    """Get all legal moves for a player."""
    moves = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if is_legal(board, (r, c), color):
                moves.append((r, c))
    return moves

def evaluate_move(board, pos, color, my_groups, opp_groups):
    """Evaluate the quality of a potential move."""
    r, c = pos
    opp = 'opponent' if color == 'me' else 'me'
    score = 0.0
    
    # 1. Capture value (highest priority)
    for nb in neighbors(pos):
        if nb in board and board[nb] == opp:
            stones, libs = get_group(board, nb)
            if libs == {pos}:
                score += len(stones) * 150  # Capture bonus
            elif len(libs) == 2:
                score += 40 + len(stones) * 10  # Atari bonus
            elif len(libs) == 3:
                score += 15  # Pressure
    
    # 2. Own group safety
    new_board, caps = play_move(board, pos, color)
    if pos in new_board:
        _, my_libs = get_group(new_board, pos)
        score += len(my_libs) * 4
        
        # Check if this saves a group
        for stones, libs in my_groups:
            if pos in libs and len(libs) <= 2:
                if len(my_libs) >= 3:
                    score += 30  # Saving a weak group
    else:
        return -1000  # Suicide (shouldn't happen with legal check)
    
    # 3. Positional value
    dr = min(r, 20 - r)  # Distance from edge
    dc = min(c, 20 - c)
    
    # Star points are valuable
    star_points = {(4,4), (4,10), (4,16), (10,4), (10,16), (16,4), (16,10), (16,16)}
    if pos in star_points:
        score += 12
    elif (dr == 4 or dr == 3) and (dc == 4 or dc == 3):
        score += 6
    elif dr == 4 or dc == 4:
        score += 5
    elif dr == 3 or dc == 3:
        score += 4
    elif dr >= 5 and dc >= 5:
        score += 2  # Center influence
    
    # Penalize edge moves
    if dr <= 2 or dc <= 2:
        score -= 6
    if dr == 1 or dc == 1:
        score -= 10
    
    # 4. Connection value
    friendly_neighbors = sum(1 for nb in neighbors(pos) if nb in board and board[nb] == color)
    enemy_neighbors = sum(1 for nb in neighbors(pos) if nb in board and board[nb] == opp)
    
    if friendly_neighbors >= 2:
        score += 10  # Strong connection
    elif friendly_neighbors == 1:
        score += 4  # Extension
    
    # 5. Cutting value
    if enemy_neighbors > 0 and friendly_neighbors > 0:
        # Check if cutting
        adjacent_enemy_groups = set()
        for nb in neighbors(pos):
            if nb in board and board[nb] == opp:
                for i, (g_stones, _) in enumerate(opp_groups):
                    if nb in g_stones:
                        adjacent_enemy_groups.add(i)
        if len(adjacent_enemy_groups) >= 2:
            score += 20  # Cutting bonus
    
    # 6. Influence towards opponent weak groups
    for stones, libs in opp_groups:
        if len(libs) <= 3:
            min_dist = min(abs(r - sr) + abs(c - sc) for sr, sc in stones)
            if min_dist <= 3:
                score += (4 - min_dist) * 3
    
    return score

def policy(me, opponent, memory):
    """Main policy function for Go AI."""
    # Build board representation
    board = {}
    for pos in me:
        board[pos] = 'me'
    for pos in opponent:
        board[pos] = 'opponent'
    
    # Get ko point from memory
    ko = memory.get('ko')
    
    # Opening move
    if not board:
        return (4, 4), {}
    
    # Find all groups
    my_groups = find_groups(board, 'me')
    opp_groups = find_groups(board, 'opponent')
    
    # Priority 1: Capture opponent groups in atari
    for stones, libs in opp_groups:
        if len(libs) == 1:
            move = list(libs)[0]
            if move != ko and is_legal(board, move, 'me'):
                _, captures = play_move(board, move, 'me')
                new_memory = {}
                # Check for ko situation
                if len(stones) == 1 and len(captures) == 1:
                    new_memory['ko'] = list(captures)[0]
                return move, new_memory
    
    # Priority 2: Save own groups in atari
    for stones, libs in my_groups:
        if len(libs) == 1:
            move = list(libs)[0]
            if move != ko and is_legal(board, move, 'me'):
                new_board, _ = play_move(board, move, 'me')
                if move in new_board:
                    _, new_libs = get_group(new_board, move)
                    if len(new_libs) >= 2:
                        return move, {}
    
    # Priority 3: Create atari on opponent groups (prioritize larger groups)
    best_atari = None
    best_atari_score = 0
    for stones, libs in opp_groups:
        if len(libs) == 2:
            for move in libs:
                if move != ko and is_legal(board, move, 'me'):
                    atari_score = len(stones) * 10
                    if atari_score > best_atari_score:
                        best_atari = move
                        best_atari_score = atari_score
    
    if best_atari:
        return best_atari, {}
    
    # Priority 4: Evaluate all legal moves
    moves = get_legal_moves(board, 'me')
    
    # Filter out ko point
    if ko and ko in moves:
        moves.remove(ko)
    
    if not moves:
        return (0, 0), {}  # Pass
    
    # Score all moves
    scored_moves = []
    for move in moves:
        score = evaluate_move(board, move, 'me', my_groups, opp_groups)
        scored_moves.append((move, score))
    
    scored_moves.sort(key=lambda x: -x[1])
    
    # Select move with slight randomization among top choices
    if len(scored_moves) >= 2:
        best_score = scored_moves[0][1]
        threshold = max(best_score - 8, best_score * 0.9)
        top_moves = [m for m, s in scored_moves if s >= threshold]
        
        if len(top_moves) > 1 and random.random() < 0.25:
            return random.choice(top_moves), {}
    
    return scored_moves[0][0], {}
