
from functools import lru_cache
from typing import List, Tuple

def policy(you: List[int], opponent: List[int]) -> int:
    """
    Strong heuristic + shallow minimax for standard Kalah (6 houses, 1 store).
    Returns an integer i in [0,5] with you[i] > 0.
    """

    # ----- Game mechanics (simulation) -----
    def move_one(state: Tuple[Tuple[int, ...], Tuple[int, ...]], i: int):
        y = list(state[0])
        o = list(state[1])
        seeds = y[i]
        y[i] = 0

        idx = i
        last_in_store = False
        last_pos = None  # (side, pos): side 0=you,1=opp ; pos 0..5 or store=6

        # sow
        while seeds > 0:
            idx += 1
            side = 0  # 0 means your row, 1 opponent row; overridden by wrap logic
            # The linear sowing order cycles through:
            # you[i+1..5], you store(6), opponent[0..5], then you[0..5] ...
            # We'll implement with explicit stepping.
            if idx <= 5:
                y[idx] += 1
                last_pos = (0, idx)
            elif idx == 6:
                y[6] += 1
                last_pos = (0, 6)
                last_in_store = True
            elif idx <= 11:
                # opponent houses 0..5
                j = idx - 7  # when idx=7 -> opponent[0]
                o[j] += 1
                last_pos = (1, j)
            else:
                # wrap to your houses
                k = idx - 12  # when idx=12 -> you[0]
                if k < 0 or k > 5:
                    # Safety; should not happen
                    k = k % 6
                y[k] += 1
                last_pos = (0, k)

            seeds -= 1
            # wrap idx into next cycle range
            if idx >= 12:
                idx -= 12  # keep within 0..11-ish, but logic above assumes comparisons vs 5/6/11

        # capture
        # last seed lands in your house i (0..5)
        if last_pos is not None and last_pos[0] == 0 and last_pos[1] in range(0, 6):
            landed = last_pos[1]
            # It was empty before the drop: to check, we need to know if it was 0 before sowing.
            # We can infer because y[landed] became >0 due to this move and was set to 0 only at start for chosen i.
            # But landed could be i=chosen or other; only chosen i was forced to 0 initially.
            # Correct approach: track emptiness before sowing.
        return y, o, last_pos

    def apply_move(y0: Tuple[int, ...], o0: Tuple[int, ...], i: int):
        y = list(y0)
        o = list(o0)
        seeds = y[i]
        assert seeds > 0

        was_empty = y[:]  # we just need emptiness of all houses before the sow
        # Only capture depends on whether the landing house was empty before the move.
        # So we record those six house values.
        empty_before = [was_empty[k] == 0 for k in range(6)]

        y[i] = 0

        # Sow
        # We'll use a position pointer in linear cycle of length 13 excluding opponent store:
        # order: you[0..5], youStore, opponent[0..5]  => total 6+1+6 = 13.
        # But sow starts from i, and we place seeds after removing from i, so first placed at i+1.
        # We'll map linear index t in [0..12] to location:
        # 0..5 => you[0..5], 6 => youStore, 7..12 => opponent[0..5] with opponent_idx=t-7
        def place(t: int):
            if t <= 5:
                y[t] += 1
                return (0, t)
            elif t == 6:
                y[6] += 1
                return (0, 6)
            else:
                j = t - 7
                o[j] += 1
                return (1, j)

        # linear index for chosen i:
        # chosen i corresponds to t=i in 0..5
        t = i
        last = None
        while seeds > 0:
            t = (t + 1) % 13
            last = place(t)
            seeds -= 1

        # Determine extra turn
        extra = (last is not None and last[0] == 0 and last[1] == 6)

        # Capture rule
        # If last seed lands in your house (0..5) and that house was empty before
        # and opposite house has seeds.
        if last is not None and last[0] == 0 and last[1] in range(0, 6):
            landed = last[1]
            if empty_before[landed] and o[5 - landed] > 0:
                captured = y[landed] + o[5 - landed]
                y[landed] = 0
                o[5 - landed] = 0
                y[6] += captured

        return tuple(y), tuple(o), extra

    def is_terminal(y: Tuple[int, ...], o: Tuple[int, ...]) -> bool:
        return all(y[k] == 0 for k in range(6)) or all(o[k] == 0 for k in range(6))

    def collect_end(y: Tuple[int, ...], o: Tuple[int, ...]):
        # when game ends, other player moves remaining seeds into their store
        # Determine who is empty.
        y_list = list(y)
        o_list = list(o)
        if all(y_list[k] == 0 for k in range(6)):
            # you empty => opponent gets remaining
            for k in range(6):
                o_list[6] += o_list[k]
                o_list[k] = 0
        else:
            # opponent empty => you gets remaining
            for k in range(6):
                y_list[6] += y_list[k]
                y_list[k] = 0
        return tuple(y_list), tuple(o_list)

    def legal_moves(y: Tuple[int, ...]) -> List[int]:
        return [i for i in range(6) if y[i] > 0]

    # ----- Evaluation -----
    def opposite_index(k: int) -> int:
        return 5 - k

    def evaluate(y: Tuple[int, ...], o: Tuple[int, ...]) -> int:
        # Store difference is primary.
        diff = y[6] - o[6]

        # Add potential capture immediate: if a move could land in an empty house and capture.
        # We'll approximate by current stones + distribution.
        capture_potential = 0
        for k in range(6):
            if y[k] == 0 and o[opposite_index(k)] > 0:
                # some move could potentially land here; weight modestly
                capture_potential += 1

        # Extra-turn tendency: more seeds generally leads to store landings; use total seeds in houses.
        my_houses = sum(y[:6])
        opp_houses = sum(o[:6])

        # Mobility: number of legal moves
        mob = sum(1 for i in range(6) if y[i] > 0)

        # Risk: if opponent has many stones facing your empties
        risk = 0
        for k in range(6):
            if y[k] == 0:
                risk += o[opposite_index(k)]

        # Weighted sum (tuned heuristically)
        return (diff * 100) + (capture_potential * 8) + (mob * 2) + (my_houses - opp_houses) - (risk * 1)

    # ----- Shallow minimax (depth 2 ply, with extra-turn handling) -----
    # We simulate only one move each, but if we get an extra turn we keep the turn for "you" in rollout.
    def negamax(y: Tuple[int, ...], o: Tuple[int, ...], depth: int) -> int:
        if depth == 0 or is_terminal(y, o):
            if is_terminal(y, o):
                y2, o2 = collect_end(y, o)
                return evaluate(y2, o2)
            return evaluate(y, o)

        moves = legal_moves(y)
        if not moves:
            # policy not called in this case normally; still handle.
            y2, o2 = collect_end(y, o)
            return evaluate(y2, o2)

        best = -10**18
        for m in moves:
            y2, o2, extra = apply_move(y, o, m)
            if is_terminal(y2, o2):
                y3, o3 = collect_end(y2, o2)
                val = evaluate(y3, o3)
            else:
                if extra:
                    # we move again (same player perspective)
                    val = negamax(y2, o2, depth - 1)
                else:
                    # opponent's turn: swap perspective (negamax)
                    val = -negamax(o2, y2, depth - 1)
            if val > best:
                best = val
        return best

    # ----- Choose best move with immediate win check -----
    y0 = tuple(you)
    o0 = tuple(opponent)

    moves = legal_moves(y0)
    # Prefer deterministic tie-breaking: center-out (2,3,1,4,0,5)
    order = sorted(moves, key=lambda x: abs(x - 2.5))
    best_move = order[0]
    best_val = -10**18

    for m in order:
        y1, o1, extra = apply_move(y0, o0, m)

        # Immediate terminal preference
        if is_terminal(y1, o1):
            y2, o2 = collect_end(y1, o1)
            val = evaluate(y2, o2) + (1000 if y2[6] > o2[6] else 0)
        else:
            # Depth-2: your move + opponent response (or your extra turn)
            if extra:
                val = negamax(y1, o1, 1)  # you already used 1 ply
            else:
                val = -negamax(o1, y1, 1)

        if val > best_val:
            best_val = val
            best_move = m

    return best_move
