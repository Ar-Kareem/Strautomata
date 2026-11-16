
import time
import math

def is_connected(board, player):
    pieces = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                pieces.append((r, c))
    n = len(pieces)
    if n <= 1:
        return True
    
    # BFS to check 8-connectivity
    visited = set()
    queue = [pieces[0]]
    visited.add(pieces[0])
    
    while queue:
        curr_r, curr_c = queue.pop()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = curr_r + dr, curr_c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if board[nr][nc] == player and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
                        
    return len(visited) == n

def get_largest_component(board, player):
    pieces = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                pieces.append((r, c))
    n = len(pieces)
    if n <= 1:
        return n, n

    unvisited = set(pieces)
    max_comp = 0
    while unvisited:
        start = next(iter(unvisited))
        unvisited.remove(start)
        comp_size = 1
        queue = [start]
        while queue:
            curr_r, curr_c = queue.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = curr_r + dr, curr_c + dc
                    if (nr, nc) in unvisited:
                        unvisited.remove((nr, nc))
                        comp_size += 1
                        queue.append((nr, nc))
        if comp_size > max_comp:
            max_comp = comp_size
    return max_comp, n

DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

def count_line_pieces(board, r, c, dr, dc):
    count = 0
    # Positive direction
    kr, kc = r, c
    while 0 <= kr < 8 and 0 <= kc < 8:
        if board[kr][kc] != 0:
            count += 1
        kr += dr
        kc += dc
    # Negative direction
    kr, kc = r - dr, c - dc
    while 0 <= kr < 8 and 0 <= kc < 8:
        if board[kr][kc] != 0:
            count += 1
        kr -= dr
        kc -= dc
    return count

def generate_moves(board, player):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != player:
                continue
            for dr, dc in DIRECTIONS:
                D = count_line_pieces(board, r, c, dr, dc)
                nr = r + dr * D
                nc = c + dc * D
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    continue
                if board[nr][nc] == player:
                    continue
                
                # Check for opponent blocks
                blocked = False
                for step in range(1, D):
                    ir = r + dr * step
                    ic = c + dc * step
                    if board[ir][ic] == -player:
                        blocked = True
                        break
                if not blocked:
                    is_capture = (board[nr][nc] == -player)
                    moves.append((r, c, nr, nc, is_capture))
    return moves

def apply_move(board, move, player):
    r, c, nr, nc, _ = move
    captured = board[nr][nc]
    board[nr][nc] = player
    board[r][c] = 0
    return captured

def undo_move(board, move, player, captured):
    r, c, nr, nc, _ = move
    board[r][c] = player
    board[nr][nc] = captured

def evaluate(board, player):
    p_conn = is_connected(board, player)
    o_conn = is_connected(board, -player)
    
    if p_conn and not o_conn:
        return 100000.0
    if o_conn and not p_conn:
        return -100000.0
    if p_conn and o_conn:
        return 100000.0

    p_largest, p_total = get_largest_component(board, player)
    o_largest, o_total = get_largest_component(board, -player)

    p_ratio = (p_largest / p_total) if p_total > 0 else 0
    o_ratio = (o_largest / o_total) if o_total > 0 else 0
    score = (p_ratio - o_ratio) * 400.0

    # Center of mass distance
    p_pts = []
    o_pts = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                p_pts.append((r, c))
            elif board[r][c] == -player:
                o_pts.append((r, c))

    if p_pts:
        cr_p = sum(p[0] for p in p_pts) / len(p_pts)
        cc_p = sum(p[1] for p in p_pts) / len(p_pts)
        p_dist = sum(max(abs(p[0] - cr_p), abs(p[1] - cc_p)) for p in p_pts)
    else:
        p_dist = 0

    if o_pts:
        cr_o = sum(p[0] for p in o_pts) / len(o_pts)
        cc_o = sum(p[1] for p in o_pts) / len(o_pts)
        o_dist = sum(max(abs(p[0] - cr_o), abs(p[1] - cc_o)) for p in o_pts)
    else:
        o_dist = 0

    score += (o_dist - p_dist) * 15.0

    # Centralization bonus
    center_bonus = 0.0
    for r, c in p_pts:
        center_bonus += (3.5 - abs(r - 3.5)) + (3.5 - abs(c - 3.5))
    for r, c in o_pts:
        center_bonus -= (3.5 - abs(r - 3.5)) + (3.5 - abs(c - 3.5))
    score += center_bonus * 2.0

    return score

class TimeoutException(Exception):
    pass

def minimax(board, depth, alpha, beta, player, root_player, end_time):
    if time.time() > end_time:
        raise TimeoutException()

    p_conn = is_connected(board, player)
    o_conn = is_connected(board, -player)
    if p_conn or o_conn:
        val = evaluate(board, root_player)
        return val, None

    if depth == 0:
        return evaluate(board, root_player), None

    moves = generate_moves(board, player)
    if not moves:
        return evaluate(board, root_player), None

    # Sort moves: captures first, then center distance reduction
    def move_priority(m):
        return 1 if m[4] else 0
    moves.sort(key=move_priority, reverse=True)

    best_move = moves[0]
    is_maximizing = (player == root_player)

    if is_maximizing:
        max_eval = -float('inf')
        for move in moves:
            captured = apply_move(board, move, player)
            # Terminal check after move
            if is_connected(board, player):
                undo_move(board, move, player, captured)
                return 100000.0, move
            val, _ = minimax(board, depth - 1, alpha, beta, -player, root_player, end_time)
            undo_move(board, move, player, captured)
            
            if val > max_eval:
                max_eval = val
                best_move = move
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            captured = apply_move(board, move, player)
            if is_connected(board, player):
                undo_move(board, move, player, captured)
                return -100000.0, move
            val, _ = minimax(board, depth - 1, alpha, beta, -player, root_player, end_time)
            undo_move(board, move, player, captured)
            
            if val < min_eval:
                min_eval = val
                best_move = move
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(board) -> str:
    start_time = time.time()
    time_budget = 0.82
    end_time = start_time + time_budget

    # Convert board representation to standard mutable list of lists
    b = [[int(board[r][c]) for c in range(8)] for r in range(8)]

    legal_moves = generate_moves(b, 1)
    if not legal_moves:
        return "0,0:0,0"

    # Check immediate winning move
    for move in legal_moves:
        captured = apply_move(b, move, 1)
        win = is_connected(b, 1)
        undo_move(b, move, 1, captured)
        if win:
            return f"{move[0]},{move[1]}:{move[2]},{move[3]}"

    best_move = legal_moves[0]
    depth = 1
    max_depth = 8

    while depth <= max_depth:
        try:
            _, move = minimax(b, depth, -float('inf'), float('inf'), 1, 1, end_time)
            if move is not None:
                best_move = move
            depth += 1
            if time.time() >= end_time:
                break
        except TimeoutException:
            break

    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
