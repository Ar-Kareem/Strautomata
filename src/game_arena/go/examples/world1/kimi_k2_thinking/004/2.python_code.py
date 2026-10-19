
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # -----------------------------------------------------------------
    # 1. board representation (0 = empty, 1 = my stones, 2 = opponent)
    # -----------------------------------------------------------------
    board = [[0] * 19 for _ in range(19)]
    for r, c in me:
        board[r - 1][c - 1] = 1
    for r, c in opponent:
        board[r - 1][c - 1] = 2

    # neighbours generator
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def neighbours(r, c):
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                yield nr, nc

    # -----------------------------------------------------------------
    # 2. compute groups and liberties for a given colour
    # -----------------------------------------------------------------
    def compute_groups(colour):
        groups = []                     # list of (set_of_points, set_of_liberties)
        visited = set()
        for i in range(19):
            for j in range(19):
                if board[i][j] == colour and (i, j) not in visited:
                    group = set()
                    queue = [(i, j)]
                    visited.add((i, j))
                    liberties = set()
                    while queue:
                        cr, cc = queue.pop()
                        group.add((cr, cc))
                        for nr, nc in neighbours(cr, cc):
                            if board[nr][nc] == 0:
                                liberties.add((nr, nc))
                            elif board[nr][nc] == colour and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                queue.append((nr, nc))
                    groups.append((group, liberties))
        return groups

    my_groups = compute_groups(1)
    opp_groups = compute_groups(2)

    # -----------------------------------------------------------------
    # 3. tactical points: captures and defences
    # -----------------------------------------------------------------
    capture_points = set()   # empty points that would capture opponent groups
    defence_points = set()   # empty points that would save my own groups in atari

    for group, libs in opp_groups:
        if len(libs) == 1:
            capture_points.update(libs)

    for group, libs in my_groups:
        if len(libs) == 1:
            defence_points.update(libs)

    # -----------------------------------------------------------------
    # 4. evaluate every empty intersection
    # -----------------------------------------------------------------
    best_move = None
    best_score = -1.0

    for r in range(19):
        for c in range(19):
            if board[r][c] != 0:
                continue

            # fast tactical checks
            is_capture = (r, c) in capture_points
            is_defence = (r, c) in defence_points

            # which opponent groups would be captured by playing (r,c)?
            captured_groups = []
            for group, libs in opp_groups:
                if (r, c) in libs and len(libs) == 1:
                    captured_groups.append(group)

            # -----------------------------------------------------------------
            # 5. legality (avoid suicide)
            # -----------------------------------------------------------------
            # set of stones that disappear after the capture
            removed = set()
            for group in captured_groups:
                removed.update(group)

            # DFS that explores the connected component of the newly placed stone.
            # liberties of that component after the capture are stored in group_libs.
            visited = set()
            group_libs = set()
            stack = [(r, c)]
            visited.add((r, c))
            while stack:
                cr, cc = stack.pop()
                for nr, nc in neighbours(cr, cc):
                    if (nr, nc) in removed:
                        continue
                    val = board[nr][nc] if (nr, nc) not in removed else 0
                    if val == 0:
                        group_libs.add((nr, nc))
                    elif val == 1 and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        stack.append((nr, nc))

            # move is illegal if the new group has no liberties and nothing was captured
            if not group_libs and not captured_groups:
                continue

            # -----------------------------------------------------------------
            # 6. scoring
            # -----------------------------------------------------------------
            score = 0.0
            if captured_groups:
                num_captured = sum(len(g) for g in captured_groups)
                score += 100 + num_captured
            else:
                if is_defence:
                    score += 50
                # small random jitter to break ties
                score += random.random() * 1e-3

            # prefer central points
            centre = (9, 9)
            dist = abs(r - centre[0]) + abs(c - centre[1])
            score += max(0, 10 - dist // 2)   # bonus up to 10

            if score > best_score:
                best_score = score
                best_move = (r + 1, c + 1)

    # -----------------------------------------------------------------
    # 7. pass if no legal move was found
    # -----------------------------------------------------------------
    if best_move is None:
        return (0, 0)
    return best_move
