
import numpy as np
import heapq
from collections import defaultdict
import time
import random

# ---------- Hex adjacency ----------
# For cell (r, c) on 11x11, neighbors are all 8 except (r-1, c-1) and (r+1, c+1)

def neighbors(r, c, size=11):
    """Return list of valid neighbor coords for hex cell (r, c)."""
    dirs = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
    result = []
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if 0 <= nr < size and 0 <= nc < size:
            result.append((nr, nc))
    return result

# Precompute neighbor graph
SIZE = 11
ALL_CELLS = [(r, c) for r in range(SIZE) for c in range(SIZE)]
NEIGHBORS = {cell: neighbors(cell[0], cell[1], SIZE) for cell in ALL_CELLS}

# Virtual edge nodes for connections
# Black: top (row -1) and bottom (row SIZE) edges represented as special keys
TOP_EDGE = (-1, -1)
BOTTOM_EDGE = (SIZE, SIZE)
LEFT_EDGE = (-2, -2)
RIGHT_EDGE = (SIZE+1, SIZE+1)

def edge_neighbors(cell, color, size=SIZE):
    """Return edge nodes if cell touches the player's target sides."""
    r, c = cell
    res = []
    if color == 'b':
        if r == 0:
            res.append(TOP_EDGE)
        if r == size - 1:
            res.append(BOTTOM_EDGE)
    else:  # white
        if c == 0:
            res.append(LEFT_EDGE)
        if c == size - 1:
            res.append(RIGHT_EDGE)
    return res

# ---------- Dijkstra distance (cost: own stones 0, empty 1, opponent ∞) ----------
def dijkstra_distances(stones, opp_stones, color, size=SIZE):
    """Compute min distance from start edge to each cell and to goal edge.
    Returns dict of distance to each node (including edges) and the goal distance."""
    start_edge = TOP_EDGE if color == 'b' else LEFT_EDGE
    goal_edge = BOTTOM_EDGE if color == 'b' else RIGHT_EDGE
    
    stone_set = set(stones)
    opp_set = set(opp_stones)
    
    # Initialize distances
    dist = {}
    # All board cells + edges
    nodes = list(ALL_CELLS) + [start_edge, goal_edge]
    for n in nodes:
        dist[n] = float('inf')
    dist[start_edge] = 0
    
    pq = [(0, start_edge)]
    
    while pq:
        d, node = heapq.heappop(pq)
        if d != dist[node]:
            continue
        if node == goal_edge:
            break
        
        # Neighbors of this node
        if node == start_edge:
            # Start edge connects to all cells on start row/col
            if color == 'b':
                next_nodes = [(0, c) for c in range(size) if (0, c) not in opp_set]
            else:
                next_nodes = [(r, 0) for r in range(size) if (r, 0) not in opp_set]
        elif node == goal_edge:
            continue  # We don't expand from goal
        else:
            r, c = node
            base_neighbors = NEIGHBORS[(r, c)]
            # Add edge connections
            edge_nodes = edge_neighbors((r, c), color, size)
            next_nodes = base_neighbors + edge_nodes
        
        for nb in next_nodes:
            if nb in opp_set:
                continue  # Can't traverse opponent stones
            # Cost: 0 if our stone, 1 if empty
            if nb == start_edge or nb == goal_edge:
                cost = 0  # edges are always "ours" conceptually
            elif nb in stone_set:
                cost = 0
            else:
                cost = 1  # empty cell
            nd = d + cost
            if nd < dist.get(nb, float('inf')):
                dist[nb] = nd
                heapq.heappush(pq, (nd, nb))
    
    return dist

def get_path_cells(dist, start_edge, goal_edge, stones, opp_stones, color, size=SIZE):
    """Backtrack from goal to start to get cells on shortest path."""
    if dist.get(goal_edge, float('inf')) == float('inf'):
        return set()
    stone_set = set(stones)
    opp_set = set(opp_stones)
    
    path_cells = set()
    current = goal_edge
    while current != start_edge:
        if current != goal_edge and current != start_edge:
            path_cells.add(current)
        # Find predecessor with correct distance
        r, c = current
        best_pred = None
        best_d = float('inf')
        for nb in NEIGHBORS.get((r, c), []):
            if nb in opp_set:
                continue
            cost = 0 if nb in stone_set else 1
            if dist.get(nb, float('inf')) + cost == dist[current]:
                if dist[nb] < best_d:
                    best_d = dist[nb]
                    best_pred = nb
        if best_pred is None:
            # Maybe current is on edge row
            if color == 'b' and current[0] == size - 1 and current[0] == r:
                # came from top/bottom edge
                pass
            break
        current = best_pred
    return path_cells

# ---------- Heuristic evaluation: who is winning? ----------
def evaluate_position(me, opp, color):
    """Returns (my_dist, opp_dist) to goal edges."""
    my_dist_dict = dijkstra_distances(me, opp, color)
    opp_color = 'w' if color == 'b' else 'b'
    opp_dist_dict = dijkstra_distances(opp, me, opp_color)
    
    my_goal = BOTTOM_EDGE if color == 'b' else RIGHT_EDGE
    opp_goal = RIGHT_EDGE if opp_color == 'w' else BOTTOM_EDGE
    
    my_dist = my_dist_dict.get(my_goal, float('inf'))
    opp_dist = opp_dist_dict.get(opp_goal, float('inf'))
    return my_dist, opp_dist

# ---------- Generate candidate moves ----------
def get_candidate_moves(me, opp, color, max_candidates=30):
    """Generate a set of promising candidate moves."""
    candidates = set()
    occupied = set(me) | set(opp)
    empty = [cell for cell in ALL_CELLS if cell not in occupied]
    
    if not me and not opp:
        # First move: play center
        return {(SIZE//2, SIZE//2)}
    
    # 1. Cells adjacent to any stone (mine or opponent's)
    all_stones = me + opp
    for r, c in all_stones:
        for nb in NEIGHBORS[(r, c)]:
            if nb not in occupied:
                candidates.add(nb)
    
    # 2. Cells on our shortest path
    my_dist_dict = dijkstra_distances(me, opp, color)
    start_edge = TOP_EDGE if color == 'b' else LEFT_EDGE
    goal_edge = BOTTOM_EDGE if color == 'b' else RIGHT_EDGE
    my_path = get_path_cells(my_dist_dict, start_edge, goal_edge, me, opp, color)
    for cell in my_path:
        if cell not in occupied:
            candidates.add(cell)
    
    # 3. Cells on opponent's shortest path (to block)
    opp_color = 'w' if color == 'b' else 'b'
    opp_dist_dict = dijkstra_distances(opp, me, opp_color)
    opp_start = TOP_EDGE if opp_color == 'b' else LEFT_EDGE
    opp_goal = BOTTOM_EDGE if opp_color == 'b' else RIGHT_EDGE
    opp_path = get_path_cells(opp_dist_dict, opp_start, opp_goal, opp, me, opp_color)
    for cell in opp_path:
        if cell not in occupied:
            candidates.add(cell)
    
    # 4. Bridge pattern cells (cells that form a bridge with our stones)
    for r, c in me:
        # Check for potential bridges: two stones separated by one empty cell in certain patterns
        for nb1 in NEIGHBORS[(r, c)]:
            if nb1 in me:
                # They share two common neighbors - those are bridge cells
                common = set(NEIGHBORS[(r, c)]) & set(NEIGHBORS[nb1])
                for bridge_cell in common:
                    if bridge_cell not in occupied:
                        candidates.add(bridge_cell)
    
    # If not enough candidates, add some near our stones
    if len(candidates) < 15:
        for r, c in me:
            for nb in NEIGHBORS[(r, c)]:
                for nnb in NEIGHBORS[nb]:
                    if nnb not in occupied:
                        candidates.add(nnb)
    
    # Limit candidates
    if len(candidates) > max_candidates:
        # Score candidates by heuristic (reduce opponent distance or our distance)
        my_dist, opp_dist = evaluate_position(me, opp, color)
        scored = []
        for cand in candidates:
            # Simulate placing
            new_me = me + [cand]
            new_dist_dict = dijkstra_distances(new_me, opp, color)
            new_my_dist = new_dist_dict.get(goal_edge, float('inf'))
            new_opp_dist_dict = dijkstra_distances(opp, new_me, opp_color)
            new_opp_dist = new_opp_dist_dict.get(opp_goal, float('inf'))
            score = (my_dist - new_my_dist) * 2 + (new_opp_dist - opp_dist)
            scored.append((score, cand))
        scored.sort(reverse=True)
        candidates = {cand for _, cand in scored[:max_candidates]}
    
    return list(candidates)

# ---------- Fast win check using Dijkstra ----------
def check_win(stones, color):
    """Return True if stones connect their sides."""
    dist = dijkstra_distances(stones, [], color)  # empty opponent
    goal = BOTTOM_EDGE if color == 'b' else RIGHT_EDGE
    return dist.get(goal, float('inf')) == 0

# ---------- MCTS Node ----------
class MCTSNode:
    def __init__(self, move=None, parent=None):
        self.move = move  # (r, c) that led to this node
        self.parent = parent
        self.children = {}
        self.visits = 0
        self.wins = 0
        # AMAF stats
        self.amaf_visits = defaultdict(int)
        self.amaf_wins = defaultdict(int)

# ---------- MCTS with AMAF ----------
def mcts_search(me, opp, color, time_budget=0.9):
    """Run MCTS from current state and return best move."""
    start_time = time.time()
    
    occupied = set(me) | set(opp)
    candidates = get_candidate_moves(me, opp, color)
    if not candidates:
        # fallback: any empty cell
        for cell in ALL_CELLS:
            if cell not in occupied:
                candidates.append(cell)
    
    # Root node represents current state
    root = MCTSNode()
    
    # Track all moves in tree for AMAF
    all_moves = set(candidates)
    
    iteration = 0
    while time.time() - start_time < time_budget:
        iteration += 1
        # Selection & Expansion
        node = root
        sim_me = list(me)
        sim_opp = list(opp)
        sim_color = color
        path_moves = []  # moves made in this iteration
        
        # Tree traversal
        while node.children:
            # UCT selection
            best_child = None
            best_uct = -float('inf')
            total_visits = node.visits
            for move, child in node.children.items():
                if child.visits == 0:
                    uct = float('inf')
                else:
                    exploit = child.wins / child.visits
                    explore = np.sqrt(2 * np.log(total_visits + 1) / child.visits)
                    uct = exploit + explore
                if uct > best_uct:
                    best_uct = uct
                    best_child = child
            
            node = best_child
            # Apply move
            move = node.move
            sim_me.append(move)
            path_moves.append(move)
            # Switch turns
            sim_me, sim_opp = sim_opp, sim_me
            sim_color = 'w' if sim_color == 'b' else 'b'
        
        # Expansion: add children for untried moves from this state
        occupied_sim = set(sim_me) | set(sim_opp)
        untried = [m for m in all_moves if m not in occupied_sim]
        if not untried:
            # Get candidates for this state
            untried = get_candidate_moves(sim_me, sim_opp, sim_color)
            untried = [m for m in untried if m not in occupied_sim]
        
        if untried and node.visits > 0:
            # Expand one child
            move = random.choice(untried)
            child = MCTSNode(move=move, parent=node)
            node.children[move] = child
            node = child
            sim_me.append(move)
            path_moves.append(move)
            sim_me, sim_opp = sim_opp, sim_me
            sim_color = 'w' if sim_color == 'b' else 'b'
        
        # Rollout (simulation)
        rollout_result = simulate_rollout(sim_me, sim_opp, sim_color, path_moves)
        
        # Backpropagation
        winner = rollout_result  # 'b' or 'w'
        back_node = node
        while back_node is not None:
            back_node.visits += 1
            if (back_node == root and winner == color) or \
               (back_node != root and back_node.parent is not None):
                # Determine if this node's side (the player who made the move to reach it) won
                # The node's move was made by the player opposite to the current sim_color at that point
                pass
            
            # Simpler: track if the player who just moved won
            # We'll use a simpler AMAF approach
            
            back_node = back_node.parent
        
        # AMAF backprop: for all moves in path, update AMAF stats
        for move in path_moves:
            root.amaf_visits[move] += 1
            if winner == color:
                root.amaf_wins[move] += 1
        
        # Also backprop wins normally
        back_node = node
        while back_node is not None:
            back_node.visits += 1
            # Determine which player made the move to reach back_node
            # If back_node is root, it's neutral
            # Else, the parent's turn made the move
            if back_node.parent is not None:
                # The move that led to back_node was made by grandparent's opponent
                # This is getting complex; simplify:
                # We'll just track from the perspective of root's color
                pass
            back_node = back_node.parent
        
        # Simplified backprop: just update from node up to root
        # winner is from the perspective of the player who made the *last* move? No.
        # Let's do proper backprop:
        back_node = node
        current_winner_perspective = winner  # 'b' or 'w'
        while back_node is not None:
            back_node.visits += 1
            if back_node != root:
                # The player who moved to reach back_node is:
                # If back_node is at depth d, the player is the one who played at depth d-1
                # We need to know which color that was
                # Since we alternate starting from 'color' at root, depth parity determines it
                depth = 0
                n = back_node
                while n.parent is not None:
                    depth += 1
                    n = n.parent
                player_at_node = color if depth % 2 == 0 else ('w' if color == 'b' else 'b')
                if current_winner_perspective == player_at_node:
                    back_node.wins += 1
            back_node = back_node.parent
    
    # Choose best move: highest visit count
    best_move = None
    best_visits = -1
    for move in candidates:
        # Combine real visits and AMAF visits
        amaf_v = root.amaf_visits.get(move, 0)
        amaf_w = root.amaf_wins.get(move, 0)
        if move in root.children:
            child = root.children[move]
            total_visits = child.visits + amaf_v * 0.5
        else:
            total_visits = amaf_v * 0.5
        if total_visits > best_visits:
            best_visits = total_visits
            best_move = move
    
    if best_move is None:
        # Fallback: heuristic choice
        best_move = candidates[0] if candidates else (SIZE//2, SIZE//2)
    
    return best_move

def simulate_rollout(me, opp, color, path_moves, max_depth=20):
    """Run a random rollout until win or max depth."""
    sim_me = list(me)
    sim_opp = list(opp)
    sim_color = color
    
    for _ in range(max_depth):
        # Check win
        if check_win(sim_me, sim_color):
            return sim_color
        if check_win(sim_opp, 'w' if sim_color == 'b' else 'b'):
            return 'w' if sim_color == 'b' else 'b'
        
        occupied = set(sim_me) | set(sim_opp)
        
        # Get candidates with heuristic bias
        candidates = get_candidate_moves(sim_me, sim_opp, sim_color, max_candidates=15)
        if not candidates:
            empty = [cell for cell in ALL_CELLS if cell not in occupied]
            if not empty:
                break
            candidates = empty[:15]
        
        # Bias towards cells that reduce our distance
        start_edge = TOP_EDGE if sim_color == 'b' else LEFT_EDGE
        goal_edge = BOTTOM_EDGE if sim_color == 'b' else RIGHT_EDGE
        current_dist_dict = dijkstra_distances(sim_me, sim_opp, sim_color)
        current_dist = current_dist_dict.get(goal_edge, float('inf'))
        
        move_scores = []
        for cand in candidates[:10]:  # evaluate up to 10
            new_me = sim_me + [cand]
            new_dist_dict = dijkstra_distances(new_me, sim_opp, sim_color)
            new_dist = new_dist_dict.get(goal_edge, float('inf'))
            improvement = current_dist - new_dist
            move_scores.append((improvement + random.random() * 0.5, cand))
        
        if move_scores:
            move_scores.sort(reverse=True)
            move = move_scores[0][1]
        else:
            move = random.choice(candidates)
        
        sim_me.append(move)
        path_moves.append(move)
        sim_me, sim_opp = sim_opp, sim_me
        sim_color = 'w' if sim_color == 'b' else 'b'
    
    # No winner: evaluate distances
    my_dist, opp_dist = evaluate_position(sim_me, sim_opp, color)
    if my_dist < opp_dist:
        return color
    else:
        return 'w' if color == 'b' else 'b'

# ---------- Main policy function ----------
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """Return the next move for Hex."""
    # Quick opening book: center or near center
    if not me and not opp:
        return (5, 5)
    
    # If only one move played, respond near center
    if len(opp) == 1 and len(me) == 0:
        oc = opp[0]
        # Play adjacent to opponent's move towards center
        r, c = 5, 5
        if oc == (5, 5):
            return (5, 4)
        return (5, 5)
    
    # Use MCTS
    move = mcts_search(me, opp, color, time_budget=0.85)
    
    # Safety: ensure move is legal
    occupied = set(me) | set(opp)
    if move in occupied or move[0] < 0 or move[0] >= SIZE or move[1] < 0 or move[1] >= SIZE:
        # Fallback: any empty cell
        for r in range(SIZE):
            for c in range(SIZE):
                if (r, c) not in occupied:
                    return (r, c)
    
    return move

