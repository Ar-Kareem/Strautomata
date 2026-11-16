
from collections import deque
import math

def get_neighbors(r: int, c: int, valid_mask):
    N = len(valid_mask)
    if c % 2 == 1:
        deltas = ((-1, 0), (1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1))
    else:
        deltas = ((-1, 0), (1, 0), (0, -1), (1, -1), (0, 1), (1, 1))
    nbrs = []
    for dr, dc in deltas:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N and valid_mask[nr][nc]:
            nbrs.append((nr, nc))
    return nbrs

def analyze_board(valid_mask):
    N = len(valid_mask)
    board_cells = [(r, c) for r in range(N) for c in range(N) if valid_mask[r][c]]
    board_set = set(board_cells)
    
    nbrs = {u: get_neighbors(u[0], u[1], valid_mask) for u in board_cells}
    boundary_cells = [u for u in board_cells if len(nbrs[u]) < 6]
    boundary_set = set(boundary_cells)
    
    # Corners are boundary cells with degree <= 3
    corners = [u for u in boundary_cells if len(nbrs[u]) <= 3]
    if len(corners) != 6:
        sorted_b = sorted(boundary_cells, key=lambda u: len(nbrs[u]))
        corners = sorted_b[:6]
    corner_set = set(corners)
    
    # Trace the boundary cycle to partition into 6 edges
    b_adj = {u: [v for v in nbrs[u] if v in boundary_set] for u in boundary_cells}
    cycle = []
    visited = set()
    curr = corners[0]
    while len(cycle) < len(boundary_cells):
        cycle.append(curr)
        visited.add(curr)
        nxt = [v for v in b_adj[curr] if v not in visited]
        if not nxt:
            break
        curr = nxt[0]
        
    cycle_corners = [u for u in cycle if u in corner_set]
    edges = [[] for _ in range(6)]
    edges_dict = {}
    
    if len(cycle_corners) == 6:
        indices = [cycle.index(c) for c in cycle_corners]
        for i in range(6):
            c_idx = indices[i]
            next_idx = indices[(i + 1) % 6]
            if next_idx > c_idx:
                edge_list = cycle[c_idx + 1:next_idx]
            else:
                edge_list = cycle[c_idx + 1:] + cycle[:next_idx]
            edges[i] = edge_list
            for cell in edge_list:
                edges_dict[cell] = i
    else:
        for u in boundary_cells:
            if u not in corner_set:
                angle = math.atan2(u[0] - 7, u[1] - 7) + math.pi
                sec = int(angle / (2 * math.pi / 6)) % 6
                edges[sec].append(u)
                edges_dict[u] = sec
                
    return board_cells, board_set, nbrs, boundary_cells, boundary_set, corners, corner_set, edges, edges_dict

def check_ring(comp_set, board_set, nbrs, boundary_set):
    other_cells = board_set - comp_set
    queue = [u for u in other_cells if u in boundary_set]
    visited = set(queue)
    for u in queue:
        for v in nbrs[u]:
            if v in other_cells and v not in visited:
                visited.add(v)
                queue.append(v)
    return len(visited) < len(other_cells)

def check_move_ring(m, comp_set, player_stones, board_set, nbrs, boundary_set):
    if check_ring(comp_set, board_set, nbrs, boundary_set):
        return True
    for f in nbrs[m]:
        if f in player_stones and f not in boundary_set:
            if check_ring(comp_set - {f}, board_set, nbrs, boundary_set):
                return True
    return False

def check_win(player_stones, new_move, corners, edges_dict, nbrs, board_set, boundary_set):
    current_stones = player_stones | {new_move}
    q = [new_move]
    visited = {new_move}
    for curr in q:
        for nxt in nbrs[curr]:
            if nxt in current_stones and nxt not in visited:
                visited.add(nxt)
                q.append(nxt)
                
    # 1. Bridge
    c_count = sum(1 for c in corners if c in visited)
    if c_count >= 2:
        return True
        
    # 2. Fork
    e_set = {edges_dict[c] for c in visited if c in edges_dict}
    if len(e_set) >= 3:
        return True
        
    # 3. Ring
    nbr_count = sum(1 for nxt in nbrs[new_move] if nxt in player_stones)
    if nbr_count >= 2:
        if check_move_ring(new_move, visited, player_stones, board_set, nbrs, boundary_set):
            return True
            
    return False

def compute_distances(targets, my_stones, opp_stones, nbrs, board_cells):
    dist = {u: 999 for u in board_cells}
    dq = deque()
    
    for t in targets:
        if t in opp_stones:
            continue
        cost = 0 if t in my_stones else 1
        dist[t] = cost
        if cost == 0:
            dq.appendleft((cost, t))
        else:
            dq.append((cost, t))
            
    while dq:
        d, u = dq.popleft()
        if d > dist[u]:
            continue
        for v in nbrs[u]:
            if v in opp_stones:
                continue
            weight = 0 if v in my_stones else 1
            new_d = d + weight
            if new_d < dist[v]:
                dist[v] = new_d
                if weight == 0:
                    dq.appendleft((new_d, v))
                else:
                    dq.append((new_d, v))
    return dist

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    board_cells, board_set, nbrs, boundary_cells, boundary_set, corners, corner_set, edges, edges_dict = analyze_board(valid_mask)
    
    my_set = set(me)
    opp_set = set(opp)
    empty_cells = [u for u in board_cells if u not in my_set and u not in opp_set]
    empty_set = set(empty_cells)
    
    if not empty_cells:
        return (7, 7)
        
    # Opening move towards the center
    center = (7, 7)
    if not my_set and not opp_set:
        if center in empty_set:
            return center
    if len(my_set) + len(opp_set) == 1 and center in empty_set:
        return center

    # 1. Immediate Win for Me
    for m in empty_cells:
        if check_win(my_set, m, corners, edges_dict, nbrs, board_set, boundary_set):
            return m
            
    # 2. Immediate Block for Opponent's Win
    opp_wins = [m for m in empty_cells if check_win(opp_set, m, corners, edges_dict, nbrs, board_set, boundary_set)]
    if len(opp_wins) == 1:
        return opp_wins[0]
    elif len(opp_wins) > 1:
        # Opponent has multiple winning moves; prioritize blocking the most central/connected one
        return max(opp_wins, key=lambda m: sum(1 for v in nbrs[m] if v in opp_set))

    # 3. Shortest Path Distance Maps (0-1 BFS)
    my_c_dists = [compute_distances([c], my_set, opp_set, nbrs, board_cells) for c in corners]
    my_e_dists = [compute_distances(edges[i], my_set, opp_set, nbrs, board_cells) for i in range(6)]
    opp_c_dists = [compute_distances([c], opp_set, my_set, nbrs, board_cells) for c in corners]
    opp_e_dists = [compute_distances(edges[i], opp_set, my_set, nbrs, board_cells) for i in range(6)]

    def evaluate_move(m):
        my_b = min(my_c_dists[i][m] + my_c_dists[j][m] - 1 for i in range(6) for j in range(i + 1, 6))
        my_e_vals = sorted(my_e_dists[e][m] for e in range(6))
        my_f = my_e_vals[0] + my_e_vals[1] + my_e_vals[2] - 2
        
        opp_b = min(opp_c_dists[i][m] + opp_c_dists[j][m] - 1 for i in range(6) for j in range(i + 1, 6))
        opp_e_vals = sorted(opp_e_dists[e][m] for e in range(6))
        opp_f = opp_e_vals[0] + opp_e_vals[1] + opp_e_vals[2] - 2

        score = 0.0
        score += max(0, 15 - my_b) * 45.0
        score += max(0, 15 - my_f) * 45.0
        score += max(0, 15 - opp_b) * 38.0
        score += max(0, 15 - opp_f) * 38.0
        
        if my_b <= 2:
            score += 600.0
        if my_f <= 2:
            score += 600.0
        if opp_b <= 2:
            score += 500.0
        if opp_f <= 2:
            score += 500.0
            
        my_nbrs = sum(1 for v in nbrs[m] if v in my_set)
        opp_nbrs = sum(1 for v in nbrs[m] if v in opp_set)
        
        if my_nbrs == 1:
            score += 20.0
        elif my_nbrs == 2:
            score += 35.0
        elif my_nbrs >= 3:
            score += 25.0
            
        score += opp_nbrs * 10.0
        
        # Virtual connection (two-bridge) bonus
        for v in nbrs[m]:
            if v in empty_set:
                for w in nbrs[v]:
                    if w in my_set and w != m and w not in nbrs[m]:
                        shared = sum(1 for s in nbrs[m] if s in nbrs[w] and s in empty_set)
                        if shared >= 2:
                            score += 15.0

        # Centrality
        dist_c = abs(m[0] - 7) + abs(m[1] - 7)
        total_st = len(my_set) + len(opp_set)
        c_weight = max(0.0, (30 - total_st) / 30.0) * 8.0
        score -= dist_c * c_weight
        
        return score

    # Sort empty cells by heuristic potential
    scored_moves = [(evaluate_move(m), m) for m in empty_cells]
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    
    top_candidates = [m for _, m in scored_moves[:15]]

    # 4. 2-Ply Search: Double-Threat Creation
    for m in top_candidates:
        test_my = my_set | {m}
        threat_count = 0
        for m2 in empty_cells:
            if m2 != m and check_win(test_my, m2, corners, edges_dict, nbrs, board_set, boundary_set):
                threat_count += 1
                if threat_count >= 2:
                    return m

    # 5. Prevent Opponent Double-Threats
    opp_top = [m for _, m in scored_moves if any(v in opp_set for v in nbrs[m])][:8]
    for om in opp_top:
        test_opp = opp_set | {om}
        opp_threat_count = 0
        for m2 in empty_cells:
            if m2 != om and check_win(test_opp, m2, corners, edges_dict, nbrs, board_set, boundary_set):
                opp_threat_count += 1
                if opp_threat_count >= 2:
                    return om

    return scored_moves[0][1]
