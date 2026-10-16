
def policy(board: list[list[int]]) -> tuple[int, int]:
    remaining = [5, 4, 3, 3, 2]
    sunk = set()

    # detect sunk ships horizontally
    for r in range(10):
        c = 0
        while c < 10:
            if board[r][c] == 1:
                start = c
                while c < 10 and board[r][c] == 1:
                    c += 1
                length = c - start
                if length in remaining:
                    max_rem = max(remaining) if remaining else 0
                    left_closed = (start == 0) or (board[r][start - 1] != 0)
                    right_closed = (c == 10) or (board[r][c] != 0)
                    if length == max_rem or (left_closed and right_closed):
                        remaining.remove(length)
                        for cc in range(start, c):
                            sunk.add((r, cc))
            else:
                c += 1

    # detect sunk ships vertically
    for c in range(10):
        r = 0
        while r < 10:
            if board[r][c] == 1:
                start = r
                while r < 10 and board[r][c] == 1:
                    r += 1
                length = r - start
                if length in remaining:
                    max_rem = max(remaining) if remaining else 0
                    top_closed = (start == 0) or (board[start - 1][c] != 0)
                    bottom_closed = (r == 10) or (board[r][c] != 0)
                    if length == max_rem or (top_closed and bottom_closed):
                        remaining.remove(length)
                        for rr in range(start, r):
                            sunk.add((rr, c))
            else:
                r += 1

    # collect active (unsunk) hits
    active = set()
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1 and (r, c) not in sunk:
                active.add((r, c))

    candidates = set()
    if active:
        visited = set()
        isolated = []
        target_lines = []

        for (r, c) in active:
            if (r, c) in visited:
                continue

            # check horizontal line
            hor_cells = []
            cc = c
            while cc >= 0 and board[r][cc] == 1 and (r, cc) in active:
                hor_cells.append((r, cc))
                cc -= 1
            cc = c + 1
            while cc < 10 and board[r][cc] == 1 and (r, cc) in active:
                hor_cells.append((r, cc))
                cc += 1
            if len(hor_cells) >= 2:
                target_lines.append(('h', hor_cells))
                for cell in hor_cells:
                    visited.add(cell)
                continue

            # check vertical line
            ver_cells = []
            rr = r
            while rr >= 0 and board[rr][c] == 1 and (rr, c) in active:
                ver_cells.append((rr, c))
                rr -= 1
            rr = r + 1
            while rr < 10 and board[rr][c] == 1 and (rr, c) in active:
                ver_cells.append((rr, c))
                rr += 1
            if len(ver_cells) >= 2:
                target_lines.append(('v', ver_cells))
                for cell in ver_cells:
                    visited.add(cell)
                continue

            isolated.append((r, c))
            visited.add((r, c))

        # collect candidate cells from target lines
        for orient, cells in target_lines:
            if orient == 'h':
                row = cells[0][0]
                cols = sorted([cc for _, cc in cells])
                left = cols[0] - 1
                if left >= 0 and board[row][left] == 0:
                    candidates.add((row, left))
                right = cols[-1] + 1
                if right < 10 and board[row][right] == 0:
                    candidates.add((row, right))
            else:  # 'v'
                col = cells[0][1]
                rows = sorted([rr for rr, _ in cells])
                top = rows[0] - 1
                if top >= 0 and board[top][col] == 0:
                    candidates.add((top, col))
                bottom = rows[-1] + 1
                if bottom < 10 and board[bottom][col] == 0:
                    candidates.add((bottom, col))

        # collect candidate cells from isolated hits
        for (r, c) in isolated:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    candidates.add((nr, nc))

        if not candidates:
            active = set()  # fallback to hunt mode

    if not active:
        # hunt mode with parity: only even parity cells
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0 and (r + c) % 2 == 0:
                    candidates.add((r, c))
        if not candidates:
            # fallback to any unknown cell
            for r in range(10):
                for c in range(10):
                    if board[r][c] == 0:
                        candidates.add((r, c))

    # build blocked set (misses and sunk ships)
    blocked = set()
    for r in range(10):
        for c in range(10):
            if board[r][c] == -1 or (r, c) in sunk:
                blocked.add((r, c))

    # heatmap: count valid placements of remaining ships
    heatmap = [[0] * 10 for _ in range(10)]
    for L in remaining:
        # horizontal placements
        for r in range(10):
            for c in range(10 - L + 1):
                valid = True
                for i in range(L):
                    if (r, c + i) in blocked:
                        valid = False
                        break
                if valid:
                    for i in range(L):
                        heatmap[r][c + i] += 1
        # vertical placements
        for c in range(10):
            for r in range(10 - L + 1):
                valid = True
                for i in range(L):
                    if (r + i, c) in blocked:
                        valid = False
                        break
                if valid:
                    for i in range(L):
                        heatmap[r + i][c] += 1

    # select the best candidate
    best_cell = None
    best_val = -1
    for cell in sorted(candidates):
        r, c = cell
        if heatmap[r][c] > best_val:
            best_val = heatmap[r][c]
            best_cell = (r, c)

    return best_cell
