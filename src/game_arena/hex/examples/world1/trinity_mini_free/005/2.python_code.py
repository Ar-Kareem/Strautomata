
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Precompute adjacency list for each cell
    adj = {}
    for i in range(11):
        for j in range(11):
            neighbors = []
            for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                ni, nj = i + dx, j + dy
                if 0 <= ni < 11 and 0 <= nj < 11:
                    if (dx == -1 and dy == -1) or (dx == 1 and dy == 1):
                        continue
                    neighbors.append((ni, nj))
            adj[(i,j)] = neighbors

    current_stones = set(me)
    opponent_stones = set(opp)
    empty_cells = [(i, j) for i in range(11) for j in range(11) if (i, j) not in current_stones and (i, j) not in opponent_stones]

    # Check for winning moves for current player
    for cell in empty_cells:
        new_stones = current_stones | {cell}
        if is_connected(new_stones, adj):
            return cell

    # Check for opponent's winning moves and block
    for cell in empty_cells:
        new_opp_stones = opponent_stones | {cell}
        if is_connected(new_opp_stones, adj):
            return cell

    # Choose best expansion move
    best_cell = None
    best_score = -1
    for cell in empty_cells:
        if color == 'b':
            dist = min(cell[0], 10 - cell[0])
        else:
            dist = min(cell[1], 10 - cell[1])
        count = sum(1 for nb in adj[cell] if nb in current_stones)
        score = count * 10 + dist
        if score > best_score:
            best_score = score
            best_cell = cell

    return best_cell

def is_connected(stones, adj):
    if not stones:
        return True
    start = next(iter(stones))
    visited = set()
    stack = [start]
    visited.add(start)
    while stack:
        node = stack.pop()
        for neighbor in adj[node]:
            if neighbor in stones and neighbor not in visited:
                visited.add(neighbor)
                stack.append(neighbor)
    return len(visited) == len(stones)
