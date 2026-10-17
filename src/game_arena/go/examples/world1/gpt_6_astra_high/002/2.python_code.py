
import math
import time

SIZE = 19
POINTS = SIZE * SIZE
FULL = (1 << POINTS) - 1
LEFT = sum(1 << (r * SIZE) for r in range(SIZE))
RIGHT = LEFT << (SIZE - 1)
NOT_LEFT = FULL ^ LEFT
NOT_RIGHT = FULL ^ RIGHT

NEIGHBORS = []
DIAGONALS = []
NBITS = []
EDGE = []

for p in range(POINTS):
    r, c = divmod(p, SIZE)
    ns = []
    ds = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < SIZE and 0 <= cc < SIZE:
            ns.append(rr * SIZE + cc)
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < SIZE and 0 <= cc < SIZE:
            ds.append(rr * SIZE + cc)
    NEIGHBORS.append(tuple(ns))
    DIAGONALS.append(tuple(ds))
    NBITS.append(sum(1 << q for q in ns))
    EDGE.append(min(r, c, 18 - r, 18 - c))

KERNEL = (1.0, 0.68, 0.43, 0.26, 0.14, 0.075, 0.035)
STENCILS = []
for p in range(POINTS):
    r, c = divmod(p, SIZE)
    stencil = []
    for dr in range(-6, 7):
        rr = r + dr
        if not 0 <= rr < SIZE:
            continue
        reach = 6 - abs(dr)
        for dc in range(-reach, reach + 1):
            cc = c + dc
            if 0 <= cc < SIZE:
                stencil.append((rr * SIZE + cc,
                                KERNEL[abs(dr) + abs(dc)]))
    STENCILS.append(tuple(stencil))

_HISTORY = set()


def _bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def _expand(mask):
    return ((mask << SIZE) | (mask >> SIZE)
            | ((mask & NOT_RIGHT) << 1)
            | ((mask & NOT_LEFT) >> 1)) & FULL


def _worth(stones):
    n = stones.bit_count()
    return 6.0 + 4.0 * n + 2.0 * math.sqrt(n)


class Board:
    __slots__ = ("black", "white", "empty", "gid", "groups")

    def __init__(self, black, white):
        self.black = black
        self.white = white
        self.empty = FULL ^ (black | white)
        self.gid = [-1] * POINTS
        self.groups = {}

        for color, occupied in ((1, black), (-1, white)):
            remaining = occupied
            while remaining:
                first = remaining & -remaining
                stones = first
                while True:
                    grown = stones | (_expand(stones) & occupied)
                    if grown == stones:
                        break
                    stones = grown
                anchor = first.bit_length() - 1
                self.groups[anchor] = (
                    color, stones, _expand(stones) & self.empty
                )
                for p in _bits(stones):
                    self.gid[p] = anchor
                remaining &= ~stones

    def preview(self, p, color):
        bit = 1 << p
        if not self.empty & bit:
            return None

        friends = set()
        enemies = set()
        for q in NEIGHBORS[p]:
            g = self.gid[q]
            if g >= 0:
                if self.groups[g][0] == color:
                    friends.add(g)
                else:
                    enemies.add(g)

        captured = 0
        for g in enemies:
            group = self.groups[g]
            if group[2] == bit:
                captured |= group[1]

        stones = bit
        for g in friends:
            stones |= self.groups[g][1]

        empty = (self.empty | captured) & ~bit
        liberties = _expand(stones) & empty
        if not liberties:
            return None

        # With no previous opponent position, a ko recapture cannot be
        # distinguished from a legal first ko capture. Avoid both at root.
        ko_shape = (
            captured.bit_count() == 1
            and stones == bit
            and liberties.bit_count() == 1
        )
        return (friends, enemies, captured, stones, liberties, empty, ko_shape)

    def play(self, p, color, preview=None):
        data = preview if preview is not None else self.preview(p, color)
        if data is None:
            return None

        friends, enemies, captured, stones, liberties, empty, ko = data
        bit = 1 << p
        result = object.__new__(Board)
        result.empty = empty
        result.gid = self.gid[:]
        result.groups = self.groups.copy()

        if color == 1:
            result.black = self.black | bit
            result.white = self.white & ~captured
        else:
            result.white = self.white | bit
            result.black = self.black & ~captured

        for g in friends:
            del result.groups[g]

        for g in enemies:
            old = self.groups[g]
            if old[1] & captured:
                del result.groups[g]
            else:
                result.groups[g] = (old[0], old[1], old[2] & ~bit)

        for q in _bits(captured):
            result.gid[q] = -1

        result.groups[p] = (color, stones, liberties)
        for q in _bits(stones):
            result.gid[q] = p

        # Captures also give liberties to friendly groups not joined by
        # the newly played stone.
        for q in _bits(captured):
            qbit = 1 << q
            for z in NEIGHBORS[q]:
                g = result.gid[z]
                if g >= 0 and g != p:
                    old = result.groups[g]
                    if not old[2] & qbit:
                        result.groups[g] = (
                            old[0], old[1], old[2] | qbit
                        )
        return result


class Reader:
    """Bounded local AND/OR capture search; 1=dead, -1=escapes, 0=unknown."""

    def __init__(self, deadline):
        self.deadline = deadline
        self.cache = {}
        self.nodes = 0
        self.budget = 0
        self.attacker = 1
        self.escape = 3

    def read(self, board, anchor, turn, budget=180, depth=36, escape=3):
        g = board.gid[anchor]
        if g < 0:
            return 1
        self.attacker = -board.groups[g][0]
        self.escape = escape
        self.nodes = 0
        self.budget = budget
        return self._search(board, anchor, turn, depth)

    def _search(self, board, anchor, turn, depth):
        self.nodes += 1
        if self.nodes > self.budget:
            return 0
        if self.nodes & 15 == 0 and time.perf_counter() >= self.deadline:
            return 0

        gid = board.gid[anchor]
        if gid < 0 or board.groups[gid][0] == self.attacker:
            return 1

        group = board.groups[gid]
        liberties = group[2]
        count = liberties.bit_count()
        if count >= self.escape:
            return -1
        if depth <= 0:
            return 0

        key = (board.black, board.white, anchor, turn,
               self.attacker, self.escape)
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        attacking = turn == self.attacker

        if attacking and count == 1:
            p = liberties.bit_length() - 1
            data = board.preview(p, turn)
            if data is None:
                return -1
            if data[6]:
                return 0
            return 1

        moves = set(_bits(liberties))
        if not attacking:
            opposing = board.black if self.attacker == 1 else board.white
            adjacent = _expand(group[1]) & opposing
            checked = set()
            for p in _bits(adjacent):
                enemy_gid = board.gid[p]
                if enemy_gid in checked:
                    continue
                checked.add(enemy_gid)
                enemy = board.groups[enemy_gid]
                if enemy[2].bit_count() == 1:
                    moves.update(_bits(enemy[2]))

        options = []
        unknown = False
        for p in moves:
            data = board.preview(p, turn)
            if data is None:
                continue
            if data[6]:
                unknown = True
                continue
            if attacking:
                order = (NBITS[p] & board.empty).bit_count()
            else:
                order = data[4].bit_count() + 2 * data[2].bit_count()
            options.append((order, p, data))
        options.sort(key=lambda x: x[0], reverse=True)

        valid = 0
        for _, p, data in options:
            if self.nodes >= self.budget:
                unknown = True
                break
            child = board.play(p, turn, data)
            valid += 1
            result = self._search(child, anchor, -turn, depth - 1)
            if attacking and result == 1:
                self.cache[key] = 1
                return 1
            if not attacking and result == -1:
                self.cache[key] = -1
                return -1
            if result == 0:
                unknown = True

        # Passing can preserve a seki or two-eye group when all local
        # defensive placements would make its shape worse.
        if not attacking and count >= 2 and not unknown:
            result = self._search(board, anchor, self.attacker, depth - 1)
            if result == -1:
                self.cache[key] = -1
                return -1
            if result == 0:
                unknown = True

        if unknown:
            return 0
        if not valid and not attacking:
            return self._search(board, anchor, self.attacker, depth - 1)

        result = -1 if attacking else 1
        self.cache[key] = result
        return result


def _risk(result):
    if result == 1:
        return 1.0
    if result == -1:
        return 0.0
    return 0.35


def _territory_maps(board):
    mine = [0.0] * POINTS
    theirs = [0.0] * POINTS
    for p in _bits(board.black):
        for q, weight in STENCILS[p]:
            mine[q] += weight
    for p in _bits(board.white):
        for q, weight in STENCILS[p]:
            theirs[q] += weight

    enclosed = [0] * POINTS
    region_size = [POINTS] * POINTS
    remaining = board.empty
    while remaining:
        component = remaining & -remaining
        while True:
            grown = component | (_expand(component) & board.empty)
            if grown == component:
                break
            component = grown
        remaining &= ~component
        size = component.bit_count()
        if size > 30:
            continue
        border = _expand(component)
        has_me = bool(border & board.black)
        has_them = bool(border & board.white)
        owner = 1 if has_me and not has_them else (
            -1 if has_them and not has_me else 0
        )
        for p in _bits(component):
            enclosed[p] = owner
            region_size[p] = size

    denominator = [0.0] * POINTS
    interest = [0.0] * POINTS
    for p in _bits(board.empty):
        d = mine[p] + theirs[p] + 0.38
        denominator[p] = d
        terrain = 1.0 / (1.0 + 0.15 * EDGE[p])
        if enclosed[p] == 1:
            terrain = 0.0
        elif enclosed[p] == -1 and region_size[p] <= 6:
            terrain *= 0.25
        interest[p] = terrain * (2.0 * theirs[p] + 0.38) / d

    return mine, theirs, enclosed, region_size, denominator, interest


def _fork_penalty(board, deadline):
    """Look for an opponent move that creates two independent ataris."""
    attacks = {}
    for gid, group in board.groups.items():
        if group[0] == 1 and group[2].bit_count() == 2:
            for p in _bits(group[2]):
                attacks.setdefault(p, []).append(gid)

    worst = 0.0
    for p, targets in attacks.items():
        if len(targets) < 2:
            continue
        if time.perf_counter() >= deadline:
            break
        data = board.preview(p, -1)
        if data is None or data[6]:
            continue
        child = board.play(p, -1, data)

        defenses = set()
        threatened = []
        for anchor in targets:
            gid = child.gid[anchor]
            if gid < 0:
                continue
            group = child.groups[gid]
            if group[2].bit_count() != 1:
                continue
            threatened.append((anchor, _worth(group[1])))
            defenses.update(_bits(group[2]))
            adjacent = _expand(group[1]) & child.white
            checked = set()
            for q in _bits(adjacent):
                eg = child.gid[q]
                if eg in checked:
                    continue
                checked.add(eg)
                enemy = child.groups[eg]
                if enemy[2].bit_count() == 1:
                    defenses.update(_bits(enemy[2]))

        if len(threatened) < 2:
            continue

        unavoidable = sum(value for _, value in threatened)
        for defense in defenses:
            dd = child.preview(defense, 1)
            if dd is None or dd[6]:
                continue
            reply = child.play(defense, 1, dd)
            loss = 0.0
            for anchor, value in threatened:
                gid = reply.gid[anchor]
                if gid < 0:
                    loss += value
                    continue
                group = reply.groups[gid]
                if group[2].bit_count() == 1:
                    capture = group[2].bit_length() - 1
                    cd = reply.preview(capture, -1)
                    if cd is not None:
                        loss += value * (0.35 if cd[6] else 1.0)
            unavoidable = min(unavoidable, loss)
            if unavoidable == 0.0:
                break
        worst = max(worst, 0.8 * unavoidable)
    return worst


def policy(me: list[tuple[int, int]],
           opponent: list[tuple[int, int]]) -> tuple[int, int]:
    start = time.perf_counter()
    deadline = start + 0.88

    black = 0
    white = 0
    for r, c in me:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            black |= 1 << ((r - 1) * SIZE + c - 1)
    for r, c in opponent:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            white |= 1 << ((r - 1) * SIZE + c - 1)
    white &= ~black

    total = (black | white).bit_count()
    if total <= 1:
        _HISTORY.clear()
    _HISTORY.add((black, white))

    if total == 0:
        p = 3 * SIZE + 3
        _HISTORY.add((1 << p, 0))
        return (4, 4)

    board = Board(black, white)
    if not board.empty:
        return (0, 0)

    reader = Reader(min(deadline, start + 0.17))
    root_risk = {}
    own_small = [
        (gid, group) for gid, group in board.groups.items()
        if group[0] == 1 and group[2].bit_count() <= 2
    ]
    own_small.sort(
        key=lambda item: (item[1][2].bit_count(), -item[1][1].bit_count())
    )

    for gid, group in own_small:
        if group[2].bit_count() == 1:
            risk = _risk(reader.read(board, gid, -1, budget=30))
        elif time.perf_counter() < start + 0.15:
            risk = _risk(reader.read(board, gid, -1, budget=220))
        else:
            risk = 0.0
        root_risk[gid] = risk

    baseline_loss = sum(
        risk * _worth(board.groups[gid][1])
        for gid, risk in root_risk.items()
    )
    reader.deadline = deadline

    mine, theirs, enclosed, region_size, denom, interest = \
        _territory_maps(board)

    occupied_points = list(_bits(black | white))
    opening_bonus = {}
    if total < 24:
        for r, c in ((3, 3), (3, 15), (15, 3), (15, 15)):
            p = r * SIZE + c
            distance = min(
                abs(r - q // SIZE) + abs(c - q % SIZE)
                for q in occupied_points
            )
            if distance >= 6:
                opening_bonus[p] = 7.5 if total < 8 else 4.0

    candidates = []
    development = max(0.15, 1.0 - total / 180.0)

    for p in _bits(board.empty):
        data = board.preview(p, 1)
        if data is None or data[6]:
            continue
        friends, enemies, captured, stones, liberties, _, _ = data
        new_key = (black | (1 << p), white & ~captured)
        if new_key in _HISTORY:
            continue

        adjacent_own = sum(bool(black & (1 << q)) for q in NEIGHBORS[p])
        adjacent_enemy = sum(bool(white & (1 << q)) for q in NEIGHBORS[p])

        # Preserve actual eyes, not just vaguely enclosed points.
        if adjacent_own == len(NEIGHBORS[p]) and not captured:
            bad_diagonals = sum(
                not bool(black & (1 << q)) for q in DIAGONALS[p]
            )
            allowance = 1 if len(DIAGONALS[p]) == 4 else 0
            if bad_diagonals <= allowance:
                continue

        gain = 0.0
        for q, weight in STENCILS[p]:
            if interest[q]:
                gain += interest[q] * weight / (denom[q] + weight)
        strategic = 0.85 * gain

        edge = EDGE[p]
        if edge == 0:
            strategic -= 7.0 * development
        elif edge == 1:
            strategic -= 2.5 * development
        elif edge == 2:
            strategic += 1.0 * development
        elif edge == 3:
            strategic += 1.3 * development

        strategic += opening_bonus.get(p, 0.0)
        strategic += 2.0 * max(0, len(friends) - 1)
        strategic += 1.4 * max(0, len(enemies) - 1)
        strategic -= 0.8 * max(0, adjacent_own - 1)

        diagonal_own = sum(
            bool(black & (1 << q)) for q in DIAGONALS[p]
        )
        strategic += 0.5 * min(2, diagonal_own)

        if adjacent_enemy and not adjacent_own:
            strategic -= 1.0 + 1.4 * development
        if not adjacent_own and mine[p] > 0.15:
            strategic += 0.65
        strategic -= 1.2 * max(0.0, theirs[p] - mine[p] - 1.5)

        if enclosed[p] == 1:
            strategic -= 24.0
        elif enclosed[p] == -1 and region_size[p] <= 6:
            strategic -= 15.0

        # Empty triangles have poor efficiency, unless connecting groups
        # or winning a tactical fight compensates for them.
        if adjacent_own >= 2 and len(friends) == 1 and diagonal_own:
            strategic -= 2.2

        tactical = 0.0
        for gid in enemies:
            group = board.groups[gid]
            if group[1] & captured:
                tactical += _worth(group[1])
            else:
                left = (group[2] & ~(1 << p)).bit_count()
                if left == 1:
                    tactical += 3.0 + math.sqrt(group[1].bit_count())
                elif left == 2:
                    tactical += 0.8

        for gid, risk in root_risk.items():
            if not risk:
                continue
            old = board.groups[gid]
            if gid in friends:
                if liberties.bit_count() >= 2:
                    tactical += risk * _worth(old[1])
            elif _expand(old[1]) & captured:
                tactical += risk * _worth(old[1])

        liberty_count = liberties.bit_count()
        if liberty_count == 1:
            tactical -= 1.15 * _worth(stones)
        elif liberty_count == 2:
            tactical -= 2.0 + min(5.0, 0.5 * stones.bit_count())

        strategic += ((p * 73 + total * 19) % 101) * 0.00002
        candidates.append((strategic + tactical, p, strategic, data))

    if not candidates:
        return (0, 0)

    candidates.sort(key=lambda item: item[0], reverse=True)
    shortlist = candidates[:28]
    evaluated = []

    for cheap, p, strategic, data in shortlist:
        if time.perf_counter() >= deadline - 0.025:
            break

        child = board.play(p, 1, data)
        friends, enemies, captured, stones, liberties, _, _ = data
        score = strategic

        for gid in enemies:
            group = board.groups[gid]
            if group[1] & captured:
                score += _worth(group[1])

        affected = {p}
        for anchor in root_risk:
            gid = child.gid[anchor]
            if gid >= 0:
                affected.add(gid)

        loss = 0.0
        for gid in affected:
            group = child.groups[gid]
            nlibs = group[2].bit_count()
            if nlibs >= 3:
                risk = 0.0
            elif (gid in root_risk
                  and board.groups.get(gid) == group):
                risk = root_risk[gid]
            else:
                risk = _risk(reader.read(
                    child, gid, -1, budget=280, depth=44
                ))
            loss += risk * _worth(group[1])

        score += baseline_loss - loss

        # Read small, tightly enclosed three-liberty shapes more deeply.
        current = child.groups[p]
        if current[2].bit_count() == 3:
            exits = _expand(current[2]) & child.empty
            if exits.bit_count() <= 4 and theirs[p] > mine[p]:
                result = reader.read(
                    child, p, -1, budget=180, depth=12, escape=4
                )
                if result == 1:
                    score -= _worth(current[1])

        ataris = []
        for old_gid in enemies:
            old_group = board.groups[old_gid]
            if old_group[1] & captured:
                continue
            anchor = (old_group[1] & -old_group[1]).bit_length() - 1
            gid = child.gid[anchor]
            if gid < 0:
                continue
            group = child.groups[gid]
            nlibs = group[2].bit_count()
            if nlibs == 1:
                result = reader.read(
                    child, anchor, -1, budget=240, depth=40
                )
                value = _worth(group[1])
                if result == 1:
                    score += 0.88 * value
                elif result == 0:
                    score += 1.0 + 0.12 * value
                else:
                    score += 1.0 + 0.35 * math.sqrt(group[1].bit_count())
                ataris.append((group[2], value))
            elif nlibs == 2:
                score += 0.9

        # Two separate forced replies are more valuable than one.
        if len(ataris) >= 2:
            independent = {}
            for liberty, value in ataris:
                independent[liberty] = max(
                    independent.get(liberty, 0.0), value
                )
            values = sorted(independent.values(), reverse=True)
            if len(values) >= 2:
                score += 0.65 * values[1]

        evaluated.append((score, p, child))

    if not evaluated:
        # This path is only a time-budget fallback. Every candidate was
        # already checked for occupancy, suicide, ko shape, and repetition.
        score, p, _, data = candidates[0]
        if score <= 0.0:
            return (0, 0)
        chosen = board.play(p, 1, data)
    else:
        evaluated.sort(key=lambda item: item[0], reverse=True)
        best_score = -float("inf")
        chosen = None
        best_p = None
        for score, p, child in evaluated:
            if score <= best_score:
                break
            if time.perf_counter() < deadline - 0.012:
                score -= _fork_penalty(child, deadline - 0.005)
            if score > best_score:
                best_score = score
                best_p = p
                chosen = child
        if chosen is None or best_score <= 0.15:
            return (0, 0)
        p = best_p

    if len(_HISTORY) > 3000:
        _HISTORY.clear()
    _HISTORY.add((chosen.black, chosen.white))
    return (p // SIZE + 1, p % SIZE + 1)
