
from collections import deque

def policy(me, opp, color):
    def get_neighbors(cell):
        i, j = cell
        neighbors = [
            (i, j + 1),  # right
            (i, j - 1),  # left
            (i - 1, j),  # top
            (i - 1, j + 1),  # top-right
            (i + 1, j),  # bottom
            (i + 1, j - 1),  # bottom-left
        ]
        return [(r, c) for r, c in neighbors if 0 <= r < 11 and 0 <= c < 11]

    def can_win(me_set, move):
        new_me = me_set | {move}
        start = []
        targets = set()

        if color == 'b':
            starts = [cell for cell in new_me if cell[0] == 0]
            targets = {(10, c) for c in range(11)}
        else:
            starts = [cell for cell in new_me if cell[1] == 0]
            targets = {(r, 9) for r in range(11)}

        if not starts:
            return False

        visited = set(starts)
        queue = deque(starts)
        while queue:
            current = queue.popleft()
            if current in targets:
                return True
            for neighbor in get_neighbors(*current):
                if neighbor in new_me and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    me_set = set(me)
    opp_set = set(opp)
    empty_cells = [(i, j) for i in range(11) for j in range(11) 
                   if (i, j) not in me_set and (i, j) not in opp_set]

    for cell in empty_cells:
        if can_win(me_set, cell):
            return cell

    scored_moves = []
    for cell in empty_cells:
        i, j = cell
        adj_count = sum(1 for neighbor in get_neighbors(cell) if neighbor in me_set)
        score = adj_count

        if color == 'b':
            score += 10 * i + j  # Prioritize bottom rows
        elif color == 'w':
            score += 10 * j + i  # Prioritize right columns

        scored_moves.append((-score, i, j, adj_count, cell))

    scored_moves.sort()

    if scored_moves:
        best = scored_moves[0]
        return best[3]
    return empty_cells[0] if empty_cells else (0, 0)
