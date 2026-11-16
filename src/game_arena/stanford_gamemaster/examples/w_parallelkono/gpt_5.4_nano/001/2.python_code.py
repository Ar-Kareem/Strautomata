
import math

def policy(state: list[list[object]], role: str) -> str:
    # --- Helpers to parse state ---
    cells = {}  # (col,row)->color/blank
    control_role = None
    for fact in state:
        if not fact:
            continue
        if fact[0] == "cell":
            # ["cell", col, x, y, color] where x is file letter? In examples: col is 'a'/'b', and x is "1".."4"
            # Format appears: ["cell", "a"/"b", x, y, color]
            _, c, x, y, col = fact
            cells[(c, int(x), int(y))] = col
        elif fact[0] == "control":
            control_role = fact[1]
        # scores/step ignored
    
    my_color = role
    opp_color = "black" if my_color == "red" else "red"

    # If control doesn't match, attempt tick (environment expects tick when "played" phase, etc.)
    # In provided examples: when it's your role, control=<role>. Otherwise often only tick is legal.
    if control_role is not None and control_role != my_color:
        return "tick"

    # Determine mapping and movement model.
    # Board: 2 columns (a,b), 4 rows (1..4). So 8 cells total.
    # Movement graphs in this variant correspond to diagonal connections like typical 2x4 slanted checkers:
    # Possible moves are between adjacent coordinates:
    # From (col, x, y):
    #  - "forward" direction depends on color: red moves towards increasing y? Examples show red near bottom (y=3,4?) capturing upwards.
    # But we don't have explicit orientation; infer from examples:
    # Initial: red pieces at y=1? Actually examples at Turn0: red at ["cell","a","3","1","red"] etc and at ["cell","a","4","4","red"].
    # That suggests x=3,4 are their column-lane, y=1..4 represent board row.
    # However action strings are: jump(a,4,1,3,1,2,1)
    # which looks like: jump(from_col, from_x, from_y, mid_col, mid_x, mid_y, to_col)
    # It's hard, but we can rely on the fact that the action syntax always has 7 args:
    # jump(c1,x1,y1,c2, x2, y2, c3)?? No, example: jump(a,4,1,3,1,2,1)
    # Split: [a,4,1,3,1,2,1] => 7 tokens after jump(
    # So likely: jump(col_from, x_from, y_from, col_mid?, x_mid, y_mid, col_to?) doesn't fit.
    # Alternative: jump(col, x_from, y_from, x_mid, y_mid, x_to, y_to) with col repeated once.
    # Example jump(a,4,1,3,1,2,1):
    # => col_from='a', x_from=4, y_from=1, x_mid=3, y_mid=1, x_to=2, y_to=1 all on same y=1 line.
    # That would mean horizontal jumps along same y. Another example:
    # jump(a,1,2,2,2,3,2) from Turn3 black.
    # => col='a', x_from=1, y_from=2, x_mid=2, y_mid=2, x_to=3, y_to=2.
    # So: first token after jump is column letter, then 3 coordinate pairs along that line:
    # from=(col, x_from, y_from), mid=(col_mid? actually x_mid,y_mid), to=(col, x_to, y_to).
    # Great: only one column letter in syntax => move confined to same column letter.
    # But there are moves like move(b,1,1,1,2) => tokens: [b,1,1,1,2] => move(col, x_from, y_from, x_to, y_to).
    # So syntax is:
    #   move(col, x1, y1, x2, y2)
    #   jump(col, x1, y1, xm, ym, x2, y2)
    #
    # Therefore the board is effectively 2x4 but encoded as (col in {a,b}, x in {1..4}, y in {1..4})
    # with all moves within same col. That yields 2*4*4=32 cells; but state shows x in 1..4 and y in 1..4 indeed.
    # Total cells shown in examples: 16 per color => 32 cells total. So yes, there are 4x4 grid,
    # but represented as two "col groups" each labeled a or b (probably top/bottom halves).
    # Likely: col letter encodes the board rows (2 groups), and x is file, y is rank.
    #
    # We'll adopt generic legal move generation assuming movement along x or y adjacency with jumps over own color.
    # However we lack exact connectivity; simplest workable approach:
    # - Generate candidate moves by trying to use captures that are consistent with observed syntax:
    #   Consider 4-neighbor diagonals: (x +/-1, y) and (x, y +/-1) and (x +/-1, y +/-1) are typical.
    # We'll implement two likely directions depending on whether "forward" means y increasing for red and decreasing for black,
    # but for tactic it suffices to consider all directions and allow any.
    #
    # Also we must ensure produced action is legal; without full connectivity we might fail.
    # So we instead implement "best-effort" by using only local patterns that match examples:
    # Captures shown had same y (jump(...,4,1,3,1,2,1) and jump(...,1,2,2,2,3,2)).
    # We'll restrict captures to same y and adjacent x distance 2.
    # Non-captures: same y adjacent x distance 1.
    #
    # This matches the examples and is likely the intended graph: a line per y across x=1..4 within each col letter.
    # Additionally there are moves like move(a,2,1,1,1?) not shown; but we saw move(a,2,4,1,4) meaning same y again.
    
    dirs = [(-1, 0), (1, 0)]  # along x
    # Generate legal-looking candidates; then choose one that seems best.
    
    def occupied(coord):
        return cells.get(coord, "blank")
    
    def in_bounds(x, y):
        return 1 <= x <= 4 and 1 <= y <= 4
    
    # Find my pieces
    my_pieces = []
    for (col, x, y), c in cells.items():
        if c == my_color:
            my_pieces.append((col, x, y))
    
    # If no pieces, tick
    if not my_pieces:
        return "tick"
    
    # Candidate jumps
    best_action = None
    best_score = -1e18

    def evaluate_after_landing(col, x_to, y_to, captured_count):
        # Heuristic: prioritize immediate capture, then advancement (towards opponent home).
        # Infer forward: red home is at smaller y? In initial, red at y=1..4 with x=3,4 suggests not.
        # We only have x movement, so use y as "depth" and push red to larger y, black to smaller y.
        forward_dir = 1 if my_color == "red" else -1
        advance = forward_dir * (y_to)
        # Prefer central x
        center_bonus = -abs(2.5 - x_to)
        # Prefer having fewer immediate threats: if opponent can jump back immediately, penalize.
        threat_penalty = 0
        # Opp can capture along same y if we left a capturable piece.
        # Simulate whether any opponent piece at (col, x_opp, y_to) can jump over us.
        for (ocol, ox, oy) in my_pieces:  # wrong scope; instead check opponent pieces
            pass
        return captured_count * 1000 + advance * 5 + center_bonus * 1 + threat_penalty

    # Build opponent piece list
    opp_pieces = [(col, x, y) for (col, x, y), c in cells.items() if c == opp_color]

    def is_threatened_if_land(col, x_to, y_to):
        # If we land at (col,x_to,y_to), can any opponent jump over any own piece? Actually capture happens by jumping over opponent piece.
        # So for opponent to capture us, opponent must have piece at (col, x_to - dx, y_to) where landing is at (col, x_to + dx, y_to),
        # with dx=1 and path contains our piece at x_to.
        threatened = False
        for (ocol, ox, oy) in opp_pieces:
            if ocol != col or oy != y_to:
                continue
            # opponent jumping over our piece to land beyond
            for dx, dy in [( -1, 0), (1, 0)]:
                # if opponent at ox, then mid would be our x_to if x_to == ox + dx*1
                mid_x = ox + dx
                land_x = ox + dx*2
                if mid_x == x_to and in_bounds(land_x, y_to):
                    # landing must be blank
                    if occupied((col, land_x, y_to)) == "blank":
                        threatened = True
        return threatened

    # Generate jumps restricted to same col and same y along x
    for col, x, y in my_pieces:
        for dx, dy in dirs:
            xm = x + dx
            x2 = x + dx*2
            ym = y + dy
            y2 = y + dy*2
            if not (in_bounds(xm, ym) and in_bounds(x2, y2)):
                continue
            if occupied((col, xm, ym)) == opp_color and occupied((col, x2, y2)) == "blank":
                # action: jump(col,x,y,xm,ym,x2,y2)
                action = f"jump({col},{x},{y},{xm},{ym},{x2},{y2})"
                threatened = is_threatened_if_land(col, x2, y2)
                score = 1_000_000 + 500 * 1
                # advancement heuristic
                forward_dir = 1 if my_color == "red" else -1
                score += forward_dir * y2 * 50 + (-abs(2.5 - x2)) * 10
                if threatened:
                    score -= 2000
                if score > best_score:
                    best_score = score
                    best_action = action

    if best_action is not None:
        return best_action

    # Otherwise, generate simple moves restricted to same col and same y along x distance 1
    best_action = None
    best_score = -1e18
    for col, x, y in my_pieces:
        for dx, dy in dirs:
            x2 = x + dx
            y2 = y + dy
            if not in_bounds(x2, y2):
                continue
            if occupied((col, x2, y2)) == "blank":
                action = f"move({col},{x},{y},{x2},{y2})"
                threatened = is_threatened_if_land(col, x2, y2)
                forward_dir = 1 if my_color == "red" else -1
                score = forward_dir * y2 * 50 + (-abs(2.5 - x2)) * 10
                if threatened:
                    score -= 200
                if score > best_score:
                    best_score = score
                    best_action = action

    return best_action if best_action is not None else "tick"
