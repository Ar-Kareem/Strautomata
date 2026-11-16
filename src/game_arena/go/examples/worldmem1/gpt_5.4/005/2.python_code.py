
from collections import deque

BOARD_SIZE = 19
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    my_set = set(me)
    opp_set = set(opponent)
    occupied = my_set | opp_set

    def on_board(r, c):
        return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE

    def neighbors(p):
        r, c = p
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if on_board(nr, nc):
                yield (nr, nc)

    def get_group_and_liberties(start, stones):
        group = set()
        liberties = set()
        stack = [start]
        group.add(start)
        while stack:
            p = stack.pop()
            for nb in neighbors(p):
                if nb in stones:
                    if nb not in group:
                        group.add(nb)
                        stack.append(nb)
                elif nb not in occupied_local:
                    liberties.add(nb)
        return group, liberties

    def analyze_group(start, my_stones, opp_stones, color_me=True):
        stones = my_stones if color_me else opp_stones
        occ = my_stones | opp_stones
        group = set()
        liberties = set()
        stack = [start]
        group.add(start)
        while stack:
            p = stack.pop()
            for nb in neighbors(p):
                if nb in stones:
                    if nb not in group:
                        group.add(nb)
                        stack.append(nb)
                elif nb not in occ:
                    liberties.add(nb)
        return group, liberties

    def simulate_move(move, my_stones, opp_stones):
        if move == (0, 0):
            return my_stones, opp_stones, 0, True
        if move in my_stones or move in opp_stones:
            return my_stones, opp_stones, 0, False

        new_my = set(my_stones)
        new_opp = set(opp_stones)
        new_my.add(move)

        captured = 0
        checked = set()
        for nb in neighbors(move):
            if nb in new_opp and nb not in checked:
                grp, libs = analyze_group(nb, new_my, new_opp, color_me=False)
                checked |= grp
                if len(libs) == 0:
                    captured += len(grp)
                    new_opp -= grp

        my_grp, my_libs = analyze_group(move, new_my, new_opp, color_me=True)
        legal = len(my_libs) > 0
        return new_my, new_opp, captured, legal

    def is_legal(move):
        _, _, _, legal = simulate_move(move, my_set, opp_set)
        return legal

    def group_liberties_map(my_stones, opp_stones, color_me=True):
        stones = my_stones if color_me else opp_stones
        seen = set()
        glib = {}
        for s in stones:
            if s not in seen:
                grp, libs = analyze_group(s, my_stones, opp_stones, color_me=color_me)
                llibs = len(libs)
                for x in grp:
                    glib[x] = (grp, llibs, libs)
                seen |= grp
        return glib

    my_info = group_liberties_map(my_set, opp_set, color_me=True)
    opp_info = group_liberties_map(my_set, opp_set, color_me=False)

    empties = [(r, c) for r in range(1, BOARD_SIZE + 1) for c in range(1, BOARD_SIZE + 1) if (r, c) not in occupied]

    if not empties:
        return (0, 0), memory

    # Candidate generation: all liberties near stones + nearby empties; fallback to all empties.
    candidates = set()

    for stone_set in (my_set, opp_set):
        for s in stone_set:
            for nb in neighbors(s):
                if nb not in occupied:
                    candidates.add(nb)
                    for nb2 in neighbors(nb):
                        if nb2 not in occupied:
                            candidates.add(nb2)

    # Add urgent liberties of atari groups
    for info_map in (my_info, opp_info):
        done = set()
        for stone, (grp, llibs, libs) in info_map.items():
            gid = min(grp)
            if gid in done:
                continue
            done.add(gid)
            if llibs <= 2:
                candidates |= libs

    # Opening / sparse-board support
    if len(candidates) < 20:
        opening_points = [
            (4, 4), (4, 16), (16, 4), (16, 16),
            (10, 10), (4, 10), (10, 4), (10, 16), (16, 10),
            (7, 7), (7, 13), (13, 7), (13, 13)
        ]
        for p in opening_points:
            if p not in occupied:
                candidates.add(p)

    if not candidates:
        candidates = set(empties)

    # Helper for eye-like detection
    def eye_like(move, my_stones, opp_stones):
        for nb in neighbors(move):
            if nb in opp_stones:
                return False
        r, c = move
        diag_coords = []
        for dr in (-1, 1):
            for dc in (-1, 1):
                nr, nc = r + dr, c + dc
                if on_board(nr, nc):
                    diag_coords.append((nr, nc))
        bad = 0
        total = 0
        for d in diag_coords:
            total += 1
            if d in opp_stones:
                bad += 1
        # corners/edges tolerate fewer diagonals
        edge_count = (1 if r in (1, BOARD_SIZE) else 0) + (1 if c in (1, BOARD_SIZE) else 0)
        if edge_count == 0:
            return bad <= 1
        else:
            return bad == 0

    def distance_to_center(move):
        r, c = move
        return abs(r - 10) + abs(c - 10)

    best_move = None
    best_score = -10**18

    # Precompute urgent statuses
    my_atari_libs = set()
    seen_groups = set()
    for stone, (grp, llibs, libs) in my_info.items():
        gid = min(grp)
        if gid in seen_groups:
            continue
        seen_groups.add(gid)
        if llibs == 1:
            my_atari_libs |= libs

    opp_atari_libs = set()
    seen_groups = set()
    for stone, (grp, llibs, libs) in opp_info.items():
        gid = min(grp)
        if gid in seen_groups:
            continue
        seen_groups.add(gid)
        if llibs == 1:
            opp_atari_libs |= libs

    for move in candidates:
        if move in occupied:
            continue

        new_my, new_opp, captured, legal = simulate_move(move, my_set, opp_set)
        if not legal:
            continue

        score = 0

        # Tactical priority
        score += captured * 100000

        if move in my_atari_libs:
            score += 25000
        if move in opp_atari_libs:
            score += 30000

        # New group's liberties
        new_grp, new_libs = analyze_group(move, new_my, new_opp, color_me=True)
        llib = len(new_libs)
        score += min(llib, 4) * 250

        if llib == 1 and captured == 0:
            score -= 20000
        elif llib == 2 and captured == 0:
            score -= 2500

        # Neighbor relations
        friendly_nbs = 0
        enemy_nbs = 0
        connect_bonus = 0
        attack_bonus = 0
        distinct_friendly_groups = set()
        distinct_enemy_groups = set()

        for nb in neighbors(move):
            if nb in my_set:
                friendly_nbs += 1
                grp, llibs, libs = my_info[nb]
                distinct_friendly_groups.add(min(grp))
                connect_bonus += 300
                if llibs == 1:
                    connect_bonus += 3000
                elif llibs == 2:
                    connect_bonus += 700
            elif nb in opp_set:
                enemy_nbs += 1
                grp, llibs, libs = opp_info[nb]
                distinct_enemy_groups.add(min(grp))
                attack_bonus += 200
                if llibs == 1:
                    attack_bonus += 6000
                elif llibs == 2:
                    attack_bonus += 1200

        if len(distinct_friendly_groups) >= 2:
            score += 1800 * len(distinct_friendly_groups)
        if len(distinct_enemy_groups) >= 2:
            score += 900 * len(distinct_enemy_groups)

        score += connect_bonus + attack_bonus
        score += friendly_nbs * 120 + enemy_nbs * 80

        # Creating pressure: count adjacent opponent groups put into atari
        checked = set()
        for nb in neighbors(move):
            if nb in new_opp and nb not in checked:
                grp, libs = analyze_group(nb, new_my, new_opp, color_me=False)
                checked |= grp
                if len(libs) == 1:
                    score += 2200
                elif len(libs) == 2:
                    score += 500

        # Avoid filling own eye unless tactically valuable
        if eye_like(move, my_set, opp_set) and captured == 0:
            score -= 5000

        # Board preference: mild center preference early, weaker later
        stones_played = len(me) + len(opponent)
        if stones_played < 20:
            score -= distance_to_center(move) * 25
        else:
            score -= distance_to_center(move) * 6

        # Slight preference against first line / extreme edge unless tactical
        r, c = move
        if r in (1, BOARD_SIZE) or c in (1, BOARD_SIZE):
            score -= 120
        if r in (2, BOARD_SIZE - 1) or c in (2, BOARD_SIZE - 1):
            score -= 40

        # Small deterministic tiebreak
        score += (20 - abs(r - 10)) + (20 - abs(c - 10))
        score -= (r * 0.001 + c * 0.0001)

        if score > best_score:
            best_score = score
            best_move = move

    if best_move is not None:
        return best_move, memory

    # Full safety fallback: first legal move on board
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            mv = (r, c)
            if mv not in occupied and is_legal(mv):
                return mv, memory

    return (0, 0), memory
