
import random

def get_group(board, r, c, color):
    group = set()
    to_visit = [(r, c)]
    while to_visit:
        x, y = to_visit.pop()
        if (x, y) in group:
            continue
        group.add((x, y))
        for dx, dy in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            nx, ny = x + dx, y + dy
            if 1 <= nx < 20 and 1 <= ny < 20 and board[nx][ny] == color and (nx, ny) not in group:
                to_visit.append((nx, ny))
    return group

def liberties(board, group):
    lib = set()
    for x, y in group:
        for dx, dy in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            nx, ny = x + dx, y + dy
            if 1 <= nx < 20 and 1 <= ny < 20 and board[nx][ny] == 0:
                lib.add((nx, ny))
    return len(lib)

def is_legal(board, r, c):
    if board[r][c] != 0:
        return False
    board[r][c] = 1
    captured = []
    for dr, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
        nr, nc = r + dr, c + dc
        if 1 <= nr < 20 and 1 <= nc < 20 and board[nr][nc] == -1:
            opp_group = get_group(board, nr, nc, -1)
            if liberties(board, opp_group) == 0:
                captured.extend(opp_group)
    my_group = get_group(board, r, c, 1)
    my_lib = liberties(board, my_group)
    if my_lib > 0 or captured:
        for x, y in captured:
            board[x][y] = 0
        board[r][c] = 0
        return True
    board[r][c] = 0
    return False

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    board = [[0] * 20 for _ in range(20)]
    for r, c in me:
        board[r][c] = 1
    for r, c in opponent:
        board[r][c] = -1
    
    best_move = (0, 0)
    best_score = -float('inf')
    
    for r in range(1, 20):
        for c in range(1, 20):
            if board[r][c] == 0 and is_legal(board, r, c):
                # Calculate heuristic score
                num_adj_same = sum(1 for dr, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]
                                   if 1 <= r + dr < 20 and 1 <= c + dc < 20 and board[r + dr][c + dc] == 1)
                num_adj_opp = sum(1 for dr, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]
                                  if 1 <= r + dr < 20 and 1 <= c + dc < 20 and board[r + dr][c + dc] == -1)
                num_adj_empty = sum(1 for dr, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]
                                    if 1 <= r + dr < 20 and 1 <= c + dc < 20 and board[r + dr][c + dc] == 0)
                centrality = (10 - abs(10 - r) - abs(10 - c)) * 0.5
                score = num_adj_same * 3 - num_adj_opp * 1 + num_adj_empty * 1 + centrality
                
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    
    # If no legal moves found (unlikely, but pass), return (0, 0)
    return best_move, memory
