
# Kalah move-selection policy
# Returns an index 0..5 (a non-empty house) for the move to play.
# Implements rules: sowing, skipping opponent store, captures, extra moves, and end-game.
# Uses depth-limited alpha-beta minimax with a simple evaluation heuristic.

from math import inf
from typing import List, Tuple

def policy(you: List[int], opponent: List[int]) -> int:
    # Parameters: adjust depth as needed for speed/strength tradeoff
    MAX_DEPTH = 8

    # Copy inputs to avoid accidental mutation
    you = you[:]  # type: ignore
    opponent = opponent[:]  # type: ignore

    def legal_moves(side: List[int]) -> List[int]:
        return [i for i in range(6) if side[i] > 0]

    # Simulate a move for the side designated as "you_side" (the side to move).
    # Returns (new_you_side, new_opp_side, extra_turn_bool, game_over_bool)
    def simulate_move(you_side: List[int], opp_side: List[int], move: int) -> Tuple[List[int], List[int], bool, bool]:
        you_s = you_side[:]  # local copies
        opp_s = opp_side[:]
        seeds = you_s[move]
        you_s[move] = 0

        # Define the sowing cycle excluding opponent's store
        cycle = []
        for i in range(6):
            cycle.append(('you', i))
        cycle.append(('you', 6))  # your store
        for i in range(6):
            cycle.append(('opponent', i))
        cycle_len = len(cycle)

        # Find start position index (the chosen house)
        start_idx = None
        for idx, p in enumerate(cycle):
            if p == ('you', move):
                start_idx = idx
                break
        pos = start_idx

        # Sow seeds one by one
        for s in range(seeds):
            pos = (pos + 1) % cycle_len
            side, idx = cycle[pos]
            if side == 'you':
                if idx == 6:
                    you_s[6] += 1
                else:
                    you_s[idx] += 1
            else:
                opp_s[idx] += 1

        last_side, last_idx = cycle[pos]
        extra = (last_side == 'you' and last_idx == 6)

        # Capture rule: last seed landed in your empty house (0..5) and opposite has seeds
        if last_side == 'you' and 0 <= last_idx <= 5:
            # If you_s[last_idx] == 1 then it was empty before placing the last seed
            if you_s[last_idx] == 1:
                opp_idx = 5 - last_idx
                if opp_s[opp_idx] > 0:
                    captured = you_s[last_idx] + opp_s[opp_idx]
                    you_s[last_idx] = 0
                    opp_s[opp_idx] = 0
                    you_s[6] += captured

        # Check end game: if one side has all houses empty, collect remaining seeds on the other side
        if sum(you_s[:6]) == 0:
            # opponent collects remaining seeds
            opp_s[6] += sum(opp_s[:6])
            for i in range(6):
                opp_s[i] = 0
            return you_s, opp_s, False, True
        if sum(opp_s[:6]) == 0:
            you_s[6] += sum(you_s[:6])
            for i in range(6):
                you_s[i] = 0
            return you_s, opp_s, False, True

        return you_s, opp_s, extra, False

    # Heuristic evaluation: store difference plus a small weight for seeds on the side
    def evaluate(you_s: List[int], opp_s: List[int]) -> float:
        store_diff = you_s[6] - opp_s[6]
        pits_diff = sum(you_s[:6]) - sum(opp_s[:6])
        return float(store_diff) + 0.1 * float(pits_diff)

    # Minimax with alpha-beta pruning.
    # maximizing == True when it's "our" turn (the original caller).
    def minimax(you_s: List[int], opp_s: List[int], depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        # Terminal check
        if sum(you_s[:6]) == 0 or sum(opp_s[:6]) == 0:
            # Final score
            return evaluate(you_s, opp_s)

        if depth == 0:
            return evaluate(you_s, opp_s)

        if maximizing:
            moves = legal_moves(you_s)
            if not moves:
                return evaluate(you_s, opp_s)
            # Move ordering: try higher immediate heuristic first
            scored_moves = []
            for m in moves:
                ny, no, extra, term = simulate_move(you_s, opp_s, m)
                scored_moves.append((evaluate(ny, no), m))
            scored_moves.sort(reverse=True)
            best = -inf
            for _, m in scored_moves:
                ny, no, extra, term = simulate_move(you_s, opp_s, m)
                if term:
                    val = evaluate(ny, no)
                else:
                    if extra:
                        val = minimax(ny, no, depth - 1, alpha, beta, True)
                    else:
                        val = minimax(ny, no, depth - 1, alpha, beta, False)
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if beta <= alpha:
                    break
            return best
        else:
            # Opponent to move: simulate from opponent perspective (swap roles)
            moves = legal_moves(opp_s)
            if not moves:
                return evaluate(you_s, opp_s)
            # Move ordering for opponent: tries to minimize our evaluation
            scored_moves = []
            for m in moves:
                no, ny, extra, term = simulate_move(opp_s, you_s, m)
                scored_moves.append((evaluate(ny, no), m))
            scored_moves.sort()  # ascending for opponent
            best = inf
            for _, m in scored_moves:
                no, ny, extra, term = simulate_move(opp_s, you_s, m)
                # Note: simulate_move returned (opp_after, you_after, extra, term)
                if term:
                    val = evaluate(ny, no)
                else:
                    if extra:
                        # opponent moves again -> still minimizing
                        val = minimax(ny, no, depth - 1, alpha, beta, False)
                    else:
                        val = minimax(ny, no, depth - 1, alpha, beta, True)
                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if beta <= alpha:
                    break
            return best

    # Top-level: choose best move using minimax
    moves = legal_moves(you)
    if not moves:
        # per problem statement this should not happen, but return a safe default
        return 0

    # Order moves by quick one-step heuristic
    scored = []
    for m in moves:
        ny, no, extra, term = simulate_move(you, opponent, m)
        scored.append((evaluate(ny, no), m))
    scored.sort(reverse=True)

    best_move = scored[0][1]
    best_val = -inf
    for _, m in scored:
        ny, no, extra, term = simulate_move(you, opponent, m)
        if term:
            val = evaluate(ny, no)
        else:
            if extra:
                val = minimax(ny, no, MAX_DEPTH - 1, -inf, inf, True)
            else:
                val = minimax(ny, no, MAX_DEPTH - 1, -inf, inf, False)
        # Prefer larger value, tie-breaker lowest index
        if val > best_val or (val == best_val and m < best_move):
            best_val = val
            best_move = m

    return best_move
