
from typing import List, Tuple, Set

BOARD_SIZE = 19
CENTER = 9  # 0-based center

# Precompute neighbors
NEIGHBORS = [[[] for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        if r > 0:
            NEIGHBORS[r][c].append((r - 1, c))
        if r + 1 < BOARD_SIZE:
            NEIGHBORS[r][c].append((r + 1, c))
        if c > 0:
            NEIGHBORS[r][c].append((r, c - 1))
        if c + 1 < BOARD_SIZE:
            NEIGHBORS[r][c].append((r, c + 1))

OPENING_POINTS = [
    (3, 3), (3, 15), (15, 3), (15, 15),   # 4-4 points
    (3, 9), (9, 3), (9, 15), (15, 9),     # side star-ish
    (9, 9),                               # center
    (3, 6), (3, 12), (6, 3), (6, 15),
    (12, 3), (12, 15), (15, 6), (15, 12)
]


def collect_group(board, r, c):
    color = board[r][c]
    stack = [(r, c)]
    seen = {(r, c)}
    stones = []
    liberties = set()

    while stack:
        x, y = stack.pop()
        stones.append((x, y))
        for nx, ny in NEIGHBORS[x][y]:
            v = board[nx][ny]
            if v == 0:
                liberties.add((nx, ny))
            elif v == color and (nx, ny) not in seen:
                seen.add((nx, ny))
                stack.append((nx, ny))
    return stones, liberties


def analyze_groups(board):
    gid = [[-1] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    groups = []

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0 and gid[r][c] == -1:
                stones, liberties = collect_group(board, r, c)
                idx = len(groups)
                for x, y in stones:
                    gid[x][y] = idx
                groups.append({
                    "color": board[r][c],
                    "stones": stones,
                    "liberties": liberties,
                    "size": len(stones),
                })
    return gid, groups


def simulate_move(board, r, c, color=1):
    if board[r][c] != 0:
        return None

    opp = 2 if color == 1 else 1
    b = [row[:] for row in board]
    b[r][c] = color

    removed = []
    checked = set()

    for nr, nc in NEIGHBORS[r][c]:
        if b[nr][nc] == opp and (nr, nc) not in checked:
            stones, libs = collect_group(b, nr, nc)
            for s in stones:
                checked.add(s)
            if len(libs) == 0:
                removed.extend(stones)

    if removed:
        for x, y in removed:
            b[x][y] = 0

    own_stones, own_libs = collect_group(b, r, c)
    if len(own_libs) == 0:
        return None

    return b, len(removed), own_stones, own_libs, removed


def quick_legal(board, groups, gid, r, c):
    if board[r][c] != 0:
        return False

    # Any adjacent empty point => immediate liberty
    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] == 0:
            return True

    # Capture makes move legal
    seen_opp = set()
    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] == 2:
            g = gid[nr][nc]
            if g not in seen_opp:
                seen_opp.add(g)
                if len(groups[g]["liberties"]) == 1 and (r, c) in groups[g]["liberties"]:
                    return True

    # Otherwise must connect to own groups that retain liberties
    combined_libs = set()
    seen_own = set()
    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] == 1:
            g = gid[nr][nc]
            if g not in seen_own:
                seen_own.add(g)
                combined_libs |= groups[g]["liberties"]

    combined_libs.discard((r, c))
    return len(combined_libs) > 0


def count_adjacent(board, r, c, color):
    s = 0
    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] == color:
            s += 1
    return s


def min_sq_dist_to_stones(r, c, stones):
    if not stones:
        return 999
    best = 10**9
    for x, y in stones:
        d = (r - x) * (r - x) + (c - y) * (c - y)
        if d < best:
            best = d
    return best


def quick_score(board, groups, gid, r, c, total_stones, all_stones):
    if not quick_legal(board, groups, gid, r, c):
        return -10**18

    score = 0

    own_adj = 0
    opp_adj = 0
    empty_adj = 0

    own_groups = set()
    opp_groups = set()

    for nr, nc in NEIGHBORS[r][c]:
        v = board[nr][nc]
        if v == 0:
            empty_adj += 1
        elif v == 1:
            own_adj += 1
            own_groups.add(gid[nr][nc])
        else:
            opp_adj += 1
            opp_groups.add(gid[nr][nc])

    capture_size = 0
    atari_attack = 0
    rescue_size = 0
    weak_connect_bonus = 0

    for g in opp_groups:
        libs = groups[g]["liberties"]
        sz = groups[g]["size"]
        if len(libs) == 1 and (r, c) in libs:
            capture_size += sz
        elif len(libs) == 2 and (r, c) in libs:
            atari_attack += sz

    for g in own_groups:
        libs = groups[g]["liberties"]
        sz = groups[g]["size"]
        if len(libs) == 1 and (r, c) in libs:
            rescue_size += sz
        elif len(libs) == 2 and (r, c) in libs:
            weak_connect_bonus += sz

    # Tactical urgency
    score += 22000 * capture_size
    score += 18000 * rescue_size
    score += 1800 * atari_attack
    score += 600 * weak_connect_bonus

    # Connectivity / shape
    if len(own_groups) >= 2:
        score += 1200 * (len(own_groups) - 1)
        score += 80 * sum(groups[g]["size"] for g in own_groups)

    score += 120 * own_adj
    score += 80 * opp_adj
    score += 50 * empty_adj

    # Avoid filling a likely own eye unless tactically necessary
    if capture_size == 0 and rescue_size == 0:
        if opp_adj == 0 and own_adj >= 3 and empty_adj <= 1:
            score -= 5000

    # Center / influence
    center_dist = abs(r - CENTER) + abs(c - CENTER)
    score += max(0, 16 - center_dist) * 12

    # Opening preference
    if total_stones < 10:
        if (r, c) in OPENING_POINTS:
            score += 1200
        d = min_sq_dist_to_stones(r, c, all_stones)
        score += min(d, 50) * 20

    # Prefer contested moves over isolated late-game random play
    if total_stones >= 10 and own_adj == 0 and opp_adj == 0:
        score -= 800

    # Slight preference for proximity to action
    local_density = 0
    for dr in (-2, -1, 0, 1, 2):
        nr = r + dr
        if 0 <= nr < BOARD_SIZE:
            rem = 2 - abs(dr)
            for dc in range(-rem, rem + 1):
                nc = c + dc
                if 0 <= nc < BOARD_SIZE and (dr != 0 or dc != 0):
                    if board[nr][nc] != 0:
                        local_density += 1
    score += 20 * local_density

    return score


def exact_refine_score(board, groups, gid, r, c, base_score):
    sim = simulate_move(board, r, c, 1)
    if sim is None:
        return None

    new_board, captured, own_stones, own_libs, removed = sim
    score = base_score

    # Exact tactical info
    score += 12000 * captured
    score += 35 * len(own_stones)
    score += 260 * len(own_libs)

    if captured == 0 and len(own_libs) == 1:
        score -= 15000
    elif captured == 0 and len(own_libs) == 2:
        score -= 1200

    # Reward saving original atari groups
    saved = 0
    connected = set()
    for nr, nc in NEIGHBORS[r][c]:
        if board[nr][nc] == 1:
            g = gid[nr][nc]
            connected.add(g)
            if len(groups[g]["liberties"]) == 1 and (r, c) in groups[g]["liberties"]:
                saved += groups[g]["size"]
    score += 5000 * saved
    if len(connected) >= 2:
        score += 1000 * (len(connected) - 1)

    # Check adjacent enemy groups after move
    seen = set()
    for nr, nc in NEIGHBORS[r][c]:
        if new_board[nr][nc] == 2 and (nr, nc) not in seen:
            stones, libs = collect_group(new_board, nr, nc)
            for s in stones:
                seen.add(s)
            if len(libs) == 1:
                score += 1600 * len(stones)
            elif len(libs) == 2:
                score += 220 * len(stones)

    # Small bonus for not being on the edge unless strategically useful
    if 0 < r < BOARD_SIZE - 1 and 0 < c < BOARD_SIZE - 1:
        score += 30

    return score


def generate_candidates(board, groups, gid):
    cands = set()

    # Urgent liberties of weak groups
    for g in groups:
        if len(g["liberties"]) <= 2:
            cands |= g["liberties"]

    # Nearby empty points around existing stones
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:
                for dr in (-2, -1, 0, 1, 2):
                    nr = r + dr
                    if 0 <= nr < BOARD_SIZE:
                        rem = 2 - abs(dr)
                        for dc in range(-rem, rem + 1):
                            nc = c + dc
                            if 0 <= nc < BOARD_SIZE and board[nr][nc] == 0:
                                cands.add((nr, nc))

    # Strategic opening points
    for p in OPENING_POINTS:
        if board[p[0]][p[1]] == 0:
            cands.add(p)

    return cands


def fallback_legal_move(board):
    # Prefer strategic points first
    seen = set()
    for p in OPENING_POINTS:
        seen.add(p)
        r, c = p
        if simulate_move(board, r, c, 1) is not None:
            return (r + 1, c + 1)

    # Then any legal point
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if (r, c) not in seen and simulate_move(board, r, c, 1) is not None:
                return (r + 1, c + 1)

    return (0, 0)


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Build board: 0 empty, 1 me, 2 opponent
    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]

    for r, c in me:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE:
            board[r - 1][c - 1] = 2

    total_stones = len(me) + len(opponent)
    all_stones = [(r - 1, c - 1) for r, c in me + opponent if 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE]

    # Fast opening: first move
    if total_stones == 0:
        return (4, 4)

    gid, groups = analyze_groups(board)
    candidates = generate_candidates(board, groups, gid)

    if not candidates:
        return fallback_legal_move(board)

    # Quick score all candidates
    scored = []
    for r, c in candidates:
        if board[r][c] != 0:
            continue
        s = quick_score(board, groups, gid, r, c, total_stones, all_stones)
        if s > -10**17:
            scored.append((s, r, c))

    if not scored:
        return fallback_legal_move(board)

    scored.sort(reverse=True)

    # Exact refinement on top candidates
    top_n = 30 if len(scored) > 30 else len(scored)
    best_score = None
    best_move = None

    for i in range(top_n):
        base, r, c = scored[i]
        s = exact_refine_score(board, groups, gid, r, c, base)
        if s is None:
            continue
        if best_score is None or s > best_score:
            best_score = s
            best_move = (r + 1, c + 1)

    if best_move is not None:
        return best_move

    return fallback_legal_move(board)
