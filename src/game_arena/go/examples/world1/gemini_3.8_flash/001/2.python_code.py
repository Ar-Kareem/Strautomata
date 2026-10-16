
import random

BOARD_SIZE = 19

def get_neighbors(r: int, c: int):
    nbrs = []
    if r > 1: nbrs.append((r - 1, c))
    if r < BOARD_SIZE: nbrs.append((r + 1, c))
    if c > 1: nbrs.append((r, c - 1))
    if c < BOARD_SIZE: nbrs.append((r, c + 1))
    return nbrs

def get_group_and_liberties(r: int, c: int, board: dict):
    color = board.get((r, c))
    if color is None:
        return set(), set()
    
    group = set()
    liberties = set()
    queue = [(r, c)]
    group.add((r, c))
    
    while queue:
        curr = queue.pop()
        for nr, nc in get_neighbors(curr[0], curr[1]):
            nbr_color = board.get((nr, nc))
            if nbr_color is None:
                liberties.add((nr, nc))
            elif nbr_color == color and (nr, nc) not in group:
                group.add((nr, nc))
                queue.append((nr, nc))
                
    return group, liberties

def simulate_move(r: int, c: int, color: int, board: dict):
    if (r, c) in board:
        return False, 0, board
    
    opp_color = 2 if color == 1 else 1
    new_board = dict(board)
    new_board[(r, c)] = color
    
    captured_stones = 0
    # Check adjacent opponent groups for captures
    for nr, nc in get_neighbors(r, c):
        if new_board.get((nr, nc)) == opp_color:
            opp_group, opp_libs = get_group_and_liberties(nr, nc, new_board)
            if len(opp_libs) == 0:
                for gr, gc in opp_group:
                    if (gr, gc) in new_board:
                        del new_board[(gr, gc)]
                        captured_stones += 1
                        
    # Check suicide for our own group
    _, my_libs = get_group_and_liberties(r, c, new_board)
    if len(my_libs) == 0:
        return False, 0, board
        
    return True, captured_stones, new_board

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board = {}
    for r, c in me:
        board[(r, c)] = 1
    for r, c in opponent:
        board[(r, c)] = 2

    occupied = set(me) | set(opponent)
    total_stones = len(occupied)

    # 1. Opening Book for empty / sparsely populated board
    if total_stones < 12:
        openings = [
            # 4-4 Star points
            (4, 4), (4, 16), (16, 4), (16, 16),
            # 3-4 points and symmetrical counterparts
            (3, 4), (4, 3), (3, 16), (4, 17),
            (16, 3), (17, 4), (17, 16), (16, 17),
            (4, 10), (16, 10), (10, 4), (10, 16), (10, 10)
        ]
        for r, c in openings:
            if (r, c) not in occupied:
                legal, _, _ = simulate_move(r, c, 1, board)
                if legal:
                    return (r, c)

    # 2. Tactical Analysis: Find all groups and their liberties
    visited_me = set()
    my_groups = []
    for pt in me:
        if pt not in visited_me:
            grp, libs = get_group_and_liberties(pt[0], pt[1], board)
            visited_me.update(grp)
            my_groups.append((grp, libs))

    visited_opp = set()
    opp_groups = []
    for pt in opponent:
        if pt not in visited_opp:
            grp, libs = get_group_and_liberties(pt[0], pt[1], board)
            visited_opp.update(grp)
            opp_groups.append((grp, libs))

    # Priority A: Capture opponent group in Atari (1 liberty)
    capture_moves = []
    for grp, libs in opp_groups:
        if len(libs) == 1:
            lib = next(iter(libs))
            legal, caps, _ = simulate_move(lib[0], lib[1], 1, board)
            if legal:
                capture_moves.append((len(grp), lib))
    if capture_moves:
        capture_moves.sort(key=lambda x: x[0], reverse=True)
        return capture_moves[0][1]

    # Priority B: Save our group in Atari (1 liberty)
    save_moves = []
    for grp, libs in my_groups:
        if len(libs) == 1:
            lib = next(iter(libs))
            legal, caps, nb = simulate_move(lib[0], lib[1], 1, board)
            if legal:
                # Check if moving to this liberty actually saves the group
                _, post_libs = get_group_and_liberties(lib[0], lib[1], nb)
                if len(post_libs) >= 2 or caps > 0:
                    save_moves.append((len(grp), lib))
    if save_moves:
        save_moves.sort(key=lambda x: x[0], reverse=True)
        return save_moves[0][1]

    # 3. Candidate move generation: prioritize points near existing stones
    candidate_set = set()
    if not occupied:
        return (4, 4)
        
    for r, c in occupied:
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) not in occupied:
                candidate_set.add((nr, nc))
        # Add diagonal neighbors for good shape and cuts
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= BOARD_SIZE and 1 <= nc <= BOARD_SIZE:
                if (nr, nc) not in occupied:
                    candidate_set.add((nr, nc))

    if not candidate_set:
        # Pass if board is completely filled
        return (0, 0)

    # 4. Score candidate moves based on shape, liberties, and position
    best_move = None
    best_score = -float('inf')

    for r, c in candidate_set:
        legal, caps, nb = simulate_move(r, c, 1, board)
        if not legal:
            continue
            
        grp, libs = get_group_and_liberties(r, c, nb)
        my_lib_count = len(libs)
        
        # Penalize self-atari (suicidal shapes) unless capturing stones
        if my_lib_count <= 1 and caps == 0:
            continue

        score = 0.0

        # Captures reward
        score += caps * 35.0

        # Liberty count reward
        score += min(my_lib_count, 6) * 5.0

        # Distance from edge heuristics (favor 3rd and 4th lines)
        dist_row = min(r, BOARD_SIZE - r + 1)
        dist_col = min(c, BOARD_SIZE - c + 1)
        min_dist = min(dist_row, dist_col)

        if min_dist == 3 or min_dist == 4:
            score += 8.0
        elif min_dist == 2:
            score += 2.0
        elif min_dist == 1:
            score -= 6.0  # Avoid first line in normal play

        # Neighbor influence
        for nr, nc in get_neighbors(r, c):
            val = board.get((nr, nc))
            if val == 2:
                # Attack enemy stone: reducing opponent liberties
                opp_grp, opp_l = get_group_and_liberties(nr, nc, board)
                if len(opp_l) == 2:
                    score += 15.0  # Put opponent into Atari
                elif len(opp_l) == 3:
                    score += 7.0
            elif val == 1:
                # Connection to friendly stones
                score += 4.0

        # Minor noise to break ties cleanly
        score += random.uniform(0.0, 0.5)

        if score > best_score:
            best_score = score
            best_move = (r, c)

    if best_move is not None:
        return best_move

    # 5. Fallback: pick any legal move, or pass if none exist
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if (r, c) not in occupied:
                legal, _, _ = simulate_move(r, c, 1, board)
                if legal:
                    return (r, c)

    return (0, 0)
