
import numpy as np

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Initialize board state
    board = np.zeros((20, 20), dtype=int)  # 1-indexed, 0 empty, 1 me, 2 opponent
    for r, c in me:
        board[r, c] = 1
    for r, c in opponent:
        board[r, c] = 2
    
    def get_neighbors(r, c):
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                neighbors.append((nr, nc))
        return neighbors
    
    def get_group(r, c, player):
        if board[r, c] != player:
            return set()
        visited = set()
        group = set()
        stack = [(r, c)]
        
        while stack:
            pos = stack.pop()
            if pos in visited:
                continue
            visited.add(pos)
            group.add(pos)
            for nr, nc in get_neighbors(pos[0], pos[1]):
                if board[nr, nc] == player and (nr, nc) not in visited:
                    stack.append((nr, nc))
        return group
    
    def get_liberties(group):
        liberties = set()
        for r, c in group:
            for nr, nc in get_neighbors(r, c):
                if board[nr, nc] == 0:
                    liberties.add((nr, nc))
        return liberties
    
    # 1. Check for captures
    for r, c in opponent:
        group = get_group(r, c, 2)
        liberties = get_liberties(group)
        if len(liberties) == 1:
            move = list(liberties)[0]
            if board[move[0], move[1]] == 0:  # Empty
                return move
    
    # 2. Check for escape moves for own groups
    for r, c in me:
        group = get_group(r, c, 1)
        liberties = get_liberties(group)
        if len(liberties) == 1:
            move = list(liberties)[0]
            if board[move[0], move[1]] == 0:  # Empty
                return move
    
    # 3. Territory-focused move selection with center preference
    best_move = None
    best_score = -1
    
    # Simple heuristic: prefer moves that are not too close to edges and have some influence
    for r in range(3, 18):
        for c in range(3, 18):
            if board[r, c] != 0:
                continue
            
            # Calculate score based on distance to center and liberties
            center_dist = abs(r - 10) + abs(c - 10)
            score = 20 - center_dist  # Higher score for closer to center
            
            # Bonus for having more liberties
            liberties_count = 0
            for nr, nc in get_neighbors(r, c):
                if board[nr, nc] == 0:
                    liberties_count += 1
            score += liberties_count
            
            # Small bonus for being near own stones
            own_neighbors = 0
            for nr, nc in get_neighbors(r, c):
                if board[nr, nc] == 1:
                    own_neighbors += 1
            score += own_neighbors * 0.5
            
            if score > best_score:
                best_score = score
                best_move = (r, c)
    
    if best_move:
        return best_move
    
    # 4. Fallback to a reasonable move near existing stones
    for r, c in me:
        for nr, nc in get_neighbors(r, c):
            if board[nr, nc] == 0:
                return (nr, nc)
    
    # 5. Pass if no good move found
    return (0, 0)
