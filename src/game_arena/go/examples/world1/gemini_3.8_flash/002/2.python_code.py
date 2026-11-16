
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    Computes the next move for a 19x19 Go board.
    me: list of (row, col) tuples (1-indexed: 1..19)
    opponent: list of (row, col) tuples (1-indexed: 1..19)
    Returns: (row, col) tuple, or (0, 0) to pass.
    """
    BOARD_SIZE = 19
    me_set = set(me)
    opp_set = set(opponent)
    
    # 0 = empty, 1 = me, 2 = opponent
    grid = [[0] * (BOARD_SIZE + 1) for _ in range(BOARD_SIZE + 1)]
    for r, c in me_set:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            grid[r][c] = 1
    for r, c in opp_set:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            grid[r][c] = 2

    def neighbors(r: int, c: int):
        if r > 1: yield (r - 1, c)
        if r < BOARD_SIZE: yield (r + 1, c)
        if c > 1: yield (r, c - 1)
        if c < BOARD_SIZE: yield (r, c + 1)

    def get_chains(color: int):
        """Returns list of (chain_stones_set, liberties_set)."""
        visited = set()
        chains = []
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                if grid[r][c] == color and (r, c) not in visited:
                    chain = set()
                    liberties = set()
                    queue = [(r, c)]
                    visited.add((r, c))
                    while queue:
                        curr_r, curr_c = queue.pop()
                        chain.add((curr_r, curr_c))
                        for nr, nc in neighbors(curr_r, curr_c):
                            if grid[nr][nc] == 0:
                                liberties.add((nr, nc))
                            elif grid[nr][nc] == color and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                queue.append((nr, nc))
                    chains.append((chain, liberties))
        return chains

    my_chains = get_chains(1)
    opp_chains = get_chains(2)

    def is_legal(r: int, c: int, color: int = 1) -> bool:
        """Check if playing (r, c) by 'color' is legal (not occupied, not suicide)."""
        if grid[r][c] != 0:
            return False
        opp_color = 2 if color == 1 else 1

        # Direct empty neighbors give immediate liberty
        has_direct_liberty = False
        for nr, nc in neighbors(r, c):
            if grid[nr][nc] == 0:
                has_direct_liberty = True
                break

        # Check if this move captures any opponent chain
        for ch, libs in (opp_chains if color == 1 else my_chains):
            if libs == {(r, c)}:
                # This move captures the opponent group, hence legal
                return True

        if has_direct_liberty:
            return True

        # If no direct liberty, check if connected to a friendly chain with > 1 liberties
        for ch, libs in (my_chains if color == 1 else opp_chains):
            if (r, c) in libs and len(libs) > 1:
                return True

        return False

    # 1. Capture Opponent Stones in Atari (liberties == 1)
    capture_candidates = []
    for ch, libs in opp_chains:
        if len(libs) == 1:
            lib = next(iter(libs))
            if is_legal(lib[0], lib[1], 1):
                capture_candidates.append((len(ch), lib))
    if capture_candidates:
        capture_candidates.sort(key=lambda x: x[0], reverse=True)
        return capture_candidates[0][1]

    # 2. Defend Friendly Stones in Atari (liberties == 1)
    defend_candidates = []
    for ch, libs in my_chains:
        if len(libs) == 1:
            lib = next(iter(libs))
            lr, lc = lib
            # Check if playing on this liberty escapes atari (gives >= 2 liberties)
            # or captures adjacent opponent
            if is_legal(lr, lc, 1):
                # Count immediate free spaces or captured chains
                lib_gain = sum(1 for nr, nc in neighbors(lr, lc) if grid[nr][nc] == 0)
                captures = sum(len(och) for och, olibs in opp_chains if olibs == {(lr, lc)})
                if lib_gain >= 2 or captures > 0:
                    defend_candidates.append((len(ch) + captures, lib))
    if defend_candidates:
        defend_candidates.sort(key=lambda x: x[0], reverse=True)
        return defend_candidates[0][1]

    # 3. Opening Moves (if early in game)
    total_stones = len(me) + len(opponent)
    if total_stones < 20:
        corners = [
            (4, 4), (16, 4), (4, 16), (16, 16),
            (3, 4), (4, 3), (17, 4), (16, 3),
            (3, 16), (4, 17), (17, 16), (16, 17),
            (3, 3), (17, 3), (3, 17), (17, 17),
            (4, 10), (10, 4), (10, 16), (16, 10),
            (10, 10)
        ]
        for r, c in corners:
            if grid[r][c] == 0:
                # Ensure no stone is immediately adjacent to keep opening clean
                adj_occupied = any(grid[nr][nc] != 0 for nr, nc in neighbors(r, c))
                if not adj_occupied and is_legal(r, c, 1):
                    return (r, c)

    # 4. Heuristic Evaluation for Mid-Game / General Play
    best_score = -1e9
    best_move = None

    # Collect active candidate points (within distance 2 of any existing stone, plus corners)
    candidate_points = set()
    all_stones = list(me_set) + list(opp_set)
    if not all_stones:
        return (4, 4)

    for r, c in all_stones:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE and grid[nr][nc] == 0:
                    candidate_points.add((nr, nc))

    # Evaluate candidates
    for r, c in candidate_points:
        if not is_legal(r, c, 1):
            continue

        score = 0.0

        # Distance from edge heuristics (favor 3rd and 4th lines, heavily penalize 1st line)
        dist_edge = min(r, 20 - r, c, 20 - c)
        if dist_edge == 1:
            score -= 40.0
        elif dist_edge == 2:
            score -= 10.0
        elif dist_edge in (3, 4):
            score += 15.0

        # Check adjacent contacts
        for nr, nc in neighbors(r, c):
            val = grid[nr][nc]
            if val == 0:
                score += 4.0  # Open liberty
            elif val == 1:
                score += 5.0  # Friendly connection
            elif val == 2:
                score += 3.0  # Contact play

        # Check diagonal neighbors (shape potential)
        diag_offsets = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in diag_offsets:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                if grid[nr][nc] == 1:
                    score += 6.0  # Good shape (e.g. keima or kosumi)
                elif grid[nr][nc] == 2:
                    score += 2.0

        # Putting opponent chain with 2 liberties into atari
        for och, olibs in opp_chains:
            if len(olibs) == 2 and (r, c) in olibs:
                score += 25.0 + len(och) * 3.0

        # Extending friendly chain with 2 liberties
        for mch, mlibs in my_chains:
            if len(mlibs) == 2 and (r, c) in mlibs:
                score += 20.0 + len(mch) * 2.0

        # Small tie-breaking noise
        score += random.uniform(0.0, 1.0)

        if score > best_score:
            best_score = score
            best_move = (r, c)

    if best_move and is_legal(best_move[0], best_move[1], 1):
        return best_move

    # 5. Fallback: Find ANY legal move with highest liberties
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if is_legal(r, c, 1):
                return (r, c)

    # 6. Pass if no legal moves exist
    return (0, 0)
