
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Dots and Boxes (4x4 boxes). Player to move is assumed to draw edges as +1.
    horizontal, vertical, capture are 5x5 arrays with values in {-1,0,1}.
    Return a legal move string: 'row,col,dir' where dir is 'H' or 'V'.
    """
    # Ensure numpy arrays
    horizontal = np.asarray(horizontal)
    vertical = np.asarray(vertical)
    capture = np.asarray(capture)

    n_boxes = 4  # 4x4 boxes
    # Helpers
    def box_edges_filled(r, c):
        """Return filled flags for box at (r,c): (top, bottom, left, right)"""
        # top: horizontal[r, c]
        # bottom: horizontal[r+1, c]
        # left: vertical[r, c]
        # right: vertical[r, c+1]
        top = horizontal[r, c] != 0
        bot = horizontal[r+1, c] != 0
        left = vertical[r, c] != 0
        right = vertical[r, c+1] != 0
        return top, bot, left, right

    def count_filled(r, c):
        t, b, l, rr = box_edges_filled(r, c)
        return int(t) + int(b) + int(l) + int(rr)

    def boxes_completed_by_move(move):
        """
        Compute how many boxes would be completed by applying a single move,
        assuming it is drawn by us (set to +1).
        """
        row, col, d = move
        completed = []
        if d == 'H':
            # horizontal edge at (row,col) touches up to two boxes:
            # top box: (row-1,col) if row>0
            # bottom box: (row,col) if row<4
            if row > 0:
                r, c = row-1, col
                if 0 <= r < n_boxes and 0 <= c < n_boxes:
                    # check if box has 3 other edges filled and this edge is the missing one
                    # If this horizontal edge is currently empty, then in current state it's missing.
                    # Completion occurs when the other three are filled.
                    # Since the edge is currently empty, count filled excluding this edge equals 3.
                    # Equivalent: count_filled after hypothetically drawing it == 4.
                    # We can compute by current count_filled and whether this specific edge contributes.
                    t, b, l, rr = box_edges_filled(r, c)
                    # For this box, this edge is either top (if row-1==box top) or bottom.
                    # Our move is horizontal at (row,col).
                    # For box (r,c), the top edge is horizontal[r,c] = horizontal[row-1,col], not our move.
                    # The bottom edge is horizontal[r+1,c] = horizontal[row,col] which is our move.
                    # Thus our move corresponds to bottom edge.
                    # So other edges: top, left, right must be filled.
                    other = int(t) + int(l) + int(rr)
                    if other == 3:
                        # Ensure not already completed by capture; doesn't matter for legality,
                        # but for scoring it would only count if unclaimed.
                        completed.append((r, c))
            if row < n_boxes:  # row in 1..3 possible; also row==4 doesn't touch below box
                r, c = row, col
                if 0 <= r < n_boxes and 0 <= c < n_boxes:
                    # This move corresponds to top edge for box (r,c) (horizontal[r,c])
                    t, b, l, rr = box_edges_filled(r, c)
                    # Our move corresponds to top edge: other edges bottom,left,right must be filled.
                    other = int(b) + int(l) + int(rr)
                    if other == 3:
                        completed.append((r, c))
        else:  # 'V'
            # vertical edge at (row,col) touches up to two boxes:
            # left box: (row,col-1) if col>0
            # right box: (row,col) if col<4
            if col > 0:
                r, c = row, col-1
                if 0 <= r < n_boxes and 0 <= c < n_boxes:
                    # move corresponds to right edge for box (r,c): vertical[r,c+1] == vertical[row,col]
                    t, b, l, rr = box_edges_filled(r, c)
                    # other edges: top,bottom,left must be filled
                    other = int(t) + int(b) + int(l)
                    if other == 3:
                        completed.append((r, c))
            if col < n_boxes:
                r, c = row, col
                if 0 <= r < n_boxes and 0 <= c < n_boxes:
                    # move corresponds to left edge for box (r,c)
                    t, b, l, rr = box_edges_filled(r, c)
                    other = int(t) + int(b) + int(rr)
                    if other == 3:
                        completed.append((r, c))
        # Only count unclaimed boxes (capture==0); if already claimed, ignore for scoring.
        # But in normal play, capturing a claimed box shouldn't happen; still safe to check.
        completed_unclaimed = [bc for bc in completed if capture[bc[0], bc[1]] == 0]
        return completed_unclaimed

    def opponent_boxes_available_after(move):
        """
        After we play move (no extra turn assumed here, but the opponent will move if we don't capture),
        estimate how many boxes the opponent could complete immediately (i.e., boxes with exactly 3 edges filled
        and unclaimed) that become available on their next move.
        """
        # Create local filled arrays (0/!=0) for edge occupancy
        h_occ = horizontal != 0
        v_occ = vertical != 0

        row, col, d = move
        if d == 'H':
            h_occ[row, col] = True
        else:
            v_occ[row, col] = True

        # For each unclaimed box, check if it now has exactly 3 edges filled.
        # If it does, opponent can complete it with the missing edge.
        count = 0
        for r in range(n_boxes):
            for c in range(n_boxes):
                if capture[r, c] != 0:
                    continue
                # compute filled edges
                top = h_occ[r, c]
                bot = h_occ[r+1, c]
                left = v_occ[r, c]
                right = v_occ[r, c+1]
                s = int(top) + int(bot) + int(left) + int(right)
                if s == 3:
                    count += 1
        return count

    # Enumerate legal moves
    legal_moves = []
    # horizontal edges: row 0..4, col 0..4
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                legal_moves.append((row, col, 'H'))
    # vertical edges
    for row in range(5):
        for col in range(5):
            if vertical[row, col] == 0:
                # 'V' move at (row,col)
                legal_moves.append((row, col, 'V'))

    # If no moves (shouldn't happen), return a dummy (but game should not call then)
    if not legal_moves:
        return "0,0,H"

    # 1) Take any immediate capture; maximize boxes captured
    best_capture = -1
    best_moves = []
    for m in legal_moves:
        completed = boxes_completed_by_move(m)
        k = len(completed)
        if k > best_capture:
            best_capture = k
            best_moves = [m]
        elif k == best_capture and k > 0:
            best_moves.append(m)

    if best_capture > 0:
        # If multiple capture moves, choose among them by minimal opponent immediate opportunities after move
        # (since capturing gives extra turn, opponent might be irrelevant, but it's still fine for tie-break)
        min_opp = None
        chosen = None
        for m in best_moves:
            opp = opponent_boxes_available_after(m)
            if min_opp is None or opp < min_opp:
                min_opp = opp
                chosen = m
        row, col, d = chosen
        return f"{row},{col},{d}"

    # 2) Otherwise, avoid creating 3-sided boxes for opponent:
    # minimize opponent_boxes_available_after(move)
    # tie-break: minimize number of new 3-sided boxes and then prefer moves that reduce total "threat surface"
    scored = []
    for m in legal_moves:
        opp_threat = opponent_boxes_available_after(m)

        # Secondary heuristic: count how many boxes become 4? (should be 0 here) and how many become 3.
        # We'll use opp_threat itself, and also compute "risk distance" by counting edge incidence into unclaimed boxes with 2 filled.
        # Simple: compute number of adjacent unclaimed boxes that currently have 2 filled and would become 3 after our move.
        row, col, d = m
        risk_add = 0

        h_occ = horizontal != 0
        v_occ = vertical != 0
        if d == 'H':
            h_occ[row, col] = True
        else:
            v_occ[row, col] = True

        # Determine adjacent boxes
        adj = []
        if d == 'H':
            if row > 0:
                adj.append((row-1, col))
            if row < n_boxes:
                adj.append((row, col))
        else:
            if col > 0:
                adj.append((row, col-1))
            if col < n_boxes:
                adj.append((row, col))

        for r, c in adj:
            if 0 <= r < n_boxes and 0 <= c < n_boxes and capture[r, c] == 0:
                top = h_occ[r, c]
                bot = h_occ[r+1, c]
                left = v_occ[r, c]
                right = v_occ[r, c+1]
                s = int(top) + int(bot) + int(left) + int(right)
                if s == 3:
                    risk_add += 1

        # Store: primary opp_threat, secondary risk_add
        scored.append((opp_threat, risk_add, m))

    scored.sort(key=lambda x: (x[0], x[1]))
    chosen = scored[0][2]
    row, col, d = chosen
    return f"{row},{col},{d}"
