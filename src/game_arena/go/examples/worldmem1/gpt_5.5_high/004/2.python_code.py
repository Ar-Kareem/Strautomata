
from __future__ import annotations

N = 19
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    if not isinstance(memory, dict):
        memory = {}

    board = [[0 for _ in range(N)] for _ in range(N)]
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N and board[r - 1][c - 1] == 0:
            board[r - 1][c - 1] = -1

    groups, gid = build_groups(board)
    total_stones = len(me) + len(opponent)
    ko_key = memory.get("last_own_board")

    best_move = None
    best_score = -10**18
    best_info = None

    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue
            info = analyze_move(board, groups, gid, r, c, ko_key)
            if info is None:
                continue
            sc = score_move(board, groups, gid, r, c, info, total_stones)
            # deterministic tiny tiebreaker
            sc += ((r + 3) * 37 + (c + 5) * 17 + total_stones * 13) % 97 * 0.0001
            if sc > best_score:
                best_score = sc
                best_move = (r, c)
                best_info = info

    # If every legal move is very bad, passing is safer than filling eyes or suicidally invading.
    if best_move is None or best_score < -65 or (total_stones > 300 and best_score < -5):
        memory["last_own_board"] = board_key(board)
        memory["turns"] = memory.get("turns", 0) + 1
        memory["last_action"] = (0, 0)
        return (0, 0), memory

    r, c = best_move
    after = apply_move(board, groups, gid, r, c)
    memory["last_own_board"] = board_key(after)
    memory["turns"] = memory.get("turns", 0) + 1
    memory["last_action"] = (r + 1, c + 1)

    return (r + 1, c + 1), memory


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def neighbors(r: int, c: int):
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if 0 <= rr < N and 0 <= cc < N:
            yield rr, cc


def build_groups(board):
    gid = [[-1 for _ in range(N)] for _ in range(N)]
    groups = []

    for r in range(N):
        for c in range(N):
            if board[r][c] == 0 or gid[r][c] != -1:
                continue

            color = board[r][c]
            idx = len(groups)
            stack = [(r, c)]
            gid[r][c] = idx
            stones = []
            liberties = set()

            while stack:
                x, y = stack.pop()
                stones.append((x, y))
                for nx, ny in neighbors(x, y):
                    v = board[nx][ny]
                    if v == 0:
                        liberties.add((nx, ny))
                    elif v == color and gid[nx][ny] == -1:
                        gid[nx][ny] = idx
                        stack.append((nx, ny))

            groups.append({
                "color": color,
                "stones": stones,
                "liberties": liberties,
                "size": len(stones),
            })

    return groups, gid


def board_key(board):
    # Compact, hashable board representation.
    return bytes((board[r][c] + 1) for r in range(N) for c in range(N))


def analyze_move(board, groups, gid, r: int, c: int, ko_key):
    if board[r][c] != 0:
        return None

    own_ids = set()
    opp_ids = set()
    empty_neighbors = 0

    for nr, nc in neighbors(r, c):
        v = board[nr][nc]
        if v == 0:
            empty_neighbors += 1
        elif v == 1:
            own_ids.add(gid[nr][nc])
        elif v == -1:
            opp_ids.add(gid[nr][nc])

    captured_ids = set()
    captured_count = 0
    for oid in opp_ids:
        libs = groups[oid]["liberties"]
        if len(libs) == 1 and (r, c) in libs:
            captured_ids.add(oid)
            captured_count += groups[oid]["size"]

    legal = False
    if captured_ids:
        legal = True
    elif empty_neighbors > 0:
        legal = True
    else:
        for oid in own_ids:
            if len(groups[oid]["liberties"]) > 1:
                legal = True
                break

    if not legal:
        return None

    # Approximate merged group liberties after playing. This is exact for non-captures
    # and good enough for tactical scoring with captures.
    new_libs = set()
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == 0:
            new_libs.add((nr, nc))

    new_size = 1
    for oid in own_ids:
        g = groups[oid]
        new_size += g["size"]
        new_libs.update(g["liberties"])
    new_libs.discard((r, c))

    # Captured stones become liberties, at least along the captured boundary.
    for cid in captured_ids:
        for s in groups[cid]["stones"]:
            new_libs.add(s)

    # Avoid simple immediate-ko recapture if it recreates our previous board.
    if ko_key is not None and captured_ids:
        after = apply_move(board, groups, gid, r, c)
        if board_key(after) == ko_key:
            return None

    return {
        "own_ids": own_ids,
        "opp_ids": opp_ids,
        "captured_ids": captured_ids,
        "captured_count": captured_count,
        "new_lib_count": len(new_libs),
        "new_size": new_size,
        "empty_neighbors": empty_neighbors,
    }


def apply_move(board, groups, gid, r: int, c: int):
    nb = [row[:] for row in board]
    nb[r][c] = 1

    captured_ids = set()
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == -1:
            oid = gid[nr][nc]
            if oid != -1 and len(groups[oid]["liberties"]) == 1 and (r, c) in groups[oid]["liberties"]:
                captured_ids.add(oid)

    for cid in captured_ids:
        for sr, sc in groups[cid]["stones"]:
            nb[sr][sc] = 0

    return nb


def is_eye(board, r: int, c: int, color: int) -> bool:
    if board[r][c] != 0:
        return False

    for nr, nc in neighbors(r, c):
        if board[nr][nc] != color:
            return False

    bad_diag = 0
    off_diag = 0
    for dr, dc in DIAGS:
        rr, cc = r + dr, c + dc
        if not in_bounds(rr, cc):
            off_diag += 1
        elif board[rr][cc] == -color:
            bad_diag += 1

    # In the corner or edge, one bad diagonal is usually fatal for a true eye.
    if off_diag >= 2:
        return bad_diag == 0
    if off_diag == 1:
        return bad_diag == 0
    return bad_diag <= 1


def score_move(board, groups, gid, r: int, c: int, info, total_stones: int) -> float:
    score = 0.0

    own_ids = info["own_ids"]
    opp_ids = info["opp_ids"]
    captured_ids = info["captured_ids"]
    captured = info["captured_count"]
    new_libs = info["new_lib_count"]
    new_size = info["new_size"]

    saving_atari = 0
    saving_second_line = 0
    attack_atari = 0
    pressure = 0

    # Captures are the most reliable source of profit.
    if captured:
        score += 120 * captured + 28 * captured * captured
        if len(captured_ids) >= 2:
            score += 35 * (len(captured_ids) - 1)
        for cid in captured_ids:
            cg = groups[cid]
            if cg["size"] >= 4:
                score += 35
            if is_near_edge_group(cg):
                score += 8

    # Save weak friendly groups.
    for oid in own_ids:
        g = groups[oid]
        libs = len(g["liberties"])
        sz = g["size"]
        if (r, c) in g["liberties"]:
            if libs == 1:
                saving_atari += sz
                score += 105 * sz + 12 * min(new_libs, 8)
            elif libs == 2:
                saving_second_line += sz
                score += 24 * sz + 5 * min(new_libs, 8)
            elif libs == 3:
                score += 7 * min(sz, 8)

    # Attack opponent groups by taking liberties.
    for oid in opp_ids:
        g = groups[oid]
        libs = len(g["liberties"])
        sz = g["size"]
        if (r, c) not in g["liberties"]:
            continue
        if libs == 1:
            continue
        elif libs == 2:
            attack_atari += sz
            score += 62 * sz
            if new_libs >= 3:
                score += 18
            else:
                score -= 18
        elif libs == 3:
            pressure += sz
            score += 14 * min(sz, 12)
        elif libs == 4:
            score += 4 * min(sz, 8)

    # Connections and cuts.
    if len(own_ids) >= 2:
        connected_size = sum(groups[x]["size"] for x in own_ids)
        score += 28 * (len(own_ids) - 1) + 3 * min(connected_size, 20)

        weak_connected = 0
        for oid in own_ids:
            if len(groups[oid]["liberties"]) <= 3:
                weak_connected += groups[oid]["size"]
        score += 9 * min(weak_connected, 15)

    if len(opp_ids) >= 2:
        cut_bonus = 24 * (len(opp_ids) - 1)
        weak_cut = 0
        for oid in opp_ids:
            if len(groups[oid]["liberties"]) <= 4:
                weak_cut += groups[oid]["size"]
        score += cut_bonus + 8 * min(weak_cut, 15)

    # Liberty and self-atari judgement.
    tactical = captured > 0 or saving_atari > 0 or attack_atari > 0
    if new_libs <= 1:
        if captured == 0:
            score -= 500
        else:
            score -= 95
            if captured == 1 and saving_atari == 0:
                score -= 75
    elif new_libs == 2:
        penalty = 35
        if captured:
            penalty -= 12 * min(captured, 3)
        if saving_atari:
            penalty -= 18
        if attack_atari and new_size <= 2:
            penalty += 15
        score -= max(0, penalty)
    elif new_libs == 3:
        score -= 4
    else:
        score += 2.2 * min(new_libs, 8)

    # Eye and territory-shape judgement.
    own_eye = is_eye(board, r, c, 1)
    opp_eye = is_eye(board, r, c, -1)

    if own_eye:
        if tactical:
            score -= 18
        else:
            score -= 125

    if opp_eye:
        if captured == 0 and attack_atari == 0:
            score -= 65 if total_stones < 240 else 35

    own_adj = 0
    opp_adj = 0
    off_adj = 0
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if not in_bounds(rr, cc):
            off_adj += 1
        elif board[rr][cc] == 1:
            own_adj += 1
        elif board[rr][cc] == -1:
            opp_adj += 1

    if own_adj + off_adj == 4 and not tactical:
        score -= 45
    if opp_adj + off_adj == 4 and captured == 0:
        score -= 55

    # Local influence and shape.
    local = local_features(board, r, c)
    own_near = local["own_near"]
    opp_near = local["opp_near"]
    closest_own = local["closest_own"]
    closest_opp = local["closest_opp"]

    if total_stones < 90 and not tactical:
        if closest_own <= 1:
            score -= 8
        elif closest_own == 2:
            score -= 3
        elif 3 <= closest_own <= 5:
            score += 5

        if closest_opp == 1 and own_adj == 0:
            score -= 6
        elif 2 <= closest_opp <= 4:
            score += 4

    if opp_near > own_near + 4 and new_libs <= 2 and captured == 0:
        score -= 20
    if own_near > opp_near + 6 and not tactical and own_eye:
        score -= 30

    score += 2.0 * min(own_near, 5)
    score += 1.5 * min(opp_near, 5)

    # Positional judgement: fuseki, sides, corners, and line value.
    score += positional_score(board, r, c, total_stones, tactical)

    # Prefer sente-looking boundary plays in the late middle game.
    if total_stones > 120:
        if own_adj > 0 and opp_adj > 0:
            score += 10
        if own_adj == 0 and opp_adj == 0:
            score -= 8

    return score


def is_near_edge_group(g) -> bool:
    for r, c in g["stones"]:
        if r <= 1 or c <= 1 or r >= N - 2 or c >= N - 2:
            return True
    return False


def local_features(board, r: int, c: int):
    own_near = 0.0
    opp_near = 0.0
    closest_own = 99
    closest_opp = 99

    r0 = max(0, r - 5)
    r1 = min(N, r + 6)
    c0 = max(0, c - 5)
    c1 = min(N, c + 6)

    for rr in range(r0, r1):
        for cc in range(c0, c1):
            v = board[rr][cc]
            if v == 0:
                continue
            d = max(abs(rr - r), abs(cc - c))
            if d == 0:
                continue
            weight = 1.0 / d
            if v == 1:
                own_near += weight
                if d < closest_own:
                    closest_own = d
            else:
                opp_near += weight
                if d < closest_opp:
                    closest_opp = d

    return {
        "own_near": own_near,
        "opp_near": opp_near,
        "closest_own": closest_own,
        "closest_opp": closest_opp,
    }


def positional_score(board, r: int, c: int, total_stones: int, tactical: bool) -> float:
    score = 0.0

    edge_d = min(r, c, N - 1 - r, N - 1 - c)

    if total_stones < 80:
        if edge_d == 0:
            score -= 32
        elif edge_d == 1:
            score -= 12
        elif edge_d == 2:
            score += 8
        elif edge_d == 3:
            score += 13
        elif edge_d == 4:
            score += 7
        else:
            score += 2
    else:
        if edge_d == 0:
            score -= 8
        elif edge_d == 1:
            score += 1
        elif edge_d == 2:
            score += 5
        elif edge_d == 3:
            score += 5
        else:
            score += 3

    # Hoshi / star-point preference.
    star = {3, 9, 15}
    if r in star and c in star:
        if (r in (3, 15)) and (c in (3, 15)):
            score += 22 if total_stones < 70 else 5
        elif r == 9 and c == 9:
            score += 8 if 8 <= total_stones < 90 else 1
        else:
            score += 11 if total_stones < 90 else 3

    # Strong corner opening logic.
    if total_stones < 70:
        corner_bonus = corner_opening_bonus(board, r, c, total_stones)
        score += corner_bonus

    # Avoid drifting into the center too early unless there is a fight.
    if total_stones < 35 and edge_d >= 6 and not tactical:
        score -= 9

    # In the middle game, central influence is more acceptable.
    if 60 <= total_stones <= 180 and 5 <= r <= 13 and 5 <= c <= 13:
        score += 4

    return score


def corner_opening_bonus(board, r: int, c: int, total_stones: int) -> float:
    score = 0.0
    corners = [
        (0, 0, 1, 1),
        (0, N - 1, 1, -1),
        (N - 1, 0, -1, 1),
        (N - 1, N - 1, -1, -1),
    ]

    for cr, cc, sr, sc in corners:
        # Coordinates measured from this corner, 0-based.
        dr = (r - cr) * sr
        dc = (c - cc) * sc
        if not (0 <= dr <= 8 and 0 <= dc <= 8):
            continue

        own = 0
        opp = 0
        for a in range(0, 7):
            for b in range(0, 7):
                rr = cr + sr * a
                cc2 = cc + sc * b
                if in_bounds(rr, cc2):
                    if board[rr][cc2] == 1:
                        own += 1
                    elif board[rr][cc2] == -1:
                        opp += 1

        # Good corner points: 4-4, 3-4, 4-3, 3-3, 5-4, 4-5.
        good = False
        premium = False
        if dr == 3 and dc == 3:
            good = True
            premium = True
        elif (dr, dc) in ((2, 3), (3, 2), (2, 2), (4, 3), (3, 4)):
            good = True

        if good:
            if own == 0 and opp == 0:
                score += 68 if premium else 48
            elif own == 0 and opp > 0:
                # Approach or invade occupied opponent corner.
                if 2 <= dr <= 5 and 2 <= dc <= 5:
                    score += 18
            elif own > 0 and opp == 0:
                # Avoid overconcentrating in our already claimed corner early.
                score -= 18 if total_stones < 35 else 6

    return score
