
from __future__ import annotations
from functools import lru_cache

# Standard Kalah (Mancala) rules:
# - 6 houses per side, index 0..5 houses, index 6 store
# - Actions: choose a non-empty house i in 0..5 for "you"
# - Sowing skips opponent's store
# - Extra move if last seed lands in your store (you[6])
# - Capture rule as described

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Return an integer move i in 0..5 with you[i] > 0.
    """

    # --- Game mechanics helpers ---
    def normalize_state(you_t, opp_t):
        # Ensure tuples for caching
        return (tuple(you_t), tuple(opp_t))

    def opposite_index(i: int) -> int:
        # Opponent's opposite house index for your house i
        return 5 - i

    def legal_moves(you_t):
        return [i for i in range(6) if you_t[i] > 0]

    def is_terminal(you_t, opp_t):
        return all(x == 0 for x in you_t[0:6]) or all(x == 0 for x in opp_t[0:6])

    def apply_move(you_t, opp_t, move_i: int):
        """
        Apply move for the player represented by (you_t, opp_t).
        Returns: (new_you, new_opp, extra_turn_flag)
        Note: Capture and endgame sweeping are handled.
        """
        you_u = list(you_t)
        opp_u = list(opp_t)

        seeds = you_u[move_i]
        you_u[move_i] = 0

        pos_side = 0  # 0 => you side/track, 1 => opponent side/track
        pos = move_i

        # We will simulate by stepping through the global ring:
        # sequence (starting after removing from move_i):
        # you houses i+1..5, then you store, then opponent houses 0..5, then you houses 0..5...
        # skipping opponent store.
        # Use simple modular walk with explicit mapping for correctness.

        # Build an array representing sowing positions in order for one full cycle:
        # 0..5 : you houses
        # 6    : you store
        # 7..12: opponent houses 0..5
        # (opponent store not included)
        ring = [(0, j) for j in range(6)] + [(0, 6)] + [(1, j) for j in range(6)]
        # ring length = 6 + 1 + 6 = 13
        # Starting index is the position of (0, move_i) in ring, then drop next seeds starting from next.
        start_idx = 0
        for idx, (side, idx2) in enumerate(ring):
            if side == 0 and idx2 == move_i:
                start_idx = idx
                break

        idx = start_idx
        last_side, last_idx2 = 0, move_i
        for _ in range(seeds):
            idx = (idx + 1) % len(ring)
            last_side, last_idx2 = ring[idx]
            if last_side == 0:
                you_u[last_idx2] += 1
            else:
                opp_u[last_idx2] += 1

        # Determine extra turn
        extra_turn = (last_side == 0 and last_idx2 == 6)

        # Capture rule (only if last seed lands in your house 0..5)
        if not extra_turn and last_side == 0 and 0 <= last_idx2 <= 5:
            # Must have been empty before landing: check by inspecting whether the house had 0 seeds pre-drop.
            # We can infer pre-drop emptiness because we only changed that house by sowing final seed.
            # But other seeds could not have landed back into same house except last one due to move rules.
            # Therefore, house was empty iff it is now 1 (since we dropped last seed there).
            if you_u[last_idx2] == 1:
                opp_i = opposite_index(last_idx2)
                if opp_u[opp_i] > 0:
                    captured = you_u[last_idx2] + opp_u[opp_i]
                    you_u[last_idx2] = 0
                    opp_u[opp_i] = 0
                    you_u[6] += captured

        # Endgame sweep: if one side has no seeds in houses, move remaining to opponent's store
        if all(x == 0 for x in you_u[0:6]):
            # you empty => opponent sweeps remaining on their side into their store
            remaining = sum(opp_u[0:6])
            for k in range(6):
                opp_u[k] = 0
            opp_u[6] += remaining
        elif all(x == 0 for x in opp_u[0:6]):
            remaining = sum(you_u[0:6])
            for k in range(6):
                you_u[k] = 0
            you_u[6] += remaining

        return you_u, opp_u, extra_turn

    # --- Evaluation function ---
    def eval_state(you_t, opp_t):
        # Win/loss score based on store difference, with additional positional heuristics.
        you_store = you_t[6]
        opp_store = opp_t[6]

        # If terminal, return decisive value
        if all(x == 0 for x in you_t[0:6]) or all(x == 0 for x in opp_t[0:6]):
            if you_store > opp_store:
                return 10_000 + (you_store - opp_store)
            elif you_store < opp_store:
                return -10_000 - (opp_store - you_store)
            else:
                return 0

        # Heuristic components
        store_diff = you_store - opp_store

        # Potential captures: count captures available on next move
        # If we play i, last seed lands in i and i was empty -> capture.
        # We estimate by looking for opponent non-empty opposite houses when we can land in an empty house.
        # We'll approximate via current empties and seed counts (coarse but helpful).
        empties = [1 if you_t[i] == 0 else 0 for i in range(6)]
        opp_presence = [1 if opp_t[j] > 0 else 0 for j in range(6)]

        capture_potential = 0
        for i in range(6):
            if empties[i] and opp_presence[5 - i]:
                # If we could land in i, it's a good sign. Weight by opponent seeds opposite.
                capture_potential += opp_t[5 - i]

        # Extra-turn tendency: moves that land in store are valuable; we estimate by near-store sowing lengths.
        # Approx: if you have enough seeds to wrap to store. Coarse:
        extra_turn_bins = 0
        for i in range(6):
            s = you_t[i]
            if s == 0:
                continue
            # Last landing in store occurs when (s mod 13) places final in store relative to i's position.
            # Instead of exact compute here, do a quick check using ring mapping:
            # For each i, exact "landing in store" position can be computed precisely from ring,
            # but for speed we approximate with s % 13 == (something). We'll omit exact and rely on search.

        # Safety: avoid leaving opponent capture opportunities.
        # Approx measure: number of opponent captures available if they were to play optimally now.
        # We'll compute exact opponent capture opportunities for current board based on empties and seed counts length mod 13.
        # This still costs little.
        opp_capture_threat = 0
        # Precompute ring positions for exact landing calculation
        ring = [(0, j) for j in range(6)] + [(0, 6)] + [(1, j) for j in range(6)]
        idx_of_you = [0]*6
        for idx, (side, idx2) in enumerate(ring):
            if side == 0 and 0 <= idx2 <= 5:
                idx_of_you[idx2] = idx

        for i in range(6):
            if you_t[i] == 0:
                # could be captured by opponent landing here if opponent plays some move that ends at our i
                # We'll approximate by considering opponent moves j that would land at our i given current opp seeds.
                # Determine exact for each opponent move.
                pass

        # Instead of full threat computation, use a simple "front-load" danger heuristic:
        # Lower-index houses (closer to sowing start next) are more exposed; still keep it moderate.
        # Penalize having many seeds in houses that are empty opposite for opponent (less relevant),
        # so we instead reward your empties when opponent has seeds opposite them.
        danger = 0
        for i in range(6):
            if opp_t[5 - i] > 0 and you_t[i] == 0:
                # leaving empty opposite a rich pocket is risky
                danger += opp_t[5 - i]

        # Mobility: count legal moves
        mobility = sum(1 for x in you_t[0:6] if x > 0)

        # Combine
        score = 120 * store_diff
        score += 6 * capture_potential
        score -= 4 * danger
        score += 2 * mobility

        # If you are far ahead, slightly prefer simplifying by protecting store lead
        if store_diff > 0:
            score += 0.1 * (you_store)
        else:
            score -= 0.1 * (opp_store)

        return score

    # --- Minimax with alpha-beta ---
    # Use small depth to fit time; Kalah branching factor <= 6.
    # Include extra-turn by not switching players when extra_turn is True.
    DEPTH = 5

    @lru_cache(maxsize=None)
    def search(you_t, opp_t, depth, alpha, beta):
        you_t = list(you_t)
        opp_t = list(opp_t)

        if depth == 0 or is_terminal(you_t, opp_t):
            return eval_state(you_t, opp_t), None

        best_move = None
        best_val = -float("inf")

        # Move ordering: captures and extra-turn first
        moves = legal_moves(you_t)

        def move_priority(i):
            # priority higher first
            # Simulate just enough to check capture/extra
            y2, o2, extra = apply_move(you_t, opp_t, i)
            # capture heuristic: gained store amount this move
            capture_gain = y2[6] - you_t[6]
            # approximate ordering
            pri = 0
            if extra:
                pri += 50_000
            pri += 10 * capture_gain
            # also prefer moves that improve store diff
            pri += (y2[6] - o2[6]) - (you_t[6] - opp_t[6])
            return pri

        moves.sort(key=move_priority, reverse=True)

        # alpha-beta
        for i in moves:
            y2, o2, extra = apply_move(you_t, opp_t, i)
            if extra:
                # same player continues; opponent unchanged roles for turn logic:
                val, _ = search(normalize_state(y2, o2)[0], normalize_state(y2, o2)[1], depth - 1, alpha, beta)
                # BUT search expects (you, opponent) from current player perspective; we are current player still => OK.
            else:
                # switch perspectives: opponent becomes "you" for next ply
                # so new perspective is (o2, y2)
                val, _ = search(normalize_state(o2, y2)[0], normalize_state(o2, y2)[1], depth - 1, -beta, -alpha)
                val = -val

            if val > best_val:
                best_val = val
                best_move = i
            alpha = max(alpha, best_val)
            if alpha >= beta:
                break

        return best_val, best_move

    # Convert to tuples for caching
    you0, opp0 = tuple(you), tuple(opponent)

    # Quick immediate win check: if any move ends game with best store lead, pick it.
    best_i = None
    best_score = -float("inf")
    for i in legal_moves(you0):
        y2, o2, extra = apply_move(list(you0), list(opp0), i)
        # If terminal, evaluation will dominate
        s = eval_state(y2, o2)
        if s > best_score:
            best_score = s
            best_i = i

    if best_i is not None and best_score > 9_000:
        return best_i

    # Otherwise use minimax search
    # Initialize alpha-beta bounds
    _, move = search(you0, opp0, DEPTH, -float("inf"), float("inf"))
    if move is None:
        # Fallback: any legal move
        return legal_moves(you0)[0]
    return move
