
from collections import deque


# Axial directions for coordinates:
# q = column
# s = row + floor(column / 2)
#
# These produce the column-parity neighborhood described in the prompt.
_AXIAL_DIRS = (
    (0, 1),
    (1, 1),
    (1, 0),
    (0, -1),
    (-1, -1),
    (-1, 0),
)


class _Geometry:
    def __init__(self, valid_mask):
        self.rows = len(valid_mask)
        self.cols = len(valid_mask[0]) if self.rows else 0

        cells = []
        valid = set()

        for r in range(self.rows):
            for c in range(self.cols):
                if bool(valid_mask[r][c]):
                    p = (r, c)
                    cells.append(p)
                    valid.add(p)

        self.cells = cells
        self.valid = valid

        self.neighbors = {}
        for r, c in cells:
            q = c
            s = r + c // 2
            ns = []

            for dq, ds in _AXIAL_DIRS:
                nq = q + dq
                ns_axial = s + ds
                nr = ns_axial - nq // 2
                nc = nq
                p = (nr, nc)
                if p in valid:
                    ns.append(p)

            self.neighbors[(r, c)] = tuple(ns)

        # A regular hexagon has boundaries at the extrema of q, s, and s-q.
        axial_values = []
        for r, c in cells:
            q = c
            s = r + c // 2
            axial_values.append((q, s, s - q))

        if axial_values:
            min_q = min(x[0] for x in axial_values)
            max_q = max(x[0] for x in axial_values)
            min_s = min(x[1] for x in axial_values)
            max_s = max(x[1] for x in axial_values)
            min_t = min(x[2] for x in axial_values)
            max_t = max(x[2] for x in axial_values)
        else:
            min_q = max_q = min_s = max_s = min_t = max_t = 0

        self.edge_map = {}
        corner_cells = []

        for r, c in cells:
            q = c
            s = r + c // 2
            t = s - q

            tags = []
            if q == min_q:
                tags.append(0)
            if q == max_q:
                tags.append(1)
            if s == min_s:
                tags.append(2)
            if s == max_s:
                tags.append(3)
            if t == min_t:
                tags.append(4)
            if t == max_t:
                tags.append(5)

            # Corners do not count as edge cells for a fork.
            if len(tags) == 1:
                self.edge_map[(r, c)] = 1 << tags[0]
            else:
                self.edge_map[(r, c)] = 0

            if len(tags) >= 2:
                corner_cells.append((r, c))

        corner_cells.sort()
        self.corner_map = {
            cell: 1 << i for i, cell in enumerate(corner_cells)
        }

        # Degree-based boundary detection is robust for flood filling.
        self.boundary = {
            p for p in cells if len(self.neighbors[p]) < 6
        }

        self.min_q = min_q
        self.max_q = max_q
        self.min_s = min_s
        self.max_s = max_s

        self.center_q = (min_q + max_q) / 2.0
        self.center_s = (min_s + max_s) / 2.0


def _components(stones, geom):
    stones = set(stones)
    labels = {}
    infos = []

    for start in stones:
        if start in labels or start not in geom.valid:
            continue

        idx = len(infos)
        stack = [start]
        labels[start] = idx

        edge_mask = 0
        corner_mask = 0
        size = 0

        while stack:
            p = stack.pop()
            size += 1
            edge_mask |= geom.edge_map.get(p, 0)
            corner_mask |= geom.corner_map.get(p, 0)

            for n in geom.neighbors[p]:
                if n in stones and n not in labels:
                    labels[n] = idx
                    stack.append(n)

        infos.append((edge_mask, corner_mask, size))

    return labels, infos


def _move_features(move, labels, infos, geom):
    edge_mask = geom.edge_map.get(move, 0)
    corner_mask = geom.corner_map.get(move, 0)
    size = 1
    component_ids = set()

    for n in geom.neighbors[move]:
        idx = labels.get(n)
        if idx is not None:
            component_ids.add(idx)

    for idx in component_ids:
        em, cm, sz = infos[idx]
        edge_mask |= em
        corner_mask |= cm
        size += sz

    return (
        edge_mask,
        corner_mask,
        size,
        len(component_ids),
        component_ids,
    )


def _has_ring_after(base_stones, move, geom):
    """
    Test whether base_stones plus move surrounds at least one board cell.

    Non-player cells are flood-filled from the outside boundary. Player cells
    are normally walls. A player cell not adjacent to the exterior after being
    opened represents a player-owned cell enclosed by a ring.
    """
    blocked = base_stones
    seen = set()
    queue = deque()

    def is_blocked(p):
        return p == move or p in blocked

    for p in geom.boundary:
        if not is_blocked(p):
            seen.add(p)
            queue.append(p)

    while queue:
        p = queue.popleft()
        for n in geom.neighbors[p]:
            if n not in seen and not is_blocked(n):
                seen.add(n)
                queue.append(n)

    blocked_count = len(blocked) + (0 if move in blocked else 1)
    passable_count = len(geom.cells) - blocked_count

    # An unreachable empty or opponent-occupied cell is enclosed.
    if len(seen) < passable_count:
        return True

    # Also detect rings whose enclosed cells are occupied by the ring owner.
    for p in blocked:
        if p in geom.boundary:
            continue
        if not any(n in seen for n in geom.neighbors[p]):
            return True

    if move not in geom.boundary:
        if not any(n in seen for n in geom.neighbors[move]):
            return True

    return False


def _winning_moves(stones, other, geom, stop_after=None):
    stones = set(stones)
    occupied = stones | set(other)
    labels, infos = _components(stones, geom)
    result = []

    for move in geom.cells:
        if move in occupied:
            continue

        edge_mask, corner_mask, _, _, _ = _move_features(
            move, labels, infos, geom
        )

        # Bridge or fork.
        if corner_mask.bit_count() >= 2 or edge_mask.bit_count() >= 3:
            result.append(move)
            if stop_after is not None and len(result) >= stop_after:
                return result
            continue

        # A newly completed ring must connect to at least two friendly stones.
        friendly_neighbors = 0
        for n in geom.neighbors[move]:
            if n in stones:
                friendly_neighbors += 1

        if friendly_neighbors >= 2 and _has_ring_after(stones, move, geom):
            result.append(move)
            if stop_after is not None and len(result) >= stop_after:
                return result

    return result


def _hex_distance_from_center(move, geom):
    r, c = move
    q = c
    s = r + c // 2

    dq = q - geom.center_q
    ds = s - geom.center_s
    return max(abs(dq), abs(ds), abs(ds - dq))


def _color_move_score(move, stones, labels, infos, geom, move_number):
    stones = set(stones)

    edge_mask, corner_mask, size, merged_count, component_ids = (
        _move_features(move, labels, infos, geom)
    )

    edge_count = edge_mask.bit_count()
    corner_count = corner_mask.bit_count()

    score = 0.0

    # Fork and bridge development.
    if edge_count == 1:
        score += 125.0
    elif edge_count == 2:
        score += 700.0
    elif edge_count >= 3:
        score += 100000.0

    if corner_count == 1:
        score += 155.0
    elif corner_count >= 2:
        score += 100000.0

    friendly_neighbors = [
        n for n in geom.neighbors[move] if n in stones
    ]
    adjacent_count = len(friendly_neighbors)

    score += adjacent_count * 31.0
    score += merged_count * 48.0
    score += min(size, 24) * 4.0

    if merged_count >= 2:
        score += 75.0 * (merged_count - 1)

    # Reward separated friendly neighbors, which are useful for rings and
    # for joining arms of a larger structure.
    ordered = list(geom.neighbors[move])
    friendly_positions = [
        i for i, p in enumerate(ordered) if p in stones
    ]

    for i in range(len(friendly_positions)):
        for j in range(i + 1, len(friendly_positions)):
            a = friendly_positions[i]
            b = friendly_positions[j]
            cyclic_gap = min((a - b) % 6, (b - a) % 6)

            if cyclic_gap >= 2:
                score += 27.0

            ia = labels.get(ordered[a])
            ib = labels.get(ordered[b])
            if ia is not None and ib is not None and ia != ib:
                score += 35.0

    # Mild preference for useful two-neighbor placements over overfilling.
    if adjacent_count == 2:
        score += 32.0
    elif adjacent_count >= 5:
        score -= 18.0

    # Central influence is especially valuable early.
    center_distance = _hex_distance_from_center(move, geom)
    if move_number < 12:
        score -= center_distance * 12.0
    elif move_number < 35:
        score -= center_distance * 5.0
    else:
        score -= center_distance * 1.5

    if adjacent_count == 0:
        if move_number < 4:
            score -= 8.0
        else:
            score -= 42.0

    # Corners are useful for bridges but should not dominate early play.
    if move in geom.corner_map:
        score += 45.0
        if move_number < 8:
            score -= 30.0

    # Small deterministic tie-breaker.
    r, c = move
    score += ((r * 37 + c * 71 + move_number * 13) % 23) * 0.013

    return score


def _choose_move(me, opp, valid_mask):
    geom = _Geometry(valid_mask)
    me_set = {p for p in me if p in geom.valid}
    opp_set = {p for p in opp if p in geom.valid}
    occupied = me_set | opp_set

    legal = [p for p in geom.cells if p not in occupied]
    if not legal:
        return None

    move_number = len(occupied)

    my_labels, my_infos = _components(me_set, geom)
    opp_labels, opp_infos = _components(opp_set, geom)

    def my_positional(move):
        attack = _color_move_score(
            move, me_set, my_labels, my_infos, geom, move_number
        )
        defense = _color_move_score(
            move, opp_set, opp_labels, opp_infos, geom, move_number
        )
        return attack + 0.72 * defense

    # Always take an immediate win.
    my_wins = _winning_moves(me_set, opp_set, geom)
    if my_wins:
        return max(my_wins, key=my_positional)

    # An opponent winning cell must be occupied immediately.
    opp_wins = _winning_moves(opp_set, me_set, geom)
    if opp_wins:
        return max(opp_wins, key=my_positional)

    attack_scores = {}
    defense_scores = {}
    combined_scores = {}

    for move in legal:
        attack = _color_move_score(
            move, me_set, my_labels, my_infos, geom, move_number
        )
        defense = _color_move_score(
            move, opp_set, opp_labels, opp_infos, geom, move_number
        )

        attack_scores[move] = attack
        defense_scores[move] = defense
        combined_scores[move] = attack + 0.72 * defense

    search_width = 30 if len(legal) < 85 else 24

    attack_candidates = sorted(
        legal,
        key=lambda p: attack_scores[p],
        reverse=True,
    )[:search_width]

    # Include strongly local moves even if their static score narrowly misses
    # the shortlist.
    local_candidates = []
    for move in legal:
        friendly = sum(1 for n in geom.neighbors[move] if n in me_set)
        if friendly >= 2:
            local_candidates.append(move)

    candidate_set = set(attack_candidates)
    candidate_set.update(
        sorted(
            local_candidates,
            key=lambda p: attack_scores[p],
            reverse=True,
        )[:12]
    )

    threat_counts = {}
    threat_targets = {}
    double_threats = []

    # Search for moves that produce one or two immediate winning replies.
    for move in candidate_set:
        wins = _winning_moves(
            me_set | {move},
            opp_set,
            geom,
            stop_after=2,
        )
        threat_counts[move] = len(wins)
        threat_targets[move] = wins

        if len(wins) >= 2:
            value = combined_scores[move] + 10000.0
            double_threats.append((value, move))

    # A double threat is a forced win when the opponent currently has no
    # immediate winning move.
    if double_threats:
        double_threats.sort(reverse=True)
        return double_threats[0][1]

    # Find cells where the opponent could create a double threat next turn.
    opponent_candidates = sorted(
        legal,
        key=lambda p: defense_scores[p],
        reverse=True,
    )[:search_width]

    opponent_local = []
    for move in legal:
        friendly = sum(1 for n in geom.neighbors[move] if n in opp_set)
        if friendly >= 2:
            opponent_local.append(move)

    opponent_candidate_set = set(opponent_candidates)
    opponent_candidate_set.update(
        sorted(
            opponent_local,
            key=lambda p: defense_scores[p],
            reverse=True,
        )[:12]
    )

    dangerous_setups = set()

    for move in opponent_candidate_set:
        wins = _winning_moves(
            opp_set | {move},
            me_set,
            geom,
            stop_after=2,
        )
        if len(wins) >= 2:
            dangerous_setups.add(move)

    final_scores = dict(combined_scores)

    for move in legal:
        tc = threat_counts.get(move, 0)

        # A single threat gains tempo by forcing a particular reply.
        if tc == 1:
            final_scores[move] += 1900.0

            target = threat_targets[move][0]
            # Prefer threats whose forced block still leaves a strong shape.
            final_scores[move] += 0.08 * defense_scores.get(target, 0.0)

        # Occupying an opponent double-threat setup is highly urgent.
        if move in dangerous_setups:
            final_scores[move] += 4800.0

    # If several opponent double-threat setups exist, static defense cannot
    # cover them all. Prefer creating a forcing threat when possible.
    if len(dangerous_setups) >= 2:
        forcing_moves = [
            p for p in candidate_set if threat_counts.get(p, 0) == 1
        ]
        if forcing_moves:
            return max(forcing_moves, key=lambda p: final_scores[p])

    return max(legal, key=lambda p: final_scores[p])


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    valid_mask
) -> tuple[int, int]:
    """
    Return a legal Havannah move.
    """
    # Establish a legal fallback before doing any strategic calculations.
    occupied = set(me) | set(opp)
    fallback = None

    try:
        rows = len(valid_mask)
        cols = len(valid_mask[0]) if rows else 0

        for r in range(rows):
            for c in range(cols):
                if bool(valid_mask[r][c]) and (r, c) not in occupied:
                    fallback = (r, c)
                    break
            if fallback is not None:
                break

        if fallback is None:
            # A legal state should never reach this condition.
            return (0, 0)

        move = _choose_move(me, opp, valid_mask)

        if move is not None:
            r, c = move
            if (
                0 <= r < rows
                and 0 <= c < cols
                and bool(valid_mask[r][c])
                and move not in occupied
            ):
                return move

        return fallback

    except Exception:
        # Preserve legality even if an unusual mask implementation or
        # unexpected state causes a strategic calculation to fail.
        if fallback is not None:
            return fallback

        # Last-resort scan, kept separate in case failure occurred early.
        try:
            for r in range(len(valid_mask)):
                for c in range(len(valid_mask[r])):
                    if bool(valid_mask[r][c]) and (r, c) not in occupied:
                        return (r, c)
        except Exception:
            pass

        return (0, 0)
