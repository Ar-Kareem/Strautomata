
import re

def policy(state: list[list[object]], role: str) -> str:
    # Identify whose turn/control
    # State includes ["control", "red"/"blue"].
    turn_role = role
    for fact in state:
        if len(fact) == 2 and fact[0] == "control":
            turn_role = fact[1]
            break

    if turn_role != role:
        # In case role mismatch, still attempt to move for provided role, but
        # safest is to use the role that is actually controlled if present.
        pass

    my = role
    opp = "blue" if my == "red" else "red"

    # Build quick lookup for occupied cells
    occupied = set()
    for fact in state:
        if len(fact) == 4 and fact[0] == "cell":
            occupied.add((fact[1], fact[2]))

    # Helper: parse potential place actions from state by scanning for "line_count" facts
    # that reference cells.
    # We don't have legal actions list, so infer all playable cells by finding
    # coordinate pairs referenced in either cell/line_count patterns.
    # Observed placement syntax: place(a,5) etc. So coords are like ["a","5"] or ["i","4"].
    coords = set()
    for fact in state:
        if len(fact) == 4 and fact[0] == "cell":
            coords.add((fact[1], fact[2]))
    # Additionally, infer all possible cells from the board encoding via line_count patterns
    # like line_count, a5, red, k or similar. Those include composite coords.
    # Composite tokens appear to be letter+number with letter in [a-i] and number 1-9.
    for fact in state:
        if len(fact) == 4 and fact[0] == "line_count":
            key = fact[1]
            if isinstance(key, str):
                m = re.fullmatch(r"([a-i])(\d)", key)
                if m:
                    coords.add((m.group(1), m.group(2)))

    # Determine a set of candidate empty cells from inferred coords
    candidates = [(r, c) for (r, c) in coords if (r, c) not in occupied]

    if not candidates:
        # Fallback: try a small set of common coordinates
        for rr in list("abcdefghi"):
            for cc in list("123456789"):
                if (rr, cc) not in occupied:
                    return f"place({rr},{cc})"
        # If still none, return something legal-looking (shouldn't happen)
        return "place(a,1)"

    # Extract line_count facts into lookup: (line_id, color) -> count
    lc = {}
    for fact in state:
        if len(fact) == 4 and fact[0] == "line_count":
            lc[(fact[1], fact[2])] = fact[3]

    # In Majorities (as encoded here), placing at (x,y) affects line_count for:
    # - the “row/letter” line id x (key is the letter)
    # - the “column/number” line id y (key is the number as string)
    # - and the diagonal/combined line id like x+y (key is concatenation letter+number)
    # This matches samples: after place(a,5,red), line_count a red increments; line_count 5 red increments;
    # and line_count a5 red increments. We'll use this to estimate score change.
    def current_score(color: str):
        # Use total across line_count for that color (bigger is better)
        s = 0
        for (lid, col), v in lc.items():
            if col == color and isinstance(v, int):
                s += v
        return s

    my_base = current_score(my)
    opp_base = current_score(opp)

    def estimate_gain(move):
        r, c = move
        my_gain = 0
        opp_gain = 0

        # affected line keys
        affected = [r, c, f"{r}{c}"]
        for lid in affected:
            # increase by 1 for my if I place there, but in case those line_ids are absent
            # the increment would be from 0.
            my_gain += (1 if lc.get((lid, my), 0) is not None else 0)
            opp_gain += 0  # opponent doesn't benefit from my move

        # Also, heuristic: we want to maximize peak line_count for us.
        # We'll add a strong term proportional to resulting maximum line_count.
        peak_before = max(lc.get((lid, my), 0) for lid in affected)
        peak_after = peak_before + 1

        return (peak_after * 1000 + my_gain)

    # Blocking: if opponent could win next, we try to find a move that prevents their best
    # immediate gain from reaching 5 or majority-threshold.
    # We infer threshold from sample late-game where a line_count reached 6 for red.
    # We'll treat >=6 as winning/near-winning; this is a heuristic.
    WIN_TH = 6

    # Precompute opponent candidate moves from empty cells and estimate their peak-after.
    # For each of our candidate moves, check if it removes their winning move.
    # Since we don't know exact legality mapping beyond occupancy, we approximate by:
    # If our move occupies a cell that opponent would otherwise play and that opponent
    # would reach WIN_TH, then we block.
    def opp_would_win_from_cell(cell):
        r, c = cell
        affected = [r, c, f"{r}{c}"]
        peak_before = max(lc.get((lid, opp), 0) for lid in affected)
        peak_after = peak_before + 1
        return peak_after >= WIN_TH

    opp_winning_cells = set([m for m in candidates if opp_would_win_from_cell(m)])

    best_move = None
    best_val = None

    # Primary: immediate win for us (heuristic peak-after >= WIN_TH)
    for mv in candidates:
        r, c = mv
        affected = [r, c, f"{r}{c}"]
        peak_after = max(lc.get((lid, my), 0) for lid in affected) + 1
        if peak_after >= WIN_TH:
            # Prefer moves that also block opponent if possible
            block = 1 if mv in opp_winning_cells else 0
            val = (1_000_000 * block + estimate_gain(mv))
            if best_val is None or val > best_val:
                best_val = val
                best_move = mv

    if best_move is not None:
        return f"place({best_move[0]},{best_move[1]})"

    # Secondary: block opponent immediate winning move if possible
    for mv in candidates:
        block = 1 if mv in opp_winning_cells else 0
        val = (block * 1_000_000 + estimate_gain(mv))
        if best_val is None or val > best_val:
            best_val = val
            best_move = mv

    return f"place({best_move[0]},{best_move[1]})"
