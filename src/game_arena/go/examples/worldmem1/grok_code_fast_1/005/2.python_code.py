
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Board representation: 0 = empty, 1 = me, 2 = opponent
    BOARD_SIZE = 19
    board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for r, c in me:
        board[r-1][c-1] = 1  # Convert to 0-based indexing
    for r, c in opponent:
        board[r-1][c-1] = 2
    
    # Initialize memory for game phase
    if 'move_count' not in memory:
        memory['move_count'] = 0
    memory['move_count'] += 1
    
    # Opening book: Star points in order (corners first, then sides, then center)
    opening_moves = [
        (4, 4), (4, 16), (16, 4), (16, 16),  # Corners
        (4, 10), (10, 4), (10, 16), (16, 10),  # Sides
        (10, 10)  # Tengen (center)
    ]
    if memory['move_count'] <= len(opening_moves) and all(board[r-1][c-1] == 0 for r, c in opening_moves[:memory['move_count']]):
        move = opening_moves[memory['move_count'] - 1]
        if is_legal_move(board, move, 1):
            return (move, memory)
    
    # Find all legal moves
    legal_moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == 0:
                pos = (r+1, c+1)  # Convert back to 1-based
                if is_legal_move(board, pos, 1):
                    legal_moves.append(pos)
    
    # If no legal moves, pass
    if not legal_moves:
        return ((0, 0), memory)
    
    # Evaluate each legal move with a simple heuristic
    def evaluate_move(pos):
        r, c = pos[0]-1, pos[1]-1  # 0-based
        score = 0
        # Directions: up, down, left, right
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                neighbor = board[nr][nc]
                if neighbor == 1:  # Own stone
                    score += 2  # Increase allies
                elif neighbor == 2:  # Opponent stone
                    score -= 1  # Threat: reduce freedom
                # Empty: neutral
        # Favor center-ish positions slightly
        dist_to_center = abs(r - 9) + abs(c - 9)
        score -= dist_to_center * 0.1
        return score
    
    # Choose the move with the highest score; break ties randomly
    best_move = max(legal_moves, key=evaluate_move)
    best_score = evaluate_move(best_move)
    candidates = [m for m in legal_moves if evaluate_move(m) == best_score]
    chosen = random.choice(candidates)
    
    return (chosen, memory)

def is_legal_move(board, pos, player):
    r, c = pos[0]-1, pos[1]-1  # 0-based
    BOARD_SIZE = 19
    if r < 0 or r >= BOARD_SIZE or c < 0 or c >= BOARD_SIZE or board[r][c] != 0:
        return False
    
    # Temporarily place the stone
    board[r][c] = player
    
    # Check if the group has liberties
    opponent = 3 - player
    visited = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    has_liberty = check_liberties(board, r, c, visited, player)
    
    # Undo placement
    board[r][c] = 0
    
    if not has_liberty:
        # Check if capturing opponent groups; if capturing, it's ok
        captures = False
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == opponent:
                visited_opp = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
                if not check_liberties(board, nr, nc, visited_opp, opponent):
                    captures = True
                    break
        if not captures:
            return False  # Suicide
    
    return True

def check_liberties(board, r, c, visited, player):
    BOARD_SIZE = 19
    if visited[r][c]:
        return False
    visited[r][c] = True
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            if board[nr][nc] == 0:
                return True  # Liberty found
            elif board[nr][nc] == player:
                if check_liberties(board, nr, nc, visited, player):
                    return True
    return False
