
from typing import List, Tuple

BOARD_SIZE = 19
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    N = BOARD_SIZE

    # board: 0 empty, 1 me, 2 opponent
    board = [[0] * N for _ in range(N)]
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N and board[r - 1][c - 1] == 0:
            board[r - 1][c - 1] = 2

    def on_board(r, c):
        return 0 <= r < N and 0 <= c < N

    def neighbors(r, c):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if on_board(nr, nc):
                yield nr, nc

    def group_and_liberties(bd, r, c):
        color = bd[r][c]
        group = {(r, c)}
        libs = set()
        stack = [(r, c)]
        while stack:
            x, y = stack.pop()
            for nx, ny in neighbors(x, y):
                v = bd[nx][ny]
                if v == 0:
                    libs.add((nx, ny))
                elif v == color and (nx, ny) not in group:
                    group.add((nx, ny))
                    stack.append((nx, ny))
        return group, libs

    def simulate_move(bd, move_r, move_c, color):
        # returns (legal, new_board, captured_count)
        if bd[move_r][move_c] != 0:
            return False, bd, 0

        opp = 3 - color
        new_bd = [row[:] for row in bd]
        new_bd[move_r][move_c] = color
        captured = 0

        # capture adjacent opponent groups with no liberties
        checked = set()
        for nr, nc in neighbors(move_r, move_c):
            if new_bd[nr][nc] == opp and (nr, nc) not in checked:
                grp, libs = group_and_liberties(new_bd, nr, nc)
                checked |= grp
                if not libs:
                    captured += len(grp)
                    for x, y in grp:
                        new_bd[x][y] = 0

        # suicide check
        grp, libs = group_and_liberties(new_bd, move_r, move_c)
        if not libs:
            return False, bd, 0

        return True, new_bd, captured

    def liberty_count_of_group(bd, r, c):
        _, libs = group_and_liberties(bd, r, c)
        return len(libs)

    def is_legal(r, c):
        legal, _, _ = simulate_move(board, r, c, 1)
        return legal

    def emergency_moves():
        moves = []

        # Save own groups in atari
        seen = set()
        for r, c in me:
            r0, c0 = r - 1, c - 1
            if not on_board(r0, c0) or board[r0][c0] != 1 or (r0, c0) in seen:
                continue
            grp, libs = group_and_liberties(board, r0, c0)
            seen |= grp
            if len(libs) == 1:
                lib = next(iter(libs))
                legal, new_bd, cap = simulate_move(board, lib[0], lib[1], 1)
                if legal:
                    score = 100000 + len(grp) * 200 + cap * 500
                    moves.append((score, (lib[0] + 1, lib[1] + 1)))

        # Capture opponent groups in atari
        seen = set()
        for r, c in opponent:
            r0, c0 = r - 1, c - 1
            if not on_board(r0, c0) or board[r0][c0] != 2 or (r0, c0) in seen:
                continue
            grp, libs = group_and_liberties(board, r0, c0)
            seen |= grp
            if len(libs) == 1:
                lib = next(iter(libs))
                legal, new_bd, cap = simulate_move(board, lib[0], lib[1], 1)
                if legal:
                    score = 120000 + len(grp) * 300 + cap * 1000
                    moves.append((score, (lib[0] + 1, lib[1] + 1)))

        if moves:
            moves.sort(reverse=True)
            return moves[0][1]
        return None

    # First handle urgent tactical moves
    em = emergency_moves()
    if em is not None:
        return em

    occupied = set(me) | set(opponent)

    # Candidate generation: empties near existing stones; opening center if board is empty
    if not occupied:
        return (10, 10)

    candidates = set()
    for r, c in occupied:
        r0, c0 = r - 1, c - 1
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r0 + dr, c0 + dc
                if on_board(nr, nc) and board[nr][nc] == 0:
                    candidates.add((nr, nc))

    # Fallback: if candidate set somehow empty, consider all empties
    if not candidates:
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    candidates.add((r, c))

    total_stones = len(me) + len(opponent)

    def score_move(r, c):
        legal, new_bd, captured = simulate_move(board, r, c, 1)
        if not legal:
            return -10**18

        score = 0.0

        # Strong tactical reward
        score += captured * 5000

        # Local adjacency features
        friendly_adj = 0
        opp_adj = 0
        empty_adj = 0
        for nr, nc in neighbors(r, c):
            if board[nr][nc] == 1:
                friendly_adj += 1
            elif board[nr][nc] == 2:
                opp_adj += 1
            else:
                empty_adj += 1

        score += friendly_adj * 180
        score += opp_adj * 120

        # Prefer connecting weak friendly groups / attacking weak enemy groups
        seen_friend = set()
        for nr, nc in neighbors(r, c):
            if board[nr][nc] == 1 and (nr, nc) not in seen_friend:
                grp, libs = group_and_liberties(board, nr, nc)
                seen_friend |= grp
                l = len(libs)
                if l == 1:
                    score += 2500
                elif l == 2:
                    score += 700
                else:
                    score += 100

        seen_enemy = set()
        for nr, nc in neighbors(r, c):
            if board[nr][nc] == 2 and (nr, nc) not in seen_enemy:
                grp, libs = group_and_liberties(board, nr, nc)
                seen_enemy |= grp
                l = len(libs)
                if l == 1:
                    score += 4000
                elif l == 2:
                    score += 1000
                else:
                    score += 150

        # Post-move group liberties
        _, libs_after = group_and_liberties(new_bd, r, c)
        libn = len(libs_after)
        score += libn * 140
        if libn == 1:
            score -= 2500
        elif libn == 2:
            score -= 400

        # Shape: avoid isolated plays unless opening
        if friendly_adj == 0 and opp_adj == 0:
            score -= 1200

        # Mild centrality preference, stronger in opening
        center = 9
        dist = abs(r - center) + abs(c - center)
        if total_stones < 20:
            score += (18 - dist) * 35
        else:
            score += (18 - dist) * 8

        # Prefer star-ish points in opening if reasonable
        if total_stones < 10:
            if (r + 1, c + 1) in {(4, 4), (4, 10), (4, 16), (10, 4), (10, 10), (10, 16), (16, 4), (16, 10), (16, 16)}:
                score += 120

        # Small edge penalty early
        if total_stones < 30:
            if r in (0, 18) or c in (0, 18):
                score -= 120
            elif r in (1, 17) or c in (1, 17):
                score -= 40

        # Encourage moves near the action
        local_density = 0
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if on_board(nr, nc) and board[nr][nc] != 0:
                    local_density += 1
        score += local_density * 18

        # Tiny deterministic tie-break
        score += (r * 19 + c) * 1e-6

        return score

    best_move = None
    best_score = -10**18

    for r, c in candidates:
        s = score_move(r, c)
        if s > best_score:
            best_score = s
            best_move = (r + 1, c + 1)

    if best_move is not None:
        return best_move

    # Full legal fallback scan
    for r in range(N):
        for c in range(N):
            if is_legal(r, c):
                return (r + 1, c + 1)

    return (0, 0)
