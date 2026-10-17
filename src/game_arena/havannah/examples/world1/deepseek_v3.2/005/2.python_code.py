
import numpy as np
from collections import deque

# Neighbor offsets for hexagonal grid: (row, col) offsets
# For even rows? Let's handle generic offsets: 
# In a hex grid represented as offset coordinates (even-r layout):
# From (r, c), neighbors are: (r-1, c), (r+1, c), (r, c-1), (r, c+1),
# and for even r: (r-1, c-1), (r+1, c-1)
# for odd r: (r-1, c+1), (r+1, c+1)
# But we must adjust to our 2D array indexing.
def get_neighbors(r, c, board_size=15):
    neighbors = []
    # orthogonal neighbors
    if r > 0:
        neighbors.append((r-1, c))
    if r < board_size - 1:
        neighbors.append((r+1, c))
    if c > 0:
        neighbors.append((r, c-1))
    if c < board_size - 1:
        neighbors.append((r, c+1))
    # diagonal neighbors depend on row parity
    if r % 2 == 0:  # even row
        if r > 0 and c > 0:
            neighbors.append((r-1, c-1))
        if r < board_size - 1 and c > 0:
            neighbors.append((r+1, c-1))
    else:  # odd row
        if r > 0 and c < board_size - 1:
            neighbors.append((r-1, c+1))
        if r < board_size - 1 and c < board_size - 1:
            neighbors.append((r+1, c+1))
    return neighbors

def get_all_neighbors_set(board_size=15):
    neigh_map = {}
    for r in range(board_size):
        for c in range(board_size):
            neigh_map[(r, c)] = get_neighbors(r, c, board_size)
    return neigh_map

NEIGHBOR_MAP = get_all_neighbors_set(15)

# Helper: board matrix from stone lists
def make_board(me, opp, size=15):
    board = [[0 for _ in range(size)] for _ in range(size)]
    for r, c in me:
        board[r][c] = 1
    for r, c in opp:
        board[r][c] = 2
    return board

# Floodfill to find connected component of same color
def component(color, start, board, visited):
    comp = []
    stack = [start]
    while stack:
        r, c = stack.pop()
        if visited[r][c]:
            continue
        visited[r][c] = True
        comp.append((r, c))
        for nr, nc in NEIGHBOR_MAP[(r, c)]:
            if board[nr][nc] == color:
                stack.append((nr, nc))
    return comp

# Find all connected components of a color
def all_components(color, board, size=15):
    visited = [[False]*size for _ in range(size)]
    comps = []
    for r in range(size):
        for c in range(size):
            if board[r][c] == color and not visited[r][c]:
                comp = component(color, (r, c), board, visited)
                comps.append(comp)
    return comps

# Check if component touches a corner
def touches_corner(comp, size=15):
    corners = [(0,0), (0,size-1), (size-1,0), (size-1,size-1)]
    for r, c in comp:
        if (r, c) in corners:
            return True
    return False

# Check if component touches an edge (excluding corners)
def touches_edge(comp, size=15):
    for r, c in comp:
        if r == 0 or r == size-1 or c == 0 or c == size-1:
            if not ((r==0 and c==0) or (r==0 and c==size-1) or
                    (r==size-1 and c==0) or (r==size-1 and c==size-1)):
                return True
    return False

# Check for bridge: component touches >= 2 corners
def is_bridge(comp, size=15):
    corners_touched = set()
    corners = [(0,0), (0,size-1), (size-1,0), (size-1,size-1)]
    for r, c in comp:
        if (r, c) in corners:
            corners_touched.add((r, c))
    return len(corners_touched) >= 2

# Check for fork: component touches >= 3 edges (edges excluding corners)
def is_fork(comp, size=15):
    edges_touched = set()
    for r, c in comp:
        if r == 0:
            edges_touched.add('top')
        if r == size-1:
            edges_touched.add('bottom')
        if c == 0:
            edges_touched.add('left')
        if c == size-1:
            edges_touched.add('right')
    # If both top/bottom, they could be same edge? No, they're opposite.
    # But for fork, need 3 distinct edges among top, bottom, left, right.
    return len(edges_touched) >= 3

# Check for ring: loop around >=1 cell
# Simplification: detect if there's a cycle in the component graph via DFS
def has_cycle_in_component(comp):
    if len(comp) < 6:  # minimum ring size in hex grid is 6
        return False
    # map from node to list of neighbors within comp
    comp_set = set(comp)
    adj = {node: [] for node in comp}
    for r, c in comp:
        for nr, nc in NEIGHBOR_MAP[(r, c)]:
            if (nr, nc) in comp_set:
                adj[(r, c)].append((nr, nc))
    visited = {}
    for node in comp:
        visited[node] = 0
    for node in comp:
        if visited[node] == 0:
            stack = [(node, None)]
            while stack:
                v, parent = stack.pop()
                if visited[v] == 1:
                    continue
                visited[v] = 1
                for nb in adj[v]:
                    if nb == parent:
                        continue
                    if visited[nb] == 1:
                        return True
                    stack.append((nb, v))
    return False

def winning_move_for(color, board, size=15):
    # Check all empty cells if placing stone of 'color' wins
    empty = [(r, c) for r in range(size) for c in range(size) if board[r][c] == 0]
    for r, c in empty:
        board[r][c] = color
        comps = all_components(color, board, size)
        for comp in comps:
            if is_bridge(comp, size) or is_fork(comp, size) or has_cycle_in_component(comp):
                board[r][c] = 0
                return (r, c)
        board[r][c] = 0
    return None

def threat_move_for(color, board, size=15):
    # If opponent can win next move, return that move (to block or to win ourselves)
    opponent = 3 - color  # 1 -> 2, 2 -> 1
    return winning_move_for(opponent, board, size)

def heuristic_score_move(r, c, me, opp, size=15):
    # Compute a score for placing stone at (r, c)
    board = make_board(me, opp, size)
    board[r][c] = 1
    # Score components:
    score = 0
    # 1. Connectivity: number of friendly neighbors
    for nr, nc in NEIGHBOR_MAP[(r, c)]:
        if board[nr][nc] == 1:
            score += 3
        elif board[nr][nc] == 2:
            score -= 1
    # 2. Near edges: good for bridges/forks
    edge_dist = min(r, size-1-r, c, size-1-c)
    score += (size - edge_dist) * 2
    # 3. Central control bonus
    center = size // 2
    dist_from_center = abs(r - center) + abs(c - center)
    score += (size - dist_from_center)
    # 4. Forming potential rings: if it connects two separate friendly groups
    # Simpler: if it connects >=2 separate comps, bonus
    before_comps = all_components(1, make_board(me, opp, size), size)
    after_comps = all_components(1, board, size)
    if len(after_comps) < len(before_comps):  # merged components
        score += 10
    return score

def policy(me, opp, valid_mask):
    size = len(valid_mask)
    board = make_board(me, opp, size)
    # 1. Immediate win
    win_move = winning_move_for(1, board, size)
    if win_move is not None:
        return win_move
    # 2. Block opponent win
    threat = threat_move_for(1, board, size)
    if threat is not None:
        return threat
    # 3. Choose best heuristic move
    best_score = -10**9
    best_move = None
    for r in range(size):
        for c in range(size):
            if valid_mask[r][c] and board[r][c] == 0:
                score = heuristic_score_move(r, c, me, opp, size)
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    if best_move is None:
        # fallback: first valid move
        for r in range(size):
            for c in range(size):
                if valid_mask[r][c] and board[r][c] == 0:
                    return (r, c)
    return best_move
