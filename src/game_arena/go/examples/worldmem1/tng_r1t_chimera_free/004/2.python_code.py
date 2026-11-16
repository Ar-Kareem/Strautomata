
import numpy as np

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    def get_adjacent(r, c):
        adj = []
        if r > 1:
            adj.append((r-1, c))
        if r < 19:
            adj.append((r+1, c))
        if c > 1:
            adj.append((r, c-1))
        if c < 19:
            adj.append((r, c+1))
        return adj
    
    def count_liberties(pos, color, board):
        visited = set()
        q = [pos]
        group = []
        liberties = set()
        while q:
            p = q.pop(0)
            if p in visited:
                continue
            visited.add(p)
            group.append(p)
            for adj in get_adjacent(*p):
                if board[adj] == 0:
                    liberties.add(adj)
                elif board[adj] == color and adj not in visited:
                    q.append(adj)
        return len(liberties), group
    
    me_set = set(me)
    opponent_set = set(opponent)
    occupied = me_set.union(opponent_set)
    board = np.zeros((20, 20), dtype=int)  # 1-based indexing
    for r, c in me:
        board[r, c] = 1
    for r, c in opponent:
        board[r, c] = 2
    
    empty_points = [(r, c) for r in range(1, 20) for c in range(1, 20) if (r, c) not in occupied]
    
    legal_moves = []
    for r, c in empty_points:
        captures = False
        
        # Temporarily place the stone
        board[r, c] = 1
        adj_opp = [(x, y) for x, y in get_adjacent(r, c) if board[x, y] == 2]
        
        # Check captures
        for x, y in adj_opp:
            lib, _ = count_liberties((x, y), 2, board)
            if lib == 0:
                captures = True
                break
        
        if captures:
            legal_moves.append((r, c))
            board[r, c] = 0
            continue
        
        # Check suicide
        lib, _ = count_liberties((r, c), 1, board)
        if lib > 0:
            legal_moves.append((r, c))
        board[r, c] = 0
    
    if not legal_moves:
        return ((0, 0), memory)
    
    # Evaluate moves
    best_score = -1
    best_move = legal_moves[0]
    for r, c in legal_moves:
        score = 0
        
        # Simulate placing the stone
        board[r, c] = 1
        
        # Capture score
        capture_count = 0
        adj_opp = [(x, y) for x, y in get_adjacent(r, c) if board[x, y] == 2]
        for x, y in adj_opp:
            lib, group = count_liberties((x, y), 2, board)
            if lib == 0:
                capture_count += len(group)
        score += capture_count * 100
        
        # Liberty score
        lib_count, _ = count_liberties((r, c), 1, board)
        score += lib_count * 10
        
        # Positional score
        if (r in (1, 19) and c in (1, 19)):
            score += 5
        elif r in (1, 19) or c in (1, 19):
            score += 3
        
        board[r, c] = 0
        
        if score > best_score or (score == best_score and (r, c) < best_move):
            best_score = score
            best_move = (r, c)
    
    return (best_move, memory)
