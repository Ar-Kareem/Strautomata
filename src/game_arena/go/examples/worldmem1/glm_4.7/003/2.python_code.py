
import random
import numpy as np

def get_group_and_liberties(board, r, c):
    """Get the group and liberties of a stone at position (r, c)."""
    if not (0 <= r < 19 and 0 <= c < 19) or board[r, c] == 0:
        return set(), set()
    
    player = board[r, c]
    group = set()
    liberties = set()
    stack = [(r, c)]
    
    while stack:
        curr_r, curr_c = stack.pop()
        if (curr_r, curr_c) in group:
            continue
        group.add((curr_r, curr_c))
        
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = curr_r + dr, curr_c + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board[nr, nc] == 0:
                    liberties.add((nr, nc))
                elif board[nr, nc] == player and (nr, nc) not in group:
                    stack.append((nr, nc))
    
    return group, liberties

def simulate_move(board, r, c, player):
    """Simulate placing a stone and return new board and captured stones."""
    new_board = board.copy()
    new_board[r, c] = player
    
    opponent = -player
    captured = set()
    
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and new_board[nr, nc] == opponent:
            group, liberties = get_group_and_liberties(new_board, nr, nc)
            if len(liberties) == 0:
                captured.update(group)
    
    for cr, cc in captured:
        new_board[cr, cc] = 0
    
    return new_board, captured

def is_valid_move(board, r, c, player, memory):
    """Check if a move is legal."""
    if not (0 <= r < 19 and 0 <= c < 19) or board[r, c] != 0:
        return False
    
    new_board, _ = simulate_move(board, r, c, player)
    group, liberties = get_group_and_liberties(new_board, r, c)
    
    if len(liberties) == 0:  # Suicide
        return False
    
    if 'previous_board' in memory and np.array_equal(new_board, memory['previous_board']):
        return False  # Ko
    
    return True

def get_all_legal_moves(board, player, memory):
    """Get all legal moves as list of (row, col) in 1-indexed format."""
    legal = []
    for r in range(19):
        for c in range(19):
            if is_valid_move(board, r, c, player, memory):
                legal.append((r + 1, c + 1))
    return legal

def find_captures(board, player, memory):
    """Find all moves that capture opponent stones."""
    captures = []
    for r in range(19):
        for c in range(19):
            if board[r, c] == 0 and is_valid_move(board, r, c, player, memory):
                _, captured = simulate_move(board, r, c, player)
                if captured:
                    captures.append(((r + 1, c + 1), len(captured)))
    return captures

def find_atari_defense(board, player, memory):
    """Find moves that save our stones from atari."""
    defenses = set()
    
    for r in range(19):
        for c in range(19):
            if board[r, c] == player:
                group, liberties = get_group_and_liberties(board, r, c)
                if len(liberties) == 1:
                    for lr, lc in liberties:
                        if is_valid_move(board, lr, lc, player, memory):
                            new_board, _ = simulate_move(board, lr, lc, player)
                            new_group, new_liberties = get_group_and_liberties(new_board, lr, lc)
                            if len(new_liberties) > 1:
                                defenses.add((lr + 1, lc + 1))
    
    return list(defenses)

def evaluate_move(board, r, c, player):
    """Score a move based on strategic factors."""
    r0, c0 = r - 1, c - 1
    score = 0.0
    opponent = -player
    
    new_board, captured = simulate_move(board, r0, c0, player)
    
    # Captures
    score += len(captured) * 15
    
    # Connection to friendly stones
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r0 + dr, c0 + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == player:
            score += 8
    
    # Diagonal connections
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = r0 + dr, c0 + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == player:
            score += 3
    
    # Our liberties
    _, our_liberties = get_group_and_liberties(new_board, r0, c0)
    if len(our_liberties) == 1:
        score -= 120
    else:
        score += len(our_liberties) * 4
    
    # Effect on opponent
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r0 + dr, c0 + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == opponent:
            _, old_libs = get_group_and_liberties(board, nr, nc)
            _, new_libs = get_group_and_liberties(new_board, nr, nc)
            reduction = len(old_libs) - len(new_libs)
            if reduction > 0:
                score += reduction * 25
            if len(new_libs) == 1:
                score += 35
    
    # Positional factors
    dist_from_center = abs(r0 - 9) + abs(c0 - 9)
    score += (18 - dist_from_center) * 0.4
    
    total_stones = np.sum(np.abs(board))
    if total_stones > 20:
        if r0 == 0 or r0 == 18 or c0 == 0 or c0 == 18:
            score -= 60
        elif r0 == 1 or r0 == 17 or c0 == 1 or c0 == 17:
            score -= 25
    
    return score

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """Select the next move using a strategic evaluation."""
    board = np.zeros((19, 19), dtype=int)
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = -1
    
    total_stones = len(me) + len(opponent)
    legal_moves = get_all_legal_moves(board, 1, memory)
    
    if not legal_moves:
        return (0, 0), memory
    
    # 1. Capture
    captures = find_captures(board, 1, memory)
    if captures:
        best_move, _ = max(captures, key=lambda x: x[1])
        new_board, _ = simulate_move(board, best_move[0]-1, best_move[1]-1, 1)
        memory['previous_board'] = new_board
        return best_move, memory
    
    # 2. Defend
    defenses = find_atari_defense(board, 1, memory)
    if defenses:
        scored = [(d, evaluate_move(board, d[0], d[1], 1)) for d in defenses]
        best_move, _ = max(scored, key=lambda x: x[1])
        new_board, _ = simulate_move(board, best_move[0]-1, best_move[1]-1, 1)
        memory['previous_board'] = new_board
        return best_move, memory
    
    # 3. Opening
    if total_stones < 30:
        star_points = [(3, 3), (3, 9), (3, 15),
                       (9, 3), (9, 9), (9, 15),
                       (15, 3), (15, 9), (15, 15)]
        for sp in star_points:
            if sp in legal_moves:
                new_board, _ = simulate_move(board, sp[0]-1, sp[1]-1, 1)
                memory['previous_board'] = new_board
                return sp, memory
        
        extensions = []
        for r, c in me:
            for dr, dc in [(-2, -1), (-2, 0), (-2, 1),
                           (-1, -2), (-1, 2),
                           (0, -2), (0, 2),
                           (1, -2), (1, 2),
                           (2, -1), (2, 0), (2, 1)]:
                nr, nc = r + dr, c + dc
                move = (nr, nc)
                if move in legal_moves and 3 <= nr <= 17 and 3 <= nc <= 17:
                    extensions.append(move)
        
        if extensions:
            chosen = random.choice(extensions)
            new_board, _ = simulate_move(board, chosen[0]-1, chosen[1]-1, 1)
            memory['previous_board'] = new_board
            return chosen, memory
    
    # 4. Evaluate all moves
    scored = [(move, evaluate_move(board, move[0], move[1], 1)) for move in legal_moves]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    top_n = min(5, len(scored))
    top_moves = scored[:top_n]
    scores = [max(0.01, s) for _, s in top_moves]
    
    total = sum(scores)
    rand_val = random.random() * total
    cumulative = 0
    chosen = top_moves[0][0]
    for (move, _), score in zip(top_moves, scores):
        cumulative += score
        if rand_val <= cumulative:
            chosen = move
            break
    
    new_board, _ = simulate_move(board, chosen[0]-1, chosen[1]-1, 1)
    memory['previous_board'] = new_board
    
    return chosen, memory
