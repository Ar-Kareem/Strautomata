
import re
from typing import List, Tuple, Optional

def policy(state: list[list[object]], role: str) -> str:
    # ---------- Helpers: parse board ----------
    # cell: ["cell", x, y, n, color]
    board = {}  # (x,y)->(n,color)
    fighters = {role: [], "red" if role=="green" else "green": []}
    other = "red" if role == "green" else "green"
    step_facts = []
    for fact in state:
        if not fact:
            continue
        if fact[0] == "cell":
            x = int(fact[1]); y = int(fact[2]); n = int(fact[3]); c = str(fact[4])
            board[(x, y)] = (n, c)
            if c in fighters:
                fighters[c].append((x, y, n))
        elif fact[0] == "step":
            step_facts.append(fact)

    # ---------- Game geometry ----------
    # Board is 5x5; x,y likely in [1..5]
    def inb(x, y):
        return 1 <= x <= 5 and 1 <= y <= 5

    # ---------- Capture rule ("eat") ----------
    # Generally can eat any smaller or equal, except:
    # 1 can eat 5 but 5 cannot eat 1.
    def can_eat(att, dfn):
        if att == dfn:
            return True
        if att > dfn:
            # includes att=5 dfn=1 (disallowed)
            if att == 5 and dfn == 1:
                return False
            return True
        # att < dfn normally cannot eat larger
        # (but 1 can eat 5 special)
        if att == 1 and dfn == 5:
            return True
        return False

    # ---------- Movement model ----------
    # A fighter can move forward to an empty cell orthogonally or diagonally.
    # Also capture diagonally only (can capture backward as well).
    # Interpreting "forward": red increases x? In examples:
    # Turn0 red move(1,1,1,2): x=1 constant, y:1->2, so red "forward" is +y.
    # Green move(1,5,1,4): y:5->4, so green "forward" is -y.
    # Thus: red forward direction = (0,+1), green forward = (0,-1).
    forward = (0, 1) if role == "red" else (0, -1)

    # Orthogonal or diagonal "forward" empty moves:
    # forward orthogonal: (x, y+dy) with dx=0
    # forward diagonal: (x±1, y+dy)
    # Capture diagonally only: "diagonally" meaning dx=±1, dy=±1 (any dy direction)
    # We'll generate both forward-diagonal captures and backward-diagonal captures.
    move_dirs_forward_empty = [(0, forward[1]), (1, forward[1]), (-1, forward[1])]
    capture_dirs_diag = [(1, 1), (-1, 1), (1, -1), (-1, -1)]

    # ---------- Determine current positions ----------
    my_pieces = fighters.get(role, [])
    my_pieces_set = {(x,y) for (x,y,_) in my_pieces}

    # ---------- Candidate move generation with legality checks ----------
    def get_piece_at(x, y):
        return board.get((x, y), None)

    def simulate_actions():
        actions = []  # list of (action_str, meta)
        for (sx, sy, sn) in my_pieces:
            # forward empty moves
            for dx, dy in move_dirs_forward_empty:
                tx, ty = sx + dx, sy + dy
                if not inb(tx, ty):
                    continue
                if (tx, ty) in board:
                    continue
                # move is legal if destination empty
                actions.append((f"move({sx},{sy},{tx},{ty})", {"type": "move", "sx": sx, "sy": sy, "tx": tx, "ty": ty, "sn": sn, "capture": None}))

            # diagonal captures (any direction)
            for dx, dy in capture_dirs_diag:
                tx, ty = sx + dx, sy + dy
                if not inb(tx, ty):
                    continue
                occ = get_piece_at(tx, ty)
                if not occ:
                    continue
                tn, c = occ
                if c == role:
                    continue
                # capture legality depends on eat rule
                if can_eat(sn, tn):
                    actions.append((f"move({sx},{sy},{tx},{ty})", {"type": "capture", "sx": sx, "sy": sy, "tx": tx, "ty": ty, "sn": sn, "capture": tn}))
        return actions

    candidates = simulate_actions()

    # As a fail-safe (shouldn't happen), if no candidates were generated, try any diagonal step within board.
    if not candidates:
        for (sx, sy, sn) in my_pieces:
            for dx, dy in [(0, forward[1]), (1, forward[1]), (-1, forward[1])]:
                tx, ty = sx + dx, sy + dy
                if inb(tx, ty) and (tx, ty) not in board:
                    return f"move({sx},{sy},{tx},{ty})"
        # ultimate fallback: return any syntactically valid move (may be illegal in some rare cases)
        return "move(1,1,1,2)"

    # ---------- Scoring heuristic ----------
    # Higher is better.
    def score_action(meta):
        sn = meta["sn"]
        tx, ty = meta["tx"], meta["ty"]
        sx, sy = meta["sx"], meta["sy"]
        is_red = (role == "red")

        # advancement: red wants to increase ty, green wants to decrease ty
        adv = ty - sy if is_red else sy - ty  # positive if moving forward

        # base preferences
        base = 10 * adv

        if meta["type"] == "capture":
            cap = meta["capture"]  # opponent piece number
            # reward capturing something valuable, but also discourage capturing a piece that would be "too good" to take back
            # Since we don't know opponent next, approximate risk by checking if opponent has any immediate counter-capture
            reward = 60 + 12 * cap  # capturing larger is good
            # But 1 capturing 5 is special; still legal. Reward slightly less because it may be fragile.
            if sn == 1 and cap == 5:
                reward -= 10

            # immediate risk estimate: can opponent capture our destination square right away?
            # We'll look for any opponent piece that can capture onto (tx,ty) with eat rules.
            risk = 0
            for (ox, oy, on) in fighters.get(other, []):
                # can it capture diagonally into our destination?
                if abs(ox - tx) == 1 and abs(oy - ty) == 1:
                    if can_eat(on, sn):
                        # if opponent can recapture, penalize
                        risk += (30 + 8 * sn)
                        # larger opponents recapture risk more
                        risk += 2 * on
            # also if by moving (non-capture) we expose to immediate capture, penalize
            # (only for non-capture moves)
            return base + reward - risk
        else:
            # non-capture: small bonus for moving toward center/advance, penalty if landing on a square that opponent can capture
            exposure = 0
            # check if any opponent piece can capture us at (tx,ty) immediately
            for (ox, oy, on) in fighters.get(other, []):
                if abs(ox - tx) == 1 and abs(oy - ty) == 1:
                    if can_eat(on, sn):
                        exposure += (20 + 6 * sn)  # moving into capture range is bad
            return base - exposure + 2  # small constant

    # Choose max scoring; tie-break by preferring captures.
    best = None
    best_key = None
    for a, meta in candidates:
        sc = score_action(meta)
        iscap = 1 if meta["type"] == "capture" else 0
        key = (sc, iscap, meta["ty"] if role=="red" else -meta["ty"], meta["sn"])
        if best is None or key > best_key:
            best = a
            best_key = key

    return best
