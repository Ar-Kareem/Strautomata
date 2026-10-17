
def get_remaining_ships(board: list[list[int]]) -> list[int]:
    """Deduces remaining ships from confirmed fully sunk clusters."""
    fleet = [5, 4, 3, 3, 2]
    visited = set()
    components = []
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1 and (r, c) not in visited:
                comp = []
                q = [(r, c)]
                visited.add((r, c))
                while q:
                    curr_r, curr_c = q.pop()
                    comp.append((curr_r, curr_c))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < 10 and 0 <= nc < 10:
                            if board[nr][nc] == 1 and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                q.append((nr, nc))
                components.append(comp)

    for comp in components:
        # A component is closed if none of its cells have an unknown neighbor
        is_closed = True
        for r, c in comp:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10:
                    if board[nr][nc] == 0:
                        is_closed = False
                        break
            if not is_closed:
                break
        
        if is_closed:
            rows = [r for r, c in comp]
            cols = [c for r, c in comp]
            is_horizontal = (len(set(rows)) == 1) and (max(cols) - min(cols) + 1 == len(comp))
            is_vertical = (len(set(cols)) == 1) and (max(rows) - min(rows) + 1 == len(comp))
            if is_horizontal or is_vertical:
                length = len(comp)
                if length in fleet:
                    fleet.remove(length)

    return fleet if fleet else [2]


def policy(board: list[list[int]]) -> tuple[int, int]:
    # Available unknown cells to fire at
    unknowns = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]
    if not unknowns:
        return (0, 0)

    remaining_ships = get_remaining_ships(board)

    # Identify hits that still have at least one adjacent unknown cell
    active_hits = set()
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                        active_hits.add((r, c))
                        break

    score = [[0.0 for _ in range(10)] for _ in range(10)]

    if active_hits:
        # TARGET MODE: Weight placements that cover unresolved hits
        for L in remaining_ships:
            # Horizontal placements
            for r in range(10):
                for c in range(10 - L + 1):
                    placement = [(r, c + i) for i in range(L)]
                    if any(board[pr][pc] == -1 for pr, pc in placement):
                        continue
                    
                    hits = [p for p in placement if board[p[0]][p[1]] == 1]
                    zeros = [p for p in placement if board[p[0]][p[1]] == 0]
                    
                    if not hits or not zeros:
                        continue
                    if not any(h in active_hits for h in hits):
                        continue

                    h_count = len(hits)
                    weight = 100.0 ** h_count

                    # Only assign weight to unknown cells directly adjacent to hits or in gaps
                    for idx, (pr, pc) in enumerate(placement):
                        if board[pr][pc] == 0:
                            left_hit = (idx > 0 and board[placement[idx - 1][0]][placement[idx - 1][1]] == 1)
                            right_hit = (idx < L - 1 and board[placement[idx + 1][0]][placement[idx + 1][1]] == 1)
                            if left_hit or right_hit:
                                mult = 2.0 if (left_hit and right_hit) else 1.0
                                score[pr][pc] += weight * mult

            # Vertical placements
            for c in range(10):
                for r in range(10 - L + 1):
                    placement = [(r + i, c) for i in range(L)]
                    if any(board[pr][pc] == -1 for pr, pc in placement):
                        continue
                    
                    hits = [p for p in placement if board[p[0]][p[1]] == 1]
                    zeros = [p for p in placement if board[p[0]][p[1]] == 0]
                    
                    if not hits or not zeros:
                        continue
                    if not any(h in active_hits for h in hits):
                        continue

                    h_count = len(hits)
                    weight = 100.0 ** h_count

                    for idx, (pr, pc) in enumerate(placement):
                        if board[pr][pc] == 0:
                            up_hit = (idx > 0 and board[placement[idx - 1][0]][placement[idx - 1][1]] == 1)
                            down_hit = (idx < L - 1 and board[placement[idx + 1][0]][placement[idx + 1][1]] == 1)
                            if up_hit or down_hit:
                                mult = 2.0 if (up_hit and down_hit) else 1.0
                                score[pr][pc] += weight * mult

    # If not in target mode or if target mode yielded no valid placements, use HUNT MODE
    if max(score[r][c] for r, c in unknowns) == 0.0:
        hunt_score = [[0.0 for _ in range(10)] for _ in range(10)]
        for L in remaining_ships:
            # Horizontal placements of 0s
            for r in range(10):
                for c in range(10 - L + 1):
                    if all(board[r][c + i] == 0 for i in range(L)):
                        for i in range(L):
                            hunt_score[r][c + i] += 1.0

            # Vertical placements of 0s
            for c in range(10):
                for r in range(10 - L + 1):
                    if all(board[r + i][c] == 0 for i in range(L)):
                        for i in range(L):
                            hunt_score[r + i][c] += 1.0

        min_len = min(remaining_ships)
        stride = max(2, min_len)

        # Select the parity offset that aligns best with already fired shots
        shots_per_offset = [0] * stride
        for r in range(10):
            for c in range(10):
                if board[r][c] != 0:
                    shots_per_offset[(r + c) % stride] += 1
        best_offset = max(range(stride), key=lambda off: shots_per_offset[off])

        for r, c in unknowns:
            center_bonus = 0.05 * (4.5 - abs(r - 4.5) + 4.5 - abs(c - 4.5))
            if (r + c) % stride == best_offset:
                score[r][c] = hunt_score[r][c] * 1000.0 + center_bonus
            else:
                score[r][c] = hunt_score[r][c] + center_bonus

    return max(unknowns, key=lambda cell: score[cell[0]][cell[1]])
