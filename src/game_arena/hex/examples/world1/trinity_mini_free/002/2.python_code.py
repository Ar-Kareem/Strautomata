
from collections import deque

def get_neighbors(i, j):
    neighbors = []
    if j - 1 >= 0:
        neighbors.append((i, j - 1))
    if j + 1 < 11:
        neighbors.append((i, j + 1))
    if i - 1 >= 0:
        neighbors.append((i - 1, j))
        neighbors.append((i - 1, j + 1))
    if i + 1 < 11:
        neighbors.append((i + 1, j))
        neighbors.append((i + 1, j - 1))
    return neighbors

def has_path(start_cells, target_cells, stones):
    if not start_cells:
        return False
    visited = set()
    queue = deque(start_cells)
    visited.update(start_cells)
    while queue:
        cell = queue.popleft()
        if cell in target_cells:
            return True
        for neighbor in get_neighbors(cell[0], cell[1]):
            if neighbor in stones and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return False

def policy(me, opp, color):
    empty = []
    for i in range(11):
        for j in range(11):
            if (i, j) not in me and (i, j) not in opp:
                empty.append((i, j))
    
    best_move = None
    best_score = -1
    
    for move in empty:
        r, c = move
        if color == 'b':
            new_me = me + [move]
            start_cells = [stone for stone in new_me if stone[0] == 0]
            target_cells = [stone for stone in new_me if stone[0] == 10]
            if has_path(start_cells, target_cells, new_me):
                score = 1000
            else:
                score = 0
                for neighbor in get_neighbors(r, c):
                    if neighbor in new_me and (neighbor[0] == 0 or neighbor[0] == 10):
                        score += 1
        else:
            new_opp = opp + [move]
            start_cells = [stone for stone in new_opp if stone[1] == 0]
            target_cells = [stone for stone in new_opp if stone[1] == 10]
            if has_path(start_cells, target_cells, new_opp):
                score = 1000
            else:
                score = 0
                for neighbor in get_neighbors(r, c):
                    if neighbor in new_opp and (neighbor[1] == 0 or neighbor[1] == 10):
                        score += 1
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
