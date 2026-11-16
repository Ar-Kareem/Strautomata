
from functools import lru_cache

def policy(you: list[int], opponent: list[int]) -> int:
    # --------- Helpers: game mechanics ----------
    def legal_moves(state_you, state_opp):
        return [i for i in range(6) if state_you[i] > 0]

    def apply_move(state_you, state_opp, i):
        """Return (new_you, new_opp) after sow/capture/extra-turn.
        Note: caller can decide turn-handling by checking extra flag.
        """
        y = state_you[:]  # length 7
        o = state_opp[:]   # length 7
        seeds = y[i]
        y[i] = 0

        idx = i + 1  # next position in sowing order relative to y
        last_was_store = False
        last_pos = None  # ('you',k) or ('opp',k)

        while seeds > 0:
            # We traverse the cycle: you[0..5], store skipped for opp[6]
            # Order described in prompt.
            if idx <= 6:
                # idx in 0..6 for you positions
                if idx <= 5:
                    y[idx] += 1
                    last_pos = ('you', idx)
                else:
                    y[6] += 1
                    last_pos = ('you', 6)
                    last_was_store = True
                idx += 1
            else:
                # After you[6], we go through opponent[0..5], skipping opponent store
                # idx=7 -> opponent[0], ..., idx=12 -> opponent[5], idx=13 -> you[0]
                opp_index = idx - 7  # 0..5
                if 0 <= opp_index <= 5:
                    o[opp_index] += 1
                    last_pos = ('opp', opp_index)
                idx += 1

            seeds -= 1
            if idx == 13:  # back to you[0]
                idx = 0

        # Determine if extra move
        extra = (last_pos == ('you', 6))

        # Capture rule
        # If last seed lands in our house k (0..5) and that house was empty before the drop
        if last_pos[0] == 'you' and 0 <= last_pos[1] <= 5:
            k = last_pos[1]
            # But we need to know if k was empty before drop.
            # We can infer: y[k] was 0 before we placed seeds, except it might have received seeds earlier.
            # Since we set y[i]=0 and sow proceeds, k could be visited earlier only if i<k and wrap.
            # Easiest correct way: recompute using simulation with tracking of "was empty".
        # Re-simulate with tracking for correctness.
        # (Still fast: only up to small depth used later.)
        y = state_you[:]
        o = state_opp[:]
        seeds = y[i]
        y[i] = 0

        idx = i + 1
        last_pos = None
        while seeds > 0:
            if idx <= 6:
                if idx <= 5:
                    last_pos = ('you', idx)
                    y[idx] += 1
                else:
                    last_pos = ('you', 6)
                    y[6] += 1
                idx += 1
            else:
                opp_index = idx - 7
                if 0 <= opp_index <= 5:
                    last_pos = ('opp', opp_index)
                    o[opp_index] += 1
                idx += 1
            seeds -= 1
            if idx == 13:
                idx = 0

        extra = (last_pos == ('you', 6))

        if last_pos[0] == 'you' and 0 <= last_pos[1] <= 5:
            k = last_pos[1]
            # Was empty before the last seed drop?
            # That means after sow but before capture, the last landing made it non-empty.
            # If we look at y[k] now, it is at least 1. For capture, it must be exactly 1
            # AND it must have been 0 before last seed. Because we don't land twice on same house at the final step,
            # capture condition simplifies to y[k]==1 now and opposite has seeds.
            if y[k] == 1 and o[5 - k] > 0:
                captured = o[5 - k] + y[k]
                o[5 - k] = 0
                y[k] = 0
                y[6] += captured

        return y, o, extra

    def terminal_check(state_you, state_opp):
        # Game ends when one player's houses are all zero
        if all(x == 0 for x in state_you[:6]):
            # opponent collects remaining
            new_o = state_opp[:]
            rem = sum(new_o[:6])
            new_o = new_o[:]  # copy
            new_o[6] += rem
            new_o[:6] = [0] * 6
            return True, state_you, new_o
        if all(x == 0 for x in state_opp[:6]):
            new_y = state_you[:]
            rem = sum(new_y[:6])
            new_y[6] += rem
            new_y[:6] = [0] * 6
            return True, new_y, state_opp
        return False, state_you, state_opp

    def score(state_you, state_opp):
        """Heuristic score from our perspective."""
        # Large weight for store difference; plus extra shaping for captures and threats.
        # store diff dominates.
        y_store = state_you[6]
        o_store = state_opp[6]
        diff = y_store - o_store

        # Count our potential captures (moves that would land in an empty pit and capture)
        pot_cap = 0
        safe = 0
        for i in range(6):
            if state_you[i] == 0:
                continue
            # simulate landing only to see if capture happens on that move
            y2, o2, extra = apply_move(state_you, state_opp, i)
            # capture detection: if our store increased compared to original
            if y2[6] > y_store:
                pot_cap += 1

            # "safe pit" idea: if move ends in our store or ends away from giving opponent captures
            # We'll approximate by checking whether opponent has any capture move afterward.
            # (Cheap: compute whether there exists a capturing move for opponent.)
            # We only care about non-terminal after opponent's turn.
            # If we got extra, opponent won't move now.
            if extra:
                continue
            # opponent to move on (o2, y2) relative perspective, but their pits are o2[0..5].
            opp_cap_moves = 0
            for j in range(6):
                if o2[j] == 0:
                    continue
                # simulate opponent move capturing
                o3, y3, extra2 = apply_move(o2, y2, j)
                # relative score: their store is o3[6], ours is y3[6]
                if o3[6] > o2[6]:
                    opp_cap_moves += 1
            if opp_cap_moves == 0:
                safe += 1

        mobility = sum(1 for x in state_you[:6] if x > 0)
        opp_mobility = sum(1 for x in state_opp[:6] if x > 0)

        # Weighting
        return (diff * 1000) + (pot_cap * 80) + (safe * 20) + (mobility - opp_mobility) * 8

    # --------- Minimax with alpha-beta ----------
    # We treat "extra turn" as same player continuing by swapping only when no extra.
    def negamax(state_you, state_opp, depth, alpha, beta):
        # Return best value from our perspective.
        term, y1, o1 = terminal_check(state_you, state_opp)
        if term or depth == 0:
            return score(y1, o1)

        best = -10**18
        moves = legal_moves(state_you, state_opp)
        # Move ordering: captures and store-ending moves first
        y_store = state_you[6]
        def move_key(i):
            y2, o2, extra = apply_move(state_you, state_opp, i)
            # prefer captures and extra turns
            cap_gain = y2[6] - y_store
            end_store = 1 if extra else 0
            # also prefer creating advantage heuristic quickly
            return (cap_gain * 1000) + (end_store * 500) + (y2[6] - o2[6])

        moves.sort(key=move_key, reverse=True)

        for i in moves:
            y2, o2, extra = apply_move(state_you, state_opp, i)
            if extra:
                val = negamax(y2, o2, depth - 1, alpha, beta)
            else:
                # Switch perspective: opponent becomes "us"
                val = -negamax(o2, y2, depth - 1, -beta, -alpha)

            if val > best:
                best = val
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best

    # --------- Choose move ----------
    moves = legal_moves(you, opponent)
    # Depth adapts to branching and remaining seeds
    total_seeds = sum(you[:6]) + sum(opponent[:6])
    if total_seeds > 80:
        depth = 4
    elif total_seeds > 40:
        depth = 5
    else:
        depth = 6

    # Quick tactical: if any capture exists, take the best one by immediate score/extra.
    y0, o0 = you[:], opponent[:]
    base_store = you[6]
    best_i = None
    best_tact = -10**18
    for i in moves:
        y2, o2, extra = apply_move(y0, o0, i)
        gain = (y2[6] - base_store) * 500 + (y2[6] - o2[6]) * 10 + (1000 if extra else 0)
        # If capture happens, give it massive priority
        if y2[6] > base_store:
            if gain > best_tact:
                best_tact = gain
                best_i = i

    if best_i is not None:
        return best_i

    # Otherwise, minimax search
    alpha = -10**18
    beta = 10**18
    best_val = -10**18
    best_move = moves[0]
    for i in moves:
        y2, o2, extra = apply_move(you, opponent, i)
        if extra:
            val = negamax(y2, o2, depth - 1, alpha, beta)
        else:
            val = -negamax(o2, y2, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = i

    return best_move
