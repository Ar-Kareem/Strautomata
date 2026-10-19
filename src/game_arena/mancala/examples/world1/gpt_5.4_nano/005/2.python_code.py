
from functools import lru_cache

def policy(you: list[int], opponent: list[int]) -> int:
    # ---------- Kalah engine helpers ----------
    def legal_moves(state_you, state_opp):
        return [i for i in range(6) if state_you[i] > 0]

    def is_terminal(state_you, state_opp):
        return all(v == 0 for v in state_you[:6]) or all(v == 0 for v in state_opp[:6])

    def normalize(state_you, state_opp):
        # Apply end-of-game rule if needed
        if all(v == 0 for v in state_you[:6]):
            # opponent collects remaining
            s = sum(state_opp[:6])
            state_opp = state_opp[:]  # copy
            state_opp[6] += s
            state_opp[:6] = [0]*6
            state_you = state_you[:]  # copy
            return tuple(state_you), tuple(state_opp)
        if all(v == 0 for v in state_opp[:6]):
            s = sum(state_you[:6])
            state_you = state_you[:]
            state_you[6] += s
            state_you[:6] = [0]*6
            state_opp = state_opp[:]
            return tuple(state_you), tuple(state_opp)
        return tuple(state_you), tuple(state_opp)

    def opposite_index(i):
        return 5 - i

    def apply_move(state_you, state_opp, i):
        # assumes legal
        you = state_you[:]
        opp = state_opp[:]
        seeds = you[i]
        you[i] = 0
        pos = i
        last_in_store = False
        # sow
        while seeds > 0:
            pos = (pos + 1) % 13  # 6 you houses + store + 6 opp houses = 13 slots
            # Map pos to actual board location, skipping opponent store
            if pos <= 4:
                # you[0..4]
                idx = pos
                you[idx] += 1
                seeds -= 1
                landed = ('you', idx)
            elif pos == 5:
                # you[5]
                you[5] += 1
                seeds -= 1
                landed = ('you', 5)
            elif pos == 6:
                # your store
                you[6] += 1
                last_in_store = True
                seeds -= 1
                landed = ('you', 6)
            elif 7 <= pos <= 12:
                # opponent houses: opponent[0..5] correspond to pos 7..12
                idx = pos - 7
                opp[idx] += 1
                seeds -= 1
                landed = ('opp', idx)
            # skip opponent store is implicit because we never create a slot for it
            if seeds == 0:
                # post-process capture/extra turn
                if landed[0] == 'you' and 0 <= landed[1] <= 5:
                    j = landed[1]
                    # capture requires the house was empty before landing
                    # We need to know whether it was empty before. Since we just sow one by one,
                    # it could have received seeds earlier in this move only if we landed there before the last.
                    # With standard rules, this check can be implemented by tracking emptiness before landing:
                    pass
        # The above sowing doesn't track whether destination was empty before last seed.
        # We'll redo apply_move more carefully with proper tracking.

    # Re-implement apply_move with correct capture semantics.
    def apply_move(state_you, state_opp, i):
        you = list(state_you)
        opp = list(state_opp)
        seeds = you[i]
        you[i] = 0

        last_owner = None
        last_idx = None

        # We'll sow across the cyclic track:
        # Track positions in order (length 13):
        # you[0..5], you_store, opp[0..5]
        # That corresponds to indices 0..12:
        # 0..5: you houses
        # 6: you store
        # 7..12: opp houses
        # Starting after position i.
        pos = i  # current position index on track when we remove seeds
        # define helpers
        def track_add(p):
            nonlocal last_owner, last_idx
            if 0 <= p <= 5:
                you[p] += 1
                last_owner = 'you'
                last_idx = p
            elif p == 6:
                you[6] += 1
                last_owner = 'you'
                last_idx = 6
            else:  # 7..12
                opp[p - 7] += 1
                last_owner = 'opp'
                last_idx = p - 7

        # capture check needs knowing whether destination house was empty before placing last seed.
        # We'll record emptiness before the last seed is placed.
        dest_was_empty = None

        for k in range(seeds):
            pos = (pos + 1) % 13
            if k == seeds - 1:
                # about to drop the last seed at current pos; check emptiness before adding
                if 0 <= pos <= 5:
                    dest_was_empty = (you[pos] == 0)
                elif pos == 6:
                    dest_was_empty = None
                else:
                    dest_was_empty = (opp[pos - 7] == 0)
            track_add(pos)

        extra_turn = (last_owner == 'you' and last_idx == 6)

        # capture: last seed in your house 0..5, house was empty before drop, opposite has seeds
        if last_owner == 'you' and 0 <= last_idx <= 5 and dest_was_empty:
            opp_i = opposite_index(last_idx)
            if opp[opp_i] > 0:
                captured = opp[opp_i]
                # pick up your landed seed too
                captured += you[last_idx]
                you[last_idx] = 0
                opp[opp_i] = 0
                you[6] += captured

        return normalize(tuple(you), tuple(opp))[0], normalize(tuple(you), tuple(opp))[1], extra_turn

    # ---------- Evaluation and search ----------
    def evaluate(state_you, state_opp):
        # store difference is primary
        y_store = state_you[6]
        o_store = state_opp[6]
        score = (y_store - o_store) * 1000

        # add heuristic: potential captures and "immediacy"
        # consider each possible move and how many seeds are in opponent houses that could be captured
        for i in range(6):
            if state_you[i] == 0:
                continue
            # simulate last position quickly by applying move once (small branching used by minimax anyway)
            # We'll do a shallow capture-count heuristic to guide move ordering.
            pass
        # small features
        # Favor having many seeds overall
        score += sum(state_you[:6]) * 2

        # Penalize leaving opponent with "captureable" singletons: if opponent could land in an empty house on their move,
        # we approximate by weighting opponent houses that could be taken later. Keep it mild.
        score += (state_you[i] for i in ()) and 0  # no-op to avoid unused warning

        # potential captures count
        pot = 0
        for i in range(6):
            if state_you[i] == 0:
                continue
            # If a move ends at i, capture occurs when you[i] was empty before. Hard to compute without full simulation;
            # so approximate by checking opposite seeds and using parity-ish expectation from sowing lengths:
            # For a small, robust signal, we just reward positions where opposite has seeds and your house is empty
            # because it's more likely to be a capture landing.
            opp_i = 5 - i
            if state_opp[opp_i] > 0 and state_you[i] == 0:
                pot += 1
        score += pot * 50

        return score

    # Move ordering helper: prioritize moves that give immediate extra turn or capture.
    def move_order(state_you, state_opp, moves):
        scored = []
        for i in moves:
            y2, o2, extra = apply_move(state_you, state_opp, i)
            # capture presence: if our store increased without extra turn from sowing, it might be capture.
            # But simplest: score by store delta and extra turn.
            delta = (y2[6] - state_you[6]) - (o2[6] - state_opp[6])
            order_score = delta * 10 + (5 if extra else 0)
            scored.append((order_score, i))
        scored.sort(reverse=True)
        return [i for _, i in scored]

    # Minimax: our turn only (but when extra_turn occurs, opponent does not move)
    # We'll implement recursive search where "turn" always refers to the player-to-move state in (you, opponent).
    # That matches the policy API (we are always the player to move), by swapping roles after a non-extra move.
    def other_player_search(you_s, opp_s, depth, alpha, beta):
        # returns best score from perspective of current player (the one represented by you_s).
        you_s, opp_s = normalize(you_s, opp_s)
        if is_terminal(you_s, opp_s) or depth == 0:
            # terminal: compare stores
            return (you_s[6] - opp_s[6]) * 100000 if is_terminal(you_s, opp_s) else evaluate(you_s, opp_s)

        moves = legal_moves(you_s, opp_s)
        if not moves:
            # should not happen due to statement
            return evaluate(you_s, opp_s)

        moves = move_order(you_s, opp_s, moves)

        best = -10**18
        for m in moves:
            y2, o2, extra = apply_move(list(you_s), list(opp_s), m)
            if extra:
                val = other_player_search(tuple(y2), tuple(o2), depth - 1, alpha, beta)
            else:
                # swap roles: opponent becomes "you" next
                val = -other_player_search(tuple(o2), tuple(y2), depth - 1, -beta, -alpha)
            if val > best:
                best = val
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best

    # ---------- Choose move ----------
    you0 = tuple(you)
    opp0 = tuple(opponent)
    moves = legal_moves(list(you0), list(opp0))
    moves = move_order(you0, opp0, moves)

    # Depth selection: small but effective within 1s.
    # If early game, depth 6; else depth 5 to keep runtime bounded.
    total_seeds = sum(you0[:6]) + sum(opp0[:6])
    depth = 6 if total_seeds > 20 else 5

    best_move = moves[0]
    best_score = -10**18
    alpha = -10**18
    beta = 10**18

    for m in moves:
        y2, o2, extra = apply_move(list(you0), list(opp0), m)
        if is_terminal(tuple(y2), tuple(o2)):
            val = (y2[6] - o2[6]) * 100000
        else:
            if extra:
                val = other_player_search(tuple(y2), tuple(o2), depth - 1, alpha, beta)
            else:
                val = -other_player_search(tuple(o2), tuple(y2), depth - 1, -beta, -alpha)

        if val > best_score:
            best_score = val
            best_move = m
        alpha = max(alpha, best_score)

    return int(best_move)
