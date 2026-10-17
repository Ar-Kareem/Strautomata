
import random

BOARD_SIZE = 19
PASS_MOVE = (0, 0)

# Star points and high-value opening points on 19x19
OPENING_POINTS = [
    (4, 4), (16, 4), (4, 16), (16, 16),
    (4, 10), (16, 10), (10, 4), (10, 16), (10, 10),
    (3, 4), (4, 3), (3, 16), (4, 17),
    (16, 3), (17, 4), (16, 17), (17, 16),
    (3, 10), (17, 10), (10, 3), (10, 17)
]

def in_bounds(r: int, c: int) -> bool:
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE

def get_neighbors(r: int, c: int) -> list[tuple[int, int]]:
    res = []
    if r > 1: res.append((r - 1, c))
    if r < BOARD_SIZE: res.append((r + 1, c))
    if c > 1: res.append((r, c - 1))
    if c < BOARD_SIZE: res.append((r, c + 1))
    return res

def get_diagonals(r: int, c: int) -> list[tuple[int, int]]:
    res = []
    for dr in (-1, 1):
        for dc in (-1, 1):
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc):
                res.append((nr, nc))
    return res

def build_chains(stones: set[tuple[int, int]], all_occupied: set[tuple[int, int]]):
    visited = set()
    chains = []
    stone_to_chain = {}

    for stone in stones:
        if stone in visited:
            continue
        chain_stones = set()
        queue = [stone]
        visited.add(stone)
        liberties = set()

        while queue:
            curr = queue.pop()
            chain_stones.add(curr)
            for nbr in get_neighbors(curr[0], curr[1]):
                if nbr in stones:
                    if nbr not in visited:
                        visited.add(nbr)
                        queue.append(nbr)
                elif nbr not in all_occupied:
                    liberties.add(nbr)

        chain_info = {
            'stones': chain_stones,
            'liberties': liberties
        }
        chains.append(chain_info)
        for s in chain_stones:
            stone_to_chain[s] = chain_info

    return chains, stone_to_chain

def simulate_move(r: int, c: int, me_set: set[tuple[int, int]], opp_set: set[tuple[int, int]], 
                  opp_chains_by_stone: dict, my_chains_by_stone: dict, ko_point: tuple[int, int] | None):
    """
    Simulates placing a stone at (r, c) for ME.
    Returns (is_legal, captured_stones_count, new_chain_liberties, is_ko_move, next_ko)
    """
    if (r, c) == ko_point:
        return False, 0, 0, False, None

    neighbors = get_neighbors(r, c)
    captured = set()
    adjacent_opp_chains = set()

    for nbr in neighbors:
        if nbr in opp_set:
            chain = opp_chains_by_stone[nbr]
            chain_id = id(chain)
            if chain_id not in adjacent_opp_chains:
                adjacent_opp_chains.add(chain_id)
                # If this chain's only liberty is (r, c), it will be captured
                if chain['liberties'] == {(r, c)}:
                    captured.update(chain['stones'])

    # Determine liberties for the new friendly chain
    new_liberties = set()
    friendly_chain_stones = {(r, c)}

    for nbr in neighbors:
        if nbr in captured:
            new_liberties.add(nbr)
        elif nbr not in me_set and nbr not in opp_set:
            new_liberties.add(nbr)
        elif nbr in me_set:
            f_chain = my_chains_by_stone[nbr]
            friendly_chain_stones.update(f_chain['stones'])
            for lib in f_chain['liberties']:
                if lib != (r, c):
                    new_liberties.add(lib)

    # Suicide check
    if len(new_liberties) == 0 and len(captured) == 0:
        return False, 0, 0, False, None

    # Check for ko creation: 1 stone played, captured exactly 1 stone, resulting chain has 1 stone and 1 liberty
    next_ko = None
    if len(captured) == 1 and len(friendly_chain_stones) == 1 and len(new_liberties) == 1:
        next_ko = list(captured)[0]

    return True, len(captured), len(new_liberties), False, next_ko

def is_true_eye(r: int, c: int, me_set: set[tuple[int, int]]) -> bool:
    """Checks if (r, c) is an eye for player ME, to avoid filling own territory."""
    neighbors = get_neighbors(r, c)
    if not all(nbr in me_set for nbr in neighbors):
        return False
    diags = get_diagonals(r, c)
    opp_diag_count = sum(1 for d in diags if d not in me_set)
    max_opp = 1 if len(neighbors) == 4 else 0
    return opp_diag_count <= max_opp

def score_move(r: int, c: int, me_set: set[tuple[int, int]], opp_set: set[tuple[int, int]],
               my_chains_by_stone: dict, opp_chains_by_stone: dict,
               captures: int, new_liberties: int, move_number: int) -> float:
    score = 0.0

    # 1. Massive reward for capturing opponent stones
    if captures > 0:
        score += 300.0 * captures

    # 2. Severe penalty for self-atari
    if new_liberties == 1 and captures == 0:
        score -= 600.0
    elif new_liberties == 2:
        score += 15.0
    elif new_liberties >= 3:
        score += 35.0

    neighbors = get_neighbors(r, c)
    diagonals = get_diagonals(r, c)

    # 3. Saving own stones in atari
    for nbr in neighbors:
        if nbr in me_set:
            my_chain = my_chains_by_stone[nbr]
            if len(my_chain['liberties']) == 1:
                if new_liberties >= 2 or captures > 0:
                    score += 250.0 + len(my_chain['stones']) * 40.0

    # 4. Attacking opponent stones (putting into atari or reducing liberties)
    for nbr in neighbors:
        if nbr in opp_set:
            opp_chain = opp_chains_by_stone[nbr]
            rem_lib = len(opp_chain['liberties'])
            if rem_lib == 2 and (r, c) in opp_chain['liberties']:
                # Puts opponent into atari!
                score += 80.0 + len(opp_chain['stones']) * 20.0
            elif rem_lib == 3 and (r, c) in opp_chain['liberties']:
                score += 30.0

    # 5. Position on board: lines 3 and 4 are ideal for territory/influence
    line_dist = min(r, 20 - r, c, 20 - c)
    if line_dist == 3:
        score += 35.0 if move_number < 40 else 15.0
    elif line_dist == 4:
        score += 40.0 if move_number < 40 else 20.0
    elif line_dist == 2:
        score += -10.0 if move_number < 30 else 5.0
    elif line_dist == 1:
        if captures == 0:
            score -= 80.0 if move_number < 50 else 10.0

    # 6. Shape & Connectivity
    friendly_adj = sum(1 for n in neighbors if n in me_set)
    opp_adj = sum(1 for n in neighbors if n in opp_set)

    # Extending or making contact
    if friendly_adj >= 1:
        score += 20.0 * friendly_adj
    if opp_adj >= 1:
        score += 10.0 * opp_adj

    # Hane / cutting opportunity
    for d in diagonals:
        if d in opp_set and friendly_adj >= 1:
            score += 25.0
        elif d in me_set and opp_adj >= 1:
            score += 20.0

    # Avoid filling own eye
    if is_true_eye(r, c, me_set):
        score -= 1000.0

    return score

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    me_set = set(me)
    opp_set = set(opponent)
    all_occupied = me_set | opp_set

    move_count = len(me) + len(opponent)
    ko_point = memory.get('ko')

    # If the board is completely empty, grab a star point
    if not all_occupied:
        return (4, 4), {'ko': None}

    # Opening phase: pick prime star points if available
    if move_count < 12:
        available_opening = [p for p in OPENING_POINTS if p not in all_occupied]
        if available_opening:
            # Prefer 4-4 corners
            corners = [(4, 4), (16, 4), (4, 16), (16, 16)]
            for c in corners:
                if c not in all_occupied:
                    return c, {'ko': None}
            return available_opening[0], {'ko': None}

    _, opp_chains_by_stone = build_chains(opp_set, all_occupied)
    _, my_chains_by_stone = build_chains(me_set, all_occupied)

    # Gather candidate moves: empty cells adjacent to existing stones or key opening points
    candidates = set()
    for stone in all_occupied:
        for nbr in get_neighbors(stone[0], stone[1]):
            if nbr not in all_occupied:
                candidates.add(nbr)
        for diag in get_diagonals(stone[0], stone[1]):
            if diag not in all_occupied:
                candidates.add(diag)

    if move_count < 40:
        for p in OPENING_POINTS:
            if p not in all_occupied:
                candidates.add(p)

    best_move = PASS_MOVE
    best_score = -float('inf')
    next_ko = None

    for r, c in candidates:
        legal, captures, new_libs, _, candidate_ko = simulate_move(
            r, c, me_set, opp_set, opp_chains_by_stone, my_chains_by_stone, ko_point
        )
        if not legal:
            continue

        score = score_move(r, c, me_set, opp_set, my_chains_by_stone, opp_chains_by_stone, 
                           captures, new_libs, move_count)

        # Small tie-breaking noise
        score += random.uniform(0.0, 0.5)

        if score > best_score:
            best_score = score
            best_move = (r, c)
            next_ko = candidate_ko

    # Fallback: if best score is extremely low or no candidate found, search any legal move
    if best_move == PASS_MOVE or best_score < -400.0:
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                if (r, c) not in all_occupied:
                    legal, captures, new_libs, _, candidate_ko = simulate_move(
                        r, c, me_set, opp_set, opp_chains_by_stone, my_chains_by_stone, ko_point
                    )
                    if legal and new_libs > 1 and not is_true_eye(r, c, me_set):
                        best_move = (r, c)
                        next_ko = candidate_ko
                        break
            if best_move != PASS_MOVE:
                break

    memory['ko'] = next_ko
    return best_move, memory
