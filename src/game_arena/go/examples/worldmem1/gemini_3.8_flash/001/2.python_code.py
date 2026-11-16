
import random

# Precompute board geometry
SIZE = 19
BOARD_RANGE = range(1, SIZE + 1)
ALL_POINTS = [(r, c) for r in BOARD_RANGE for c in BOARD_RANGE]

NEIGHBORS = {}
DIAGONALS = {}
for r in BOARD_RANGE:
    for c in BOARD_RANGE:
        NEIGHBORS[(r, c)] = [
            (nr, nc)
            for nr, nc in [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
            if 1 <= nr <= SIZE and 1 <= nc <= SIZE
        ]
        DIAGONALS[(r, c)] = [
            (nr, nc)
            for nr, nc in [(r - 1, c - 1), (r - 1, c + 1), (r + 1, c - 1), (r + 1, c + 1)]
            if 1 <= nr <= SIZE and 1 <= nc <= SIZE
        ]

STAR_POINTS = [
    (4, 4), (4, 16), (16, 4), (16, 16),
    (4, 10), (10, 4), (10, 16), (16, 10),
    (10, 10),
    (3, 4), (4, 3), (3, 16), (16, 3), (4, 17), (17, 4), (16, 17), (17, 16),
    (3, 10), (10, 3), (10, 17), (17, 10)
]

def get_groups(stones_set, board_occupied):
    """Find connected chains of stones and their liberties."""
    visited = set()
    groups = []
    for stone in stones_set:
        if stone in visited:
            continue
        chain = []
        liberties = set()
        queue = [stone]
        visited.add(stone)
        while queue:
            curr = queue.pop()
            chain.append(curr)
            for n in NEIGHBORS[curr]:
                if n in stones_set and n not in visited:
                    visited.add(n)
                    queue.append(n)
                elif n not in board_occupied:
                    liberties.add(n)
        groups.append({'stones': chain, 'liberties': liberties})
    return groups

def simulate_move(move, me_set, opp_set, opp_groups):
    """
    Simulates playing 'move' for 'me'.
    Returns (is_legal, captured_stones, new_my_liberties_count).
    """
    if move in me_set or move in opp_set:
        return False, set(), 0

    captured = set()
    for g in opp_groups:
        if g['liberties'] == {move}:
            captured.update(g['stones'])

    # Determine liberties for the newly played stone's group
    opp_after = opp_set - captured
    me_after = me_set | {move}
    occupied_after = me_after | opp_after

    # Compute liberties for the new group containing 'move'
    visited = {move}
    chain = [move]
    liberties = set()
    queue = [move]
    while queue:
        curr = queue.pop()
        for n in NEIGHBORS[curr]:
            if n in me_after and n not in visited:
                visited.add(n)
                queue.append(n)
            elif n not in occupied_after:
                liberties.add(n)

    if not liberties:
        # Suicide move is illegal
        return False, set(), 0

    return True, captured, len(liberties)

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    me_set = set(me)
    opp_set = set(opponent)
    occupied = me_set | opp_set

    # Track Ko history
    ko_states = memory.get('ko_states', set())

    # Find groups and their liberties
    my_groups = get_groups(me_set, occupied)
    opp_groups = get_groups(opp_set, occupied)

    # Detect opponent's last move
    prev_opp = set(memory.get('last_opp', []))
    last_opp_move = list(opp_set - prev_opp)
    last_move_target = last_opp_move[0] if last_opp_move else None

    # Identify tactical points
    my_in_atari = [g for g in my_groups if len(g['liberties']) == 1]
    opp_in_atari = [g for g in opp_groups if len(g['liberties']) == 1]
    opp_two_lib = [g for g in opp_groups if len(g['liberties']) == 2]

    # Quick candidate collection
    candidates = {}

    def add_candidate(pt, score):
        if 1 <= pt[0] <= SIZE and 1 <= pt[1] <= SIZE and pt not in occupied:
            candidates[pt] = candidates.get(pt, 0) + score

    # 1. Opening moves
    total_stones = len(occupied)
    if total_stones < 20:
        for idx, sp in enumerate(STAR_POINTS):
            if sp not in occupied:
                add_candidate(sp, 100 - idx * 2)

    # 2. Urgent captures: opponent groups in atari
    for g in opp_in_atari:
        lib = next(iter(g['liberties']))
        add_candidate(lib, 2000 + len(g['stones']) * 100)

    # 3. Urgent defense: save our groups in atari
    for g in my_in_atari:
        lib = next(iter(g['liberties']))
        # Escaping
        add_candidate(lib, 1800 + len(g['stones']) * 80)
        # Counter-attack: find adjacent opponent groups in atari to save ourselves
        for s in g['stones']:
            for n in NEIGHBORS[s]:
                if n in opp_set:
                    for og in opp_in_atari:
                        if n in og['stones']:
                            add_candidate(next(iter(og['liberties'])), 2200 + len(og['stones']) * 100)

    # 4. Attack 2-liberty opponent groups
    for g in opp_two_lib:
        for lib in g['liberties']:
            add_candidate(lib, 250 + len(g['stones']) * 20)

    # 5. Local fight / Shape heuristics around active stones
    active_sources = []
    if last_move_target:
        active_sources.append((last_move_target, 40))
    for g in my_in_atari + opp_in_atari:
        for s in g['stones']:
            active_sources.append((s, 20))

    for source, weight in active_sources:
        for n in NEIGHBORS[source]:
            add_candidate(n, weight)
        for d in DIAGONALS[source]:
            add_candidate(d, weight // 2)

    # 6. Global shape and expansion moves (eye making, connectivity, line 3/4 balance)
    for s in me_set:
        for n in NEIGHBORS[s]:
            if n not in occupied:
                add_candidate(n, 15)
        for d in DIAGONALS[s]:
            if d not in occupied:
                add_candidate(d, 10)

    # Add general empty points if candidates are sparse
    if len(candidates) < 15:
        for pt in ALL_POINTS:
            if pt not in occupied:
                r, c = pt
                dist_edge = min(r - 1, SIZE - r, c - 1, SIZE - c)
                if dist_edge in (2, 3):  # Lines 3 and 4
                    add_candidate(pt, 5)

    # Evaluate candidate legality and tactical safety
    scored_moves = []
    for move, heuristic_score in candidates.items():
        legal, captured, new_libs = simulate_move(move, me_set, opp_set, opp_groups)
        if not legal:
            continue

        # Check Simple Ko
        new_opp = tuple(sorted(opp_set - captured))
        new_me = tuple(sorted(me_set | {move}))
        board_hash = hash((new_me, new_opp))
        if board_hash in ko_states:
            continue

        final_score = heuristic_score

        # Self-atari penalty: if move has 1 liberty and doesn't capture, heavily penalize
        if new_libs <= 1 and not captured:
            final_score -= 1500
        elif new_libs == 2 and not captured:
            final_score -= 100
        else:
            final_score += new_libs * 15

        # Territorial value based on line (3rd and 4th lines are ideal)
        r, c = move
        dist_edge = min(r - 1, SIZE - r, c - 1, SIZE - c)
        if dist_edge in (2, 3):
            final_score += 25
        elif dist_edge == 0:  # 1st line penalty unless capturing/connecting
            if not captured:
                final_score -= 60

        # Capture reward
        if captured:
            final_score += len(captured) * 200

        scored_moves.append((final_score, move, board_hash))

    # Sort descending by score
    scored_moves.sort(key=lambda x: x[0], reverse=True)

    if scored_moves and scored_moves[0][0] > -500:
        best_score, best_move, next_hash = scored_moves[0]
        # Keep Ko states set compact (last 6 states)
        updated_ko = set(list(ko_states)[-6:])
        updated_ko.add(hash((tuple(sorted(me_set)), tuple(sorted(opp_set)))))
        
        new_memory = {
            'last_opp': opponent,
            'ko_states': updated_ko
        }
        return best_move, new_memory

    # If no positive move found, pass
    return (0, 0), {'last_opp': opponent, 'ko_states': ko_states}
