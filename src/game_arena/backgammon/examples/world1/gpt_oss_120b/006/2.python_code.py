
import copy

def policy(state: dict) -> str:
    """
    Return a legal move string for the given Backgammon state.
    The move string format is "<ORDER>:<FROM1>,<FROM2>" where ORDER is H or L,
    and each FROM token is A0..A23, B (bar) or P (pass).
    """
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice'][:]               # list of 0, 1 or 2 ints

    # No dice – must pass
    if not dice:
        return "H:P,P"

    # Normalise dice list (if only one value, duplicate it)
    if len(dice) == 1:
        dice = [dice[0], dice[0]]

    hi = max(dice)
    lo = min(dice)

    # ------------------------------------------------------------------
    # Helper functions
    # ------------------------------------------------------------------

    def dest_from_bar(die):
        """Destination index when entering from the bar."""
        return 24 - die               # 0‑based board, player moves 23→0

    def can_enter(die):
        """Can a checker on the bar enter with this die?"""
        if my_bar == 0:
            return False
        d = dest_from_bar(die)
        return opp_pts[d] < 2

    def all_in_home(pts):
        """True if all my checkers are on points 0..5 (home board)."""
        for i in range(6, 24):
            if pts[i]:
                return False
        return True

    def higher_point_exists_above(i, pts):
        """Any own checker on a higher home point than i? (i in 0..5)."""
        for j in range(i + 1, 6):
            if pts[j]:
                return True
        return False

    def possible_starts(pts, opp, bar, die):
        """Return a list of start tokens that can legally move with *die*."""
        starts = []

        # From bar
        if bar > 0 and opp[dest_from_bar(die)] < 2:
            starts.append('B')

        # From board points
        for i in range(24):
            if pts[i] == 0:
                continue
            dest = i - die
            if dest >= 0:
                # normal move inside board
                if opp[dest] < 2:
                    starts.append(f"A{i}")
            else:
                # bearing off
                if all_in_home(pts):
                    # exact bear off
                    if dest == -1:
                        starts.append(f"A{i}")
                    # bear off from higher point if no higher checkers
                    elif not higher_point_exists_above(i, pts):
                        starts.append(f"A{i}")
        return starts

    def apply_move(pts, opp, bar, opp_bar, off, start, die):
        """Return new (pts, opp, bar, opp_bar, off) after moving *start* with *die*."""
        pts = pts[:]      # shallow copy of lists
        opp = opp[:]

        # Determine source
        if start == 'B':
            bar -= 1
            src_desc = 'bar'
        else:
            src = int(start[1:])
            pts[src] -= 1
            src_desc = src

        # Destination
        if start == 'B':
            dest = dest_from_bar(die)
        else:
            src = int(start[1:])
            dest = src - die

        # Bearing off
        if dest < 0:
            off += 1
            return pts, opp, bar, opp_bar, off

        # Hit?
        if opp[dest] == 1:
            opp[dest] = 0
            opp_bar += 1

        # Place checker
        pts[dest] += 1
        return pts, opp, bar, opp_bar, off

    def move_score(move_seq):
        """Simple heuristic score for a sequence of moves (list of (start,die))."""
        score = 0
        # simulate to know hits and blots created
        temp_pts = my_pts[:]
        temp_opp = opp_pts[:]
        temp_bar = my_bar
        temp_opp_bar = opp_bar
        temp_off = my_off

        for start, die in move_seq:
            # identify hit
            if start == 'B':
                dest = dest_from_bar(die)
                if opp_pts[dest] == 1:
                    score += 10          # hit
                # after move, we will update state
            else:
                src = int(start[1:])
                dest = src - die
                if dest >= 0 and opp_pts[dest] == 1:
                    score += 10

            # bearing off adds some value
            if start != 'B' and (int(start[1:]) - die) < 0:
                score += 5

            # apply move to keep track of created blots
            temp_pts, temp_opp, temp_bar, temp_opp_bar, temp_off = apply_move(
                temp_pts, temp_opp, temp_bar, temp_opp_bar, temp_off, start, die)

        # penalise blots we leave behind (points with exactly 1 checker)
        for cnt in temp_pts:
            if cnt == 1:
                score -= 2
        return score

    # ------------------------------------------------------------------
    # Enumerate all legal move strings
    # ------------------------------------------------------------------

    candidate_moves = []

    # Helper to create the move string from order and start tokens
    def make_move_str(order, s1, s2):
        return f"{order}:{s1},{s2}"

    # Try both possible orders (H = high die first, L = low die first)
    for order in ('H', 'L'):
        first_die = hi if order == 'H' else lo
        second_die = lo if order == 'H' else hi

        # First die possible starts
        first_starts = possible_starts(my_pts, opp_pts, my_bar, first_die)
        if not first_starts:
            continue

        for s1 in first_starts:
            # Apply first move
            pts1, opp1, bar1, opp_bar1, off1 = apply_move(
                my_pts, opp_pts, my_bar, opp_bar, my_off, s1, first_die)

            # Second die possible starts *after* first move
            second_starts = possible_starts(pts1, opp1, bar1, second_die)

            # If we can play the second die, generate full move
            if second_starts:
                for s2 in second_starts:
                    cand = (order, s1, s2, [(s1, first_die), (s2, second_die)])
                    candidate_moves.append(cand)
            else:
                # Second die cannot be played – a single‑die move is legal only
                # if the higher die cannot be played at all.  We will handle those
                # later, so skip adding a two‑token move with a pass here.
                pass

    # ------------------------------------------------------------------
    # If we have any two‑die moves, pick the best according to the heuristic.
    # ------------------------------------------------------------------
    if candidate_moves:
        best = None
        best_score = -10**9
        for order, s1, s2, seq in candidate_moves:
            sc = move_score(seq)
            if sc > best_score:
                best_score = sc
                best = (order, s1, s2)
        return f"{best[0]}:{best[1]},{best[2]}"

    # ------------------------------------------------------------------
    # No two‑die move possible – try a single die (must be the higher if
    # possible, otherwise the lower).
    # ------------------------------------------------------------------
    # First try higher die
    higher_starts = possible_starts(my_pts, opp_pts, my_bar, hi)
    if higher_starts:
        # choose best single move
        best = None
        best_score = -10**9
        for s in higher_starts:
            sc = move_score([(s, hi)])
            if sc > best_score:
                best_score = sc
                best = s
        return f"H:{best},P"

    # Try lower die
    lower_starts = possible_starts(my_pts, opp_pts, my_bar, lo)
    if lower_starts:
        best = None
        best_score = -10**9
        for s in lower_starts:
            sc = move_score([(s, lo)])
            if sc > best_score:
                best_score = sc
                best = s
        return f"H:P,{best}"   # order is irrelevant when only one die is used; we use H

    # ------------------------------------------------------------------
    # No move possible – pass.
    # ------------------------------------------------------------------
    return "H:P,P"
