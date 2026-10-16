
from __future__ import annotations

import math
import functools
from typing import List, Tuple

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Returns a legal move i in [0..5] with you[i] > 0.
    Uses depth-limited alpha-beta minimax with heuristics.
    """
    # ---------- Utilities to simulate Kalah ----------

    def is_terminal(state: Tuple[Tuple[int, ...], Tuple[int, ...]]) -> bool:
        y, o = state
        return all(x == 0 for x in y[:6]) or all(x == 0 for x in o[:6])

    def collect_remaining_to_store(y: List[int], o: List[int]) -> Tuple[List[int], List[int]]:
        # If you are out of seeds, opponent sweeps to their store; if opponent is out, you sweep.
        if all(x == 0 for x in y[:6]):
            o[6] += sum(o[:6])
            for i in range(6):
                o[i] = 0
        elif all(x == 0 for x in o[:6]):
            y[6] += sum(y[:6])
            for i in range(6):
                y[i] = 0
        return y, o

    def legal_moves(y: List[int]) -> List[int]:
        return [i for i in range(6) if y[i] > 0]

    def apply_move(
        y_in: List[int], o_in: List[int], i: int
    ) -> Tuple[List[int], List[int], bool]:
        """
        Apply move for player-to-move (currently you).
        Returns (new_y, new_o, extra_turn_for_current_player).
        Note: It assumes i is legal for current player.
        """
        y = y_in[:]  # current player's side
        o = o_in[:]
        seeds = y[i]
        y[i] = 0

        cur_side = "you"
        pos_index = i  # we will start sowing at next position

        # Distribute one-by-one across the cyclic board skipping opponent store.
        while seeds > 0:
            # advance to next pit/store
            if cur_side == "you":
                # move across you pits and store
                if pos_index < 5:
                    pos_index += 1
                else:
                    pos_index = 6  # store
                # If we hit store, skip handled naturally (we don't skip our store)
                if pos_index == 6:
                    cur_side = "opp"
                    pos_index = -1  # so that next increment sets opponent pit 0
            else:
                # opponent side: pits 0..5; skip opponent store
                if pos_index < 5:
                    pos_index += 1
                # cur_side switches back after opponent pit 5 -> you pit 0
                if pos_index == 5:
                    # this was the last opponent pit; next would go to your pit 0
                    cur_side = "you"
                    pos_index = 0

                    # But careful: after switching, the "next" placement isn't happening yet.
                    # We'll place the current seed before switching.
                    # So do placement logic below before adjusting.
                    # Here we only adjust turn for next advance; to keep it correct, we won't
                    # change cur_side/pos_index earlier.
                    # We'll rewrite for clarity by using a deterministic ring mapping.
                    pass

        # The above approach is error-prone; use a ring-mapping method instead.

    def apply_move_ring(
        y_in: List[int], o_in: List[int], i: int
    ) -> Tuple[List[int], List[int], bool]:
        y = y_in[:]
        o = o_in[:]
        seeds = y[i]
        y[i] = 0

        # Create a ring of 14 positions excluding opponent store:
        # Index mapping for sowing order:
        # 0..5: your pits 0..5
        # 6: your store
        # 7..12: opponent pits 0..5
        # (opponent store excluded)
        #
        # We sow starting from position right after i.
        # The linear order is: your pit (i+1..5), your store, opponent pit 0..5, wrap to your pit 0..5.
        ring = list(range(13))  # positions 0..12

        def place(pos: int, amount: int = 1):
            # pos 0..5 -> y[pos]
            # pos 6 -> y[6]
            # pos 7..12 -> o[pos-7]
            if 0 <= pos <= 5:
                y[pos] += amount
            elif pos == 6:
                y[6] += amount
            else:
                o[pos - 7] += amount

        # Starting position just after i on the ring
        start = i + 1
        if start <= 5:
            pos = start
        else:
            # i=5 -> next is your store (pos 6)
            # if somehow >5 -> handle by modular arithmetic on ring length 13
            pos = (i + 1) % 13

        pos = (i + 1) % 13  # ring length 13 (since opponent store removed)
        # Determine initial empty status for capture: capture occurs only if last seed lands
        # in your pit (0..5) and it was empty before landing.
        # We'll need to know where last seed lands.
        last_pos = None

        while seeds > 0:
            last_pos = pos
            place(pos, 1)
            seeds -= 1
            pos = (pos + 1) % 13

        # Extra turn if last seed lands in your store (pos 6)
        extra_turn = (last_pos == 6)

        # Capture: last seed in your house (0..5) and that house was empty before drop.
        # Since we already placed the last seed, we can infer "emptiness before" by checking
        # whether y[last_pos] became 1 from 0 at that time. But it could also be >1 if
        # multiple seeds landed there (only possible if sowing loops). Then capture rules
        # still require "was empty before the drop"—which means count was 0 before placing
        # the final seed, i.e., after the distribution excluding last seed.
        #
        # Simpler: replay distribution but stop before last placement to test.
        if last_pos is not None and 0 <= last_pos <= 5:
            # Determine where the last seed landed: in your pit k=last_pos.
            k = last_pos
            # Re-simulate to know y count before last seed:
            y2 = y_in[:]
            o2 = o_in[:]
            seeds2 = y2[i]
            y2[i] = 0
            pos2 = (i + 1) % 13
            # number of steps before last placement = original seeds - 1
            steps_before_last = seeds2 - 1
            for _ in range(steps_before_last):
                # place without caring
                if 0 <= pos2 <= 5:
                    y2[pos2] += 1
                elif pos2 == 6:
                    y2[6] += 1
                else:
                    o2[pos2 - 7] += 1
                pos2 = (pos2 + 1) % 13
            # pos2 is where last seed lands
            # Check capture condition:
            if pos2 == k:
                was_empty = (y2[k] == 0)
                if was_empty:
                    opp_index = 5 - k
                    if o2[opp_index] > 0:
                        captured = o2[opp_index]
                        # After capture, last seed remains in k then whole pit captured.
                        # Total seeds in k after last seed is 1 (since was empty).
                        # Remove opponent seeds and move to store.
                        y_after = y2
                        o_after = o2
                        # Place last seed then capture effect:
                        y_after[k] += 1
                        # Now capture:
                        y_after[6] += y_after[k] + o_after[opp_index]
                        y_after[k] = 0
                        o_after[opp_index] = 0
                        y, o = y_after, o_after

        return y, o, extra_turn

    def evaluate(y: List[int], o: List[int]) -> float:
        # Primary: store difference
        store_diff = y[6] - o[6]

        # Seeds on pits and potential: add small terms
        pit_diff = sum(y[:6]) - sum(o[:6])

        # Threat/capture potential heuristic: count immediate captures available for current player
        # after making a move? We'll approximate by comparing opposite pairs that are non-empty.
        capture_threat = 0
        for idx in range(6):
            # If we could land into idx, we'd capture opposite if non-empty.
            # Hard to know landing without simulation, but we can reward having seeds in pits
            # whose opposite has seeds (potential captures by landing there).
            if y[idx] > 0 and o[5 - idx] > 0:
                capture_threat += 1

        # Mobility: more legal moves generally good (tempo)
        mobility = sum(1 for x in y[:6] if x > 0)

        # Safety: penalize leaving opponent pit that can capture us easily.
        # Approximate by rewarding having fewer "exposed" seeds facing opponent pits.
        exposure_penalty = 0
        for idx in range(6):
            if y[idx] > 0 and o[5 - idx] == 0:
                exposure_penalty += y[idx]

        return (
            20.0 * store_diff
            + 1.0 * pit_diff
            + 6.0 * capture_threat
            + 0.8 * mobility
            - 0.15 * exposure_penalty
        )

    # ---------- Minimax with alpha-beta ----------

    def alpha_beta(
        y: List[int],
        o: List[int],
        depth: int,
        alpha: float,
        beta: float,
    ) -> Tuple[float, int]:
        """
        Returns (best_value_from_current_player_perspective, best_move_index).
        Current player is the one represented by y.
        """
        if is_terminal((tuple(y), tuple(o))):
            y_fin, o_fin = collect_remaining_to_store(y[:], o[:])
            if y_fin[6] > o_fin[6]:
                return 1e9, -1
            elif y_fin[6] < o_fin[6]:
                return -1e9, -1
            else:
                return 0.0, -1

        if depth == 0:
            return evaluate(y, o), -1

        moves = legal_moves(y)
        if not moves:
            # should not happen per prompt
            y_fin, o_fin = collect_remaining_to_store(y[:], o[:])
            return evaluate(y_fin, o_fin), -1

        # Move ordering: prioritize captures/extra-turn likely.
        def move_score(i: int) -> int:
            # fast simulate one move to see if it grants extra turn
            y2, o2, extra = apply_move_ring(y, o, i)
            score = 0
            # prioritize store gain and extra turn
            score += int(1000 * (y2[6] - y[6]))
            if extra:
                score += 2000
            # prioritize if opponent pit opposite became empty (possible capture)
            # or if store increased a lot
            score += 50 * (o[6] - o2[6])
            return score

        moves.sort(key=move_score, reverse=True)

        best_move = moves[0]
        best_val = -math.inf

        for m in moves:
            y2, o2, extra = apply_move_ring(y, o, m)

            if extra:
                # Current player gets another move: same perspective, depth-1
                val, _ = alpha_beta(y2, o2, depth - 1, alpha, beta)
            else:
                # Turn passes: swap roles. Opponent becomes "you" in next call.
                val_op, _ = alpha_beta(o2, y2, depth - 1, -beta, -alpha)
                val = -val_op

            if val > best_val:
                best_val = val
                best_move = m
            alpha = max(alpha, best_val)
            if alpha >= beta:
                break

        return best_val, best_move

    # ---------- Adaptive depth selection ----------
    total_seeds = sum(you[:6]) + sum(opponent[:6])  # stores don't affect sowing
    # Deeper when smaller to improve exactness, but keep fast.
    if total_seeds <= 24:
        depth = 7
    elif total_seeds <= 36:
        depth = 6
    else:
        depth = 5

    # Small tweak if we have few moves -> deeper
    if sum(1 for x in you[:6] if x > 0) <= 2:
        depth += 1
    depth = min(depth, 8)

    # Run search
    _, best = alpha_beta(you[:], opponent[:], depth=depth, alpha=-math.inf, beta=math.inf)

    # Ensure legality
    if best is None or best < 0 or you[best] <= 0:
        # Fallback: choose the move maximizing immediate store gain
        best = max([i for i in range(6) if you[i] > 0],
                   key=lambda i: apply_move_ring(you, opponent, i)[0][6] - you[6])

    return int(best)
