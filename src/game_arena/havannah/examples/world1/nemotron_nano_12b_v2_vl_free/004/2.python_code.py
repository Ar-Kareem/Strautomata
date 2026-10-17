
def is_adjacent(a, b):
    dr = abs(a[0] - b[0])
    dc = abs(a[1] - b[1])
    return (dr <= 1 and dc <= 1) and (dr != 0 or dc != 0)

def policy(me, opp, valid_mask):
    valid_cells = [(r, c) for r in range(15) for c in range(15) if valid_mask[r][c]]

    # Step 1: Check for immediate ring-forming moves
    for cell in valid_cells:
        r, c = cell
        neighbors = [
            (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1),
            (r - 1, c + 1), (r + 1, c - 1)
        ]

        my_neighbors = [n for n in neighbors if n in me]
        if len(my_neighbors) >= 2:
            for i in range(len(my_neighbors)):
                a = my_neighbors[i]
                for j in range(i + 1, len(my_neighbors)):
                    b = my_neighbors[j]
                    if is_adjacent(a, b):
                        return (r, c)

    # Step 2: Block opponent's possible ring moves
    for cell in valid_cells:
        r, c = cell
        if (r, c) in me:
            continue
        handled_me = me + [(r, c)]
        me_set = set(handled_me)
        opponent_can_win = False

        # Simulate placing the AI's stone and check if opponent can win
        for opp_cell in valid_cells:
            if opp_cell in me_set or opp_cell == cell:
                continue
            opp_neighbors = [
                (opp_cell[0] - 1, opp_cell[1]), (opp_cell[0] + 1, opp_cell[1]),
                (opp_cell[0], opp_cell[1] - 1), (opp_cell[0], opp_cell[1] + 1),
                (opp_cell[0] - 1, opp_cell[1] + 1), (opp_cell[0] + 1, opp_cell[1] - 1)
            ]
            opp_my_neighbors = [n for n in opp_neighbors if n in opp]
            for k in range(len(opp_my_neighbors)):
                for l in range(k + 1, len(opp_my_neighbors)):
                    a = opp_my_neighbors[k]
                    b = opp_my_neighbors[l]
                    if is_adjacent(a, b):
                        opponent_can_win = True
                        break
                if opponent_can_win:
                    break
            if opponent_can_win:
                break
        if opponent_can_win:
            return (r, c)

    # Step 3: Greedy heuristic: choose cell with the most adjacent me cells
    best_cell = None
    best_score = -1

    for r in range(15):
        for c in range(15):
            if not valid_mask[r][c]:
                continue

            num_me_neighbors = 0
            for dr, dc in [
                (-1, 0), (1, 0), (0, -1), (0, 1),
                (-1, 1), (1, -1)
            ]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in me:
                    num_me_neighbors += 1

            if num_me_neighbors > best_score:
                best_score = num_me_neighbors
                best_cell = (r, c)

    if best_cell:
        return best_cell

    # Fallback: return first valid move
    return valid_cells[0] if valid_cells else None
