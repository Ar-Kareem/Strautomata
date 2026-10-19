
def policy(me, opponent):
    N = 19
    board = {}
    for r, c in me:
        board[(r, c)] = 1
    for r, c in opponent:
        board[(r, c)] = 2

    def neighbors(r, c):
        out = []
        if r > 1: out.append((r-1, c))
        if r < N: out.append((r+1, c))
        if c > 1: out.append((r, c-1))
        if c < N: out.append((r, c+1))
        return out

    def get_group(r, c, b):
        color = b.get((r, c))
        if color is None:
            return set(), set()
        stones = set()
        libs = set()
        stack = [(r, c)]
        while stack:
            p = stack.pop()
            if p in stones:
                continue
            stones.add(p)
            for n in neighbors(*p):
                v = b.get(n)
                if v is None:
                    libs.add(n)
                elif v == color and n not in stones:
                    stack.append(n)
        return stones, libs

    def try_move(r, c, b, color):
        if (r, c) in b:
            return None
        nb = dict(b)
        nb[(r, c)] = color
        opp = 3 - color
        captured = set()
        seen = set()
        for n in neighbors(r, c):
            if nb.get(n) == opp and n not in seen:
                stones, libs = get_group(*n, nb)
                seen.update(stones)
                if not libs:
                    captured.update(stones)
        for s in captured:
            del nb[s]
        stones, libs = get_group(r, c, nb)
        if not libs:
            return None
        return nb, len(captured)

    # Opening: play star points
    star_points = [(16,16),(4,4),(16,4),(4,16),(10,10),
                   (10,4),(10,16),(4,10),(16,10),
                   (16,14),(16,6),(4,14),(4,6),
                   (14,16),(6,16),(14,4),(6,4)]
    if len(me) + len(opponent) < 10:
        for p in star_points:
            if p not in board:
                res = try_move(*p, board, 1)
                if res is not None:
                    return p

    # Candidate moves: near existing stones
    candidates = set()
    for r, c in list(board.keys()):
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r+dr, c+dc
                if 1 <= nr <= N and 1 <= nc <= N and (nr, nc) not in board:
                    candidates.add((nr, nc))

    if not candidates:
        return (10, 10)

    # Precompute my groups in atari and opponent weak groups
    my_groups = []
    opp_groups = []
    visited = set()
    for pos, col in board.items():
        if pos in visited:
            continue
        stones, libs = get_group(*pos, board)
        visited.update(stones)
        if col == 1:
            my_groups.append((stones, libs))
        else:
            opp_groups.append((stones, libs))

    best_score = -10**9
    best_move = None

    for move in candidates:
        res = try_move(*move, board, 1)
        if res is None:
            continue
        nb, captures = res
        score = 0
        score += captures * 120

        # Save groups in atari
        for stones, libs in my_groups:
            if len(libs) == 1 and move in libs:
                # Check if this move actually saves them
                # After move, re-check liberties of merged group
                merged, mlibs = get_group(*move, nb)
                if len(mlibs) >= 2:
                    score += len(stones) * 40
                else:
                    score -= len(stones) * 10  # doesn't save

        # Attack opponent: reduce liberties
        attack_seen = set()
        for n in neighbors(*move):
            if nb.get(n) == 2 and n not in attack_seen:
                s, l = get_group(*n, nb)
                attack_seen.update(s)
                if len(l) == 1:
                    score += len(s) * 25
                elif len(l) == 2:
                    score += len(s) * 6
                elif len(l) == 3:
                    score += len(s) * 2

        # Own group liberties after move
        my_stones, my_libs = get_group(*move, nb)
        if len(my_libs) == 1:
            score -= len(my_stones) * 30  # self-atari bad
        else:
            score += min(len(my_libs), 6)

        # Connection bonus
        own_n = sum(1 for n in neighbors(*move) if board.get(n) == 1)
        opp_n = sum(1 for n in neighbors(*move) if board.get(n) == 2)
        score += own_n * 2
        score += opp_n  # contact can be good

        # Avoid first line without reason
        r, c = move
        edge_dist = min(r-1, N-r, c-1, N-c)
        if edge_dist == 0:
            score -= 8
        elif edge_dist == 1:
            score -= 2

        # Don't fill own eyes
        if all(board.get(n) == 1 for n in neighbors(*move)):
            # check diagonals
            diag = [(r-1,c-1),(r-1,c+1),(r+1,c-1),(r+1,c+1)]
            diag = [d for d in diag if 1 <= d[0] <= N and 1 <= d[1] <= N]
            enemy_diag = sum(1 for d in diag if board.get(d) == 2)
            if enemy_diag == 0 or (len(diag) == 4 and enemy_diag <= 1):
                score -= 200

        # Small preference for center-ish
        score += (9 - abs(r-10) - abs(c-10)) * 0.05

        if score > best_score:
            best_score = score
            best_move = move

    if best_move is None:
        # find any legal move
        for r in range(1, N+1):
            for c in range(1, N+1):
                if (r, c) not in board:
                    res = try_move(r, c, board, 1)
                    if res is not None:
                        return (r, c)
        return (0, 0)

    return best_move
