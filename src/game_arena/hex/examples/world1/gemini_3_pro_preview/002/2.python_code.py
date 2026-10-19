
import numpy as np
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """
    Hex policy based on electric circuit resistance analysis (Flow Centrality).
    Maximizes the total current flow through a node for both players to find
    critical moves for attacking and defending.
    """
    SIZE = 11
    
    # Convert lists to sets for O(1) lookups
    me_set = set(me)
    opp_set = set(opp)
    
    # Identify legal moves
    valid_moves = []
    for r in range(SIZE):
        for c in range(SIZE):
            if (r, c) not in me_set and (r, c) not in opp_set:
                valid_moves.append((r, c))
    
    # Safety check (should not be reached in normal play)
    if not valid_moves:
        return (0, 0)
        
    # Optimization: On an empty board, play the center
    if len(valid_moves) == SIZE * SIZE:
        return (SIZE // 2, SIZE // 2)

    # -----------------------------------------------------------
    # Helper: Get valid hexagonal neighbors
    # -----------------------------------------------------------
    def get_neighbors(r, c):
        # Touching logic: 6 neighbors
        # Direct Offsets: Left, Right, TopLeft, TopRight, BotLeft, BotRight
        offsets = [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, -1), (1, 0)]
        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                yield nr, nc

    # -----------------------------------------------------------
    # Solver: Calculate Voltages (Potentials) for a player configuration
    # -----------------------------------------------------------
    def get_potentials(my_stones, their_stones, is_vertical):
        N = SIZE * SIZE
        
        # Resistance parameters
        # We work with Conductance G = 1/R
        G_WIRE = 1000.0  # High conductance for own stones
        G_AIR = 1.0      # Standard conductance for empty cells
        
        # System: Mat_A * V = Vec_b
        mat_A = np.zeros((N, N), dtype=float)
        vec_b = np.zeros(N, dtype=float)
        
        node_map = lambda r, c: r * SIZE + c
        
        for r in range(SIZE):
            for c in range(SIZE):
                u = node_map(r, c)
                
                # If cell is blocked by opponent, it's an insulator (removed node).
                # We set a dummy equation V_u = 0 to keep matrix non-singular.
                if (r, c) in their_stones:
                    mat_A[u, u] = 1.0
                    vec_b[u] = 0.0
                    continue
                
                u_is_me = (r, c) in my_stones
                
                total_conductance = 0.0
                
                # Internal neighbors
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in their_stones:
                        continue # No connection to insulator
                    
                    v = node_map(nr, nc)
                    v_is_me = (nr, nc) in my_stones
                    
                    # Edge conductance: Wire if both nodes are 'me', else Air
                    g = G_WIRE if (u_is_me and v_is_me) else G_AIR
                    
                    mat_A[u, v] -= g
                    total_conductance += g
                
                # Virtual connections to Source (1V) and Sink (0V) rails
                g_source = 0.0
                g_sink = 0.0
                
                if is_vertical: # Black: Top to Bottom
                    if r == 0:
                        g_source = G_WIRE if u_is_me else G_AIR
                    if r == SIZE - 1:
                        g_sink = G_WIRE if u_is_me else G_AIR
                else: # White: Left to Right
                    if c == 0:
                        g_source = G_WIRE if u_is_me else G_AIR
                    if c == SIZE - 1:
                        g_sink = G_WIRE if u_is_me else G_AIR
                
                total_conductance += g_source + g_sink
                mat_A[u, u] = total_conductance
                
                # b[u] accumulates known voltages (Source=1.0, Sink=0.0)
                vec_b[u] = g_source * 1.0 
                
        # Solve the linear system
        try:
            return np.linalg.solve(mat_A, vec_b)
        except np.linalg.LinAlgError:
            # Fallback if matrix is singular (disconnected graph)
            return np.zeros(N)

    # -----------------------------------------------------------
    # Main Logic
    # -----------------------------------------------------------
    
    # 1. Solve potentials for Me
    am_i_vertical = (color == 'b')
    pot_me = get_potentials(me_set, opp_set, am_i_vertical)
    
    # 2. Solve potentials for Opponent (Targeting their edges)
    opp_vertical = not am_i_vertical
    pot_opp = get_potentials(opp_set, me_set, opp_vertical)
    
    best_score = -1.0
    best_cell = valid_moves[0]
    
    # Shuffle moves to break ties randomly
    random.shuffle(valid_moves)
    
    node_map = lambda r, c: r * SIZE + c
    
    # 3. Evaluate each empty cell
    for r, c in valid_moves:
        u = node_map(r, c)
        
        # --- Calculate Flow for Me ---
        # Flow ~ Sum of |dV| to all connected nodes
        flow_me = 0.0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) not in opp_set:
                v = node_map(nr, nc)
                flow_me += abs(pot_me[u] - pot_me[v])
        
        # Add flow from virtual source/sink edges
        if am_i_vertical:
            if r == 0: flow_me += abs(pot_me[u] - 1.0)
            if r == SIZE - 1: flow_me += abs(pot_me[u] - 0.0)
        else:
            if c == 0: flow_me += abs(pot_me[u] - 1.0)
            if c == SIZE - 1: flow_me += abs(pot_me[u] - 0.0)
            
        # --- Calculate Flow for Opponent ---
        flow_opp = 0.0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) not in me_set:
                v = node_map(nr, nc)
                flow_opp += abs(pot_opp[u] - pot_opp[v])
                
        if opp_vertical:
            if r == 0: flow_opp += abs(pot_opp[u] - 1.0)
            if r == SIZE - 1: flow_opp += abs(pot_opp[u] - 0.0)
        else:
            if c == 0: flow_opp += abs(pot_opp[u] - 1.0)
            if c == SIZE - 1: flow_opp += abs(pot_opp[u] - 0.0)
            
        # Combined score: Aid my connection + Block their connection
        score = flow_me + flow_opp
        
        if score > best_score:
            best_score = score
            best_cell = (r, c)
            
    return best_cell
