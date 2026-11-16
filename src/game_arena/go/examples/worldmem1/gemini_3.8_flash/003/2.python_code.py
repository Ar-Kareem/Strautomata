
import random
import time

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    start_time = time.time()
    
    # 1. Coordinate / Board Setup
    BOARD_SIZE = 19
    me_set = set(me)
    opp_set = set(opponent)
    all_occupied = me_set | opp_set

    # Retrieve memory history for Ko handling
    ko_point = memory.get("ko_point", None)
    
    # Neighbors helper
    def get_adj(r, c):
        res = []
        if r > 1: res.append((r - 1, c))
        if r < BOARD_SIZE: res.append((r + 1, c))
        if c > 1: res.append((r, c - 1))
        if c < BOARD_SIZE: res.append((r, c + 1))
        return res

    # Group and Liberty Analysis
    def get_chains(stones, enemies):
        visited = set()
        chains = []  # list of (set(stones), set(liberties))
        stone_to_chain = {}
        for s in stones:
            if s in visited:
                continue
            chain = set()
            liberties = set()
            queue = [s]
            visited.add(s)
            while queue:
                curr = queue.pop()
                chain.add(curr)
                for adj in get_adj(curr[0], curr[1]):
                    if adj in stones:
                        if adj not in visited:
                            visited.add(adj)
                            queue.append(adj)
                    elif adj not in enemies:
                        liberties.add(adj)
            idx = len(chains)
            chains.append((chain, liberties))
            for st in chain:
                stone_to_chain[st] = idx
        return chains, stone_to_chain

    my_chains, my_stone_to_chain = get_chains(me_set, opp_set)
    opp_chains, opp_stone_to_chain = get_chains(opp_set, me_set)

    # Legality checker simulating single move
    def check_move_legal(move, player_set, enemy_set, opp_chains_list, opp_map):
        r, c = move
        if move in all_occupied:
            return False, 0, None
        if move == ko_point:
            return False, 0, None

        adj = get_adj(r, c)
        captured_stones = 0
        captured_single_stone = None
        
        # Check if this move captures any enemy chain
        checked_opp_chains = set()
        for a in adj:
            if a in enemy_set:
                c_idx = opp_map[a]
                if c_idx not in checked_opp_chains:
                    checked_opp_chains.add(c_idx)
                    ch_stones, ch_libs = opp_chains_list[c_idx]
                    if len(ch_libs) == 1 and move in ch_libs:
                        captured_stones += len(ch_stones)
                        if len(ch_stones) == 1:
                            captured_single_stone = list(ch_stones)[0]

        if captured_stones > 0:
            # Captures are always legal (unless ko, checked above)
            new_ko = captured_single_stone if captured_stones == 1 else None
            return True, captured_stones, new_ko

        # If no captures, check if move has liberties or connects to a chain with > 1 liberty
        has_direct_liberty = False
        for a in adj:
            if a not in all_occupied:
                has_direct_liberty = True
                break
        if has_direct_liberty:
            return True, 0, None

        # Check friendly chains connected
        for a in adj:
            if a in player_set:
                c_idx = my_stone_to_chain[a]
                _, ch_libs = my_chains[c_idx]
                if len(ch_libs) > 1:
                    return True, 0, None

        # Otherwise suicide
        return False, 0, None

    # Tactical & Strategic Move Generation
    candidate_moves = {}

    def add_candidate(m, score):
        if m in candidate_moves:
            candidate_moves[m] = max(candidate_moves[m], score)
        else:
            candidate_moves[m] = score

    # 1. Urgent: Opponent in atari (capture them)
    for chain, libs in opp_chains:
        if len(libs) == 1:
            lib = list(libs)[0]
            # Big bonus for capturing stones
            add_candidate(lib, 2000.0 + len(chain) * 50.0)

    # 2. Urgent: My chain in atari (save them)
    for chain, libs in my_chains:
        if len(libs) == 1:
            lib = list(libs)[0]
            # Saving move
            add_candidate(lib, 1800.0 + len(chain) * 45.0)

    # 3. Threaten opponent chains with 2 liberties (Atari them)
    for chain, libs in opp_chains:
        if len(libs) == 2:
            for lib in libs:
                add_candidate(lib, 400.0 + len(chain) * 15.0)

    # 4. Opening moves (Star points and 3-4 points)
    opening_points = [
        # 4-4 Star points
        (4, 4), (4, 16), (16, 4), (16, 16), (4, 10), (10, 4), (10, 16), (16, 10), (10, 10),
        # 3-4 points & 4-3 points
        (3, 4), (4, 3), (3, 16), (4, 17), (16, 3), (17, 4), (16, 17), (17, 16),
        # 3-3 points
        (3, 3), (3, 17), (17, 3), (17, 17)
    ]
    if len(all_occupied) < 40:
        for p in opening_points:
            if p not in all_occupied:
                add_candidate(p, 500.0)

    # 5. Local shapes: Around existing stones (hane, extension, connection)
    scanned_points = set()
    for s in me_set | opp_set:
        for adj in get_adj(s[0], s[1]):
            if adj not in all_occupied and adj not in scanned_points:
                scanned_points.add(adj)
                r, c = adj
                # Line distance value (lines 3 and 4 are ideal)
                dist_edge = min(r, BOARD_SIZE + 1 - r, c, BOARD_SIZE + 1 - c)
                line_score = 0.0
                if dist_edge == 3:
                    line_score = 120.0
                elif dist_edge == 4:
                    line_score = 100.0
                elif dist_edge == 2:
                    line_score = 40.0
                elif dist_edge == 5:
                    line_score = 70.0
                elif dist_edge == 1:
                    line_score = -50.0  # Avoid first line early

                # Bonus for adjacent friendly/opponent stones
                adj_friends = sum(1 for a in get_adj(r, c) if a in me_set)
                adj_foes = sum(1 for a in get_adj(r, c) if a in opp_set)
                
                shape_bonus = adj_friends * 35.0 + adj_foes * 30.0
                add_candidate(adj, line_score + shape_bonus + 50.0)

    # Fallback pool: Any empty spot on the board if candidates are few
    if len(candidate_moves) < 20:
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                p = (r, c)
                if p not in all_occupied:
                    dist_edge = min(r, BOARD_SIZE + 1 - r, c, BOARD_SIZE + 1 - c)
                    base = 10.0 if dist_edge in (3, 4) else 1.0
                    add_candidate(p, base)

    # Sort candidates by score descending
    sorted_candidates = sorted(candidate_moves.items(), key=lambda x: x[1], reverse=True)

    chosen_move = (0, 0)
    next_ko = None

    for move, base_score in sorted_candidates:
        if time.time() - start_time > 0.85:
            # Time safety check: pick first legal move
            legal, caps, ko = check_move_legal(move, me_set, opp_set, opp_chains, opp_stone_to_chain)
            if legal:
                chosen_move = move
                next_ko = ko
                break
            continue

        legal, caps, ko = check_move_legal(move, me_set, opp_set, opp_chains, opp_stone_to_chain)
        if not legal:
            continue

        # Check self-atari penalty: does this move result in a group with only 1 liberty?
        # Simulate placing stone:
        r, c = move
        adj = get_adj(r, c)
        empty_adj = [a for a in adj if a not in all_occupied and a != move]
        
        # If no captures and only 0 or 1 immediate empty neighbor, inspect connected friendly chains
        if caps == 0 and len(empty_adj) <= 1:
            total_libs = set(empty_adj)
            for a in adj:
                if a in me_set:
                    c_idx = my_stone_to_chain[a]
                    _, ch_libs = my_chains[c_idx]
                    total_libs |= (ch_libs - {move})
            if len(total_libs) <= 1:
                # Self-atari move: heavily penalize unless desperate
                if base_score < 1500.0:
                    continue

        chosen_move = move
        next_ko = ko
        break

    # If no legal move found, pass
    new_memory = {"ko_point": next_ko}
    return chosen_move, new_memory
