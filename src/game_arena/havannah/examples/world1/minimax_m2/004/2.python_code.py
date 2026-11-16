
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    # Create a 15x15 board grid initialized to 0 for empty
    board = [[0] * 15 for _ in range(15)]
    for r, c in me:
        board[r][c] = 1  # My stones
    for r, c in opp:
        board[r][c] = 2  # Opponent's stones

    # Find all valid empty cells
    empty_cells = []
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c] and board[r][c] == 0:
                empty_cells.append((r, c))

    if not empty_cells:
        # Should not happen since there is always a move, but return first cell if empty
        return empty_cells[0] if empty_cells else (0, 0)

    # Check for immediate winning move
    for move in empty_cells:
        r, c = move
        board[r][c] = 1
        if check_win(board, 1, valid_mask):
            return move
        board[r][c] = 0

    # Check for opponent's winning move and block it
    for move in empty_cells:
        r, c = move
        board[r][c] = 2
        if check_win(board, 2, valid_mask):
            board[r][c] = 0
            return move  # Block opponent by playing here
        board[r][c] = 0

    # Otherwise, choose a move that maximizes empty neighbors
    best_move = empty_cells[0]
    max_neighbors = -1
    for move in empty_cells:
        r, c = move
        count = 0
        # Check neighbors using the hex grid adjacency rules
        for dr, dc in [(-1, 0), (1, 0), (-1, -1), (0, -1), (0, 1), (-1, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 15 and 0 <= nc < 15 and valid_mask[nr][nc] and board[nr][nc] == 0:
                count += 1
        if count > max_neighbors:
            max_neighbors = count
            best_move = move
    return best_move

def check_win(board: list[list[int]], player: int, valid_mask) -> bool:
    """Check if the player has won by ring, bridge, or fork."""
    # Create a graph of the player's stones for connectivity
    graph = {}
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c] and board[r][c] == player:
                graph[(r, c)] = []
                # Add neighbors that are also player's stones
                for dr, dc in [(-1, 0), (1, 0), (-1, -1), (0, -1), (0, 1), (-1, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 15 and 0 <= nc < 15 and valid_mask[nr][nc] and board[nr][nc] == player:
                        graph[(r, c)].append((nr, nc))

    # Check for ring (cycle)
    if has_cycle(graph):
        return True

    # Check for bridge: path between two corners
    corners = get_corners(valid_mask)
    if len(corners) >= 2:
        # Check if any two corners are connected
        for i in range(len(corners)):
            for j in range(i + 1, len(corners)):
                if is_connected(graph, corners[i], corners[j]):
                    return True

    # Check for fork: path between three edges
    edges = get_edges(valid_mask)
    if len(edges) >= 3:
        # Check if any three edges are connected
        for i in range(len(edges)):
            for j in range(i + 1, len(edges)):
                for k in range(j + 1, len(edges)):
                    if is_connected_to_edge(graph, edges[i]) and is_connected_to_edge(graph, edges[j]) and is_connected_to_edge(graph, edges[k]):
                        return True

    return False

def get_corners(valid_mask) -> list[tuple[int, int]]:
    """Get the corner cells of the board."""
    corners = []
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c]:
                # Check if this cell is a corner (has only two neighbors)
                neighbors = 0
                for dr, dc in [(-1, 0), (1, 0), (-1, -1), (0, -1), (0, 1), (-1, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 15 and 0 <= nc < 15 and valid_mask[nr][nc]:
                        neighbors += 1
                if neighbors == 2:
                    corners.append((r, c))
    # There should be exactly six corners, but take up to six
    return corners[:6]

def get_edges(valid_mask) -> list[set[tuple[int, int]]]:
    """Get the six edges of the board as sets of cells."""
    edges = []
    # Top edge: r=0
    edge = set()
    for c in range(15):
        if valid_mask[0][c]:
            edge.add((0, c))
    edges.append(edge)
    # Bottom edge: r=14
    edge = set()
    for c in range(15):
        if valid_mask[14][c]:
            edge.add((14, c))
    edges.append(edge)
    # Left edge: c=0
    edge = set()
    for r in range(15):
        if valid_mask[r][0]:
            edge.add((r, 0))
    edges.append(edge)
    # Right edge: c=14
    edge = set()
    for r in range(15):
        if valid_mask[r][14]:
            edge.add((r, 14))
    edges.append(edge)
    # Top-left edge: cells where r=c
    edge = set()
    for r in range(15):
        c = r
        if 0 <= c < 15 and valid_mask[r][c]:
            edge.add((r, c))
    edges.append(edge)
    # Bottom-right edge: cells where r=14-c
    edge = set()
    for r in range(15):
        c = 14 - r
        if 0 <= c < 15 and valid_mask[r][c]:
            edge.add((r, c))
    edges.append(edge)
    return edges

def is_connected(graph: dict, start: tuple[int, int], end: tuple[int, int]) -> bool:
    """Check if there is a path between start and end in the graph."""
    if start not in graph or end not in graph:
        return False
    visited = set()
    stack = [start]
    while stack:
        node = stack.pop()
        if node == end:
            return True
        if node not in visited:
            visited.add(node)
            stack.extend(graph[node])
    return False

def is_connected_to_edge(graph: dict, edge: set[tuple[int, int]]) -> bool:
    """Check if the graph has a path to any cell in the edge."""
    for cell in edge:
        if cell in graph:
            return True
    return False

def has_cycle(graph: dict) -> bool:
    """Check if the graph has a cycle."""
    visited = set()
    for node in graph:
        if node not in visited:
            if dfs_cycle(graph, node, visited, set()):
                return True
    return False

def dfs_cycle(graph: dict, node: tuple[int, int], visited: set, parent: set) -> bool:
    """DFS to detect cycle in the graph."""
    visited.add(node)
    parent.add(node)
    for neighbor in graph[node]:
        if neighbor not in visited:
            if dfs_cycle(graph, neighbor, visited, parent):
                return True
        elif neighbor in parent:
            return True
    parent.remove(node)
    return False
