
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Board is 4x4 boxes => edges are 5x5 arrays for both orientations.
    # horizontal[r,c] represents horizontal edge between (r,c) and (r,c+1), r in [0..4], c in [0..4]
    # vertical[r,c] represents vertical edge between (r,c) and (r+1,c), r in [0..4], c in [0..4]
    # Boxes are indexed box (br,bc) with br,bc in [0..3].
    #
    # For a given box (br,bc), its four edges are:
    # top:    horizontal[br, bc]
    # bottom: horizontal[br+1, bc]
    # left:   vertical[br, bc]
    # right:  vertical[br, bc+1]
    #
    # capture[br,bc] in {-1,0,1} doesn't affect move legality, only scoring evaluation.

    def is_edge_empty(dir_char, r, c):
        if dir_char == 'H':
            return horizontal[r, c] == 0
        else:
            return vertical[r, c] == 0

    def edge_value_after_move(dir_char, r, c):
        # after we play, the edge is ours => +1
        return 1

    # Check which boxes would be completed by playing edge (dir,r,c).
    def boxes_completed_by_edge(dir_char, r, c):
        completed = []
        if dir_char == 'H':
            # horizontal edge at (r,c) is top of box (r, c) if r in 0..3 and c in 0..3
            # also bottom of box (r-1, c) if r-1 in 0..3
            # Because horizontal indices span 0..4, boxes use br=0..3, bc=0..3.
            if 0 <= r <= 3 and 0 <= c <= 3:
                br, bc = r, c
                top = (horizontal[br, bc] == 0)  # current empty check (not strictly needed)
                # if we play it, top becomes filled.
                # Completed means other three edges already filled.
                other_filled = (
                    horizontal[br+1, bc] != 0 and   # bottom
                    vertical[br, bc] != 0 and       # left
                    vertical[br, bc+1] != 0         # right
                )
                if other_filled:
                    # Additionally ensure top edge isn't already filled (should be empty when called)
                    completed.append((br, bc))
            if 1 <= r <= 4 and 0 <= c <= 3:
                br, bc = r-1, c
                other_filled = (
                    horizontal[br, bc] != 0 and     # top
                    vertical[br, bc] != 0 and       # left
                    vertical[br, bc+1] != 0        # right
                )
                # Here, the played edge is bottom edge of box (br,bc)
                # For completion, top+left+right must already be filled (bottom will be filled by our move).
                if other_filled:
                    completed.append((br, bc))
        else:  # 'V'
            # vertical edge at (r,c) is left of box (r,c) if r in 0..3 and c in 0..3
            # also right of box (r,c-1) if c-1 in 0..3
            if 0 <= r <= 3 and 0 <= c <= 3:
                br, bc = r, c
                other_filled = (
                    horizontal[br, bc] != 0 and     # top
                    horizontal[br+1, bc] != 0 and # bottom
                    vertical[br, bc+1] != 0        # right
                )
                if other_filled:
                    completed.append((br, bc))
            if 0 <= r <= 3 and 1 <= c <= 4:
                br, bc = r, c-1
                other_filled = (
                    horizontal[br, bc] != 0 and     # top
                    horizontal[br+1, bc] != 0 and # bottom
                    vertical[br, bc] != 0          # left
                )
                if other_filled:
                    completed.append((br, bc))
        return completed

    def count_three_sided_boxes_created_by_edge(dir_char, r, c):
        # Evaluate boxes adjacent to this edge and count how many would become
        # "dangerous": exactly 3 of its edges filled after we play this edge.
        # This is done by checking current filled count for each adjacent box,
        # then adding 1 for the played edge (since it is empty now).
        danger = 0
        adjacent_boxes = []
        if dir_char == 'H':
            if 0 <= r <= 3 and 0 <= c <= 3:
                adjacent_boxes.append((r, c))
            if 1 <= r <= 4 and 0 <= c <= 3:
                adjacent_boxes.append((r-1, c))
        else:
            if 0 <= r <= 3 and 0 <= c <= 3:
                adjacent_boxes.append((r, c))
            if 0 <= r <= 3 and 1 <= c <= 4:
                adjacent_boxes.append((r, c-1))

        # For each adjacent box, compute filled sides after playing.
        for br, bc in adjacent_boxes:
            # Determine filled status of the four edges with our hypothetical placement.
            # edges values: horizontal[br,bc], horizontal[br+1,bc], vertical[br,bc], vertical[br,bc+1]
            # Replace the played edge with filled.
            # Count filled edges.
            h_top = horizontal[br, bc] != 0
            h_bot = horizontal[br+1, bc] != 0
            v_left = vertical[br, bc] != 0
            v_right = vertical[br, bc+1] != 0

            # If this play is the top/bottom/left/right edge, update accordingly.
            if dir_char == 'H':
                if r == br and c == bc:
                    h_top = True
                if r == br+1 and c == bc:
                    h_bot = True
            else:
                if r == br and c == bc:
                    v_left = True
                if r == br and c == bc+1:
                    v_right = True

            filled = int(h_top) + int(h_bot) + int(v_left) + int(v_right)
            if filled == 3:
                danger += 1
        return danger

    def legal_moves():
        moves = []
        # Horizontal edges: r 0..4, c 0..4
        for r in range(5):
            for c in range(5):
                if horizontal[r, c] == 0:
                    moves.append((r, c, 'H'))
        # Vertical edges: r 0..4, c 0..4
        for r in range(5):
            for c in range(5):
                if vertical[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves

    moves = legal_moves()

    # 1) Take any immediate captures.
    best_capture_moves = []
    for r, c, d in moves:
        completed = boxes_completed_by_edge(d, r, c)
        if len(completed) > 0:
            best_capture_moves.append((len(completed), r, c, d))
    if best_capture_moves:
        # Prefer maximum boxes captured
        best_capture_moves.sort(reverse=True)  # by (count, r, c, d) lexicographically; ok
        _, r, c, d = best_capture_moves[0]
        return f"{r},{c},{d}"

    # 2) Otherwise, avoid giving opponent a box with 3 sides filled.
    # Choose move that minimizes number of 3-sided boxes created for opponent.
    scored = []
    for r, c, d in moves:
        danger = count_three_sided_boxes_created_by_edge(d, r, c)
        # secondary heuristic: also avoid moves that affect already-captured boxes is irrelevant;
        # but we can slightly prefer moves that create fewer total adjacent box tensions.
        adjacent_tension = danger
        # If tie, add a tiny preference for central-ish edges to improve future mobility.
        center_pref = 0
        # For centrality: r closer to 1.5..2.5 and c closer similarly.
        center_pref = - (abs(r - 2) + abs(c - 2))  # higher is better
        scored.append((danger, adjacent_tension, -danger, center_pref, r, c, d))

    # Filter safest: danger == 0 if possible, else minimal danger.
    scored.sort(key=lambda x: (x[0], x[1], -x[3]))  # danger, then adjacent_tension, then center_pref
    best = scored[0]
    _, _, _, _, r, c, d = best
    return f"{r},{c},{d}"
