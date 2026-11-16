
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Smart heuristic policy for 4x4 Dots and Boxes (5x5 arrays provided).

    Returns a legal move string "row,col,dir" where dir is 'H' or 'V'.
    """
    # Board constants
    BOX_ROWS = 4
    BOX_COLS = 4
    SIZE = 5  # arrays are 5x5

    # Convert to boolean drawn arrays
    drawn_h = (horizontal != 0)
    drawn_v = (vertical != 0)
    # Ensure shapes exist
    drawn_h = np.array(drawn_h, copy=True)
    drawn_v = np.array(drawn_v, copy=True)
    capture = np.array(capture, copy=True)

    # Helper: count sides for a given box (i,j)
    def box_sides_count(i, j, h_drawn, v_drawn):
        # top: horizontal[i, j]
        # bottom: horizontal[i+1, j]
        # left: vertical[i, j]
        # right: vertical[i, j+1]
        count = 0
        if h_drawn[i, j]:
            count += 1
        if h_drawn[i+1, j]:
            count += 1
        if v_drawn[i, j]:
            count += 1
        if v_drawn[i, j+1]:
            count += 1
        return count

    # Helper: get boxes touched by a move and their indices
    def touched_boxes_for_move(r, c, dirc):
        touched = []
        if dirc == 'H':
            # top box at (r-1, c)
            if 0 <= r-1 < BOX_ROWS and 0 <= c < BOX_COLS:
                touched.append((r-1, c))
            # bottom box at (r, c)
            if 0 <= r < BOX_ROWS and 0 <= c < BOX_COLS:
                touched.append((r, c))
        else:  # 'V'
            # left box at (r, c-1)
            if 0 <= r < BOX_ROWS and 0 <= c-1 < BOX_COLS:
                touched.append((r, c-1))
            # right box at (r, c)
            if 0 <= r < BOX_ROWS and 0 <= c < BOX_COLS:
                touched.append((r, c))
        return touched

    # Gather all legal moves and evaluate them
    candidates = []

    # iterate horizontal edges
    for r in range(SIZE):
        for c in range(SIZE):
            if not drawn_h[r, c]:
                # legal horizontal move
                touched = touched_boxes_for_move(r, c, 'H')
                # compute before counts
                before = []
                for (i, j) in touched:
                    before.append(box_sides_count(i, j, drawn_h, drawn_v))
                # simulate move
                drawn_h[r, c] = True
                after = []
                for (i, j) in touched:
                    after.append(box_sides_count(i, j, drawn_h, drawn_v))
                # restore
                drawn_h[r, c] = False

                # count captures and created 3-sided boxes, only consider boxes not already claimed
                captures = 0
                created_3 = 0
                for idx, (i, j) in enumerate(touched):
                    if int(capture[i, j]) != 0:
                        continue
                    if before[idx] < 4 and after[idx] == 4:
                        captures += 1
                    elif before[idx] < 3 and after[idx] == 3:
                        created_3 += 1

                candidates.append({
                    'r': r, 'c': c, 'dir': 'H',
                    'captures': captures, 'created_3': created_3,
                    'touches': len(touched)
                })

    # iterate vertical edges
    for r in range(SIZE):
        for c in range(SIZE):
            if not drawn_v[r, c]:
                # legal vertical move
                touched = touched_boxes_for_move(r, c, 'V')
                before = []
                for (i, j) in touched:
                    before.append(box_sides_count(i, j, drawn_h, drawn_v))
                # simulate move
                drawn_v[r, c] = True
                after = []
                for (i, j) in touched:
                    after.append(box_sides_count(i, j, drawn_h, drawn_v))
                # restore
                drawn_v[r, c] = False

                captures = 0
                created_3 = 0
                for idx, (i, j) in enumerate(touched):
                    if int(capture[i, j]) != 0:
                        continue
                    if before[idx] < 4 and after[idx] == 4:
                        captures += 1
                    elif before[idx] < 3 and after[idx] == 3:
                        created_3 += 1

                candidates.append({
                    'r': r, 'c': c, 'dir': 'V',
                    'captures': captures, 'created_3': created_3,
                    'touches': len(touched)
                })

    # Must have at least one legal move. If none (shouldn't happen), fallback to first zero entry.
    if not candidates:
        # fallback search
        for r in range(SIZE):
            for c in range(SIZE):
                if not drawn_h[r, c]:
                    return f"{r},{c},H"
                if not drawn_v[r, c]:
                    return f"{r},{c},V"
        # if absolutely none, return arbitrary
        return "0,0,H"

    # Strategy selection:
    # 1) Prefer capturing moves: maximize captures, minimize created_3, then minimize touches, then stable tie-break by (r,c,dir)
    capturing = [m for m in candidates if m['captures'] > 0]
    if capturing:
        # sort by (-captures, created_3, touches, r, c, dir)
        capturing.sort(key=lambda m: (-m['captures'], m['created_3'], m['touches'], m['r'], m['c'], m['dir']))
        best = capturing[0]
        return f"{best['r']},{best['c']},{best['dir']}"

    # 2) No captures: choose moves that create zero 3-sided boxes if possible
    safe = [m for m in candidates if m['created_3'] == 0]
    if safe:
        # prefer fewer touches (edges touching 1 box are safer than touching 2)
        safe.sort(key=lambda m: (m['touches'], m['r'], m['c'], m['dir']))
        best = safe[0]
        return f"{best['r']},{best['c']},{best['dir']}"

    # 3) Otherwise minimize created_3, then touches
    candidates.sort(key=lambda m: (m['created_3'], m['touches'], m['r'], m['c'], m['dir']))
    best = candidates[0]
    return f"{best['r']},{best['c']},{best['dir']}"
