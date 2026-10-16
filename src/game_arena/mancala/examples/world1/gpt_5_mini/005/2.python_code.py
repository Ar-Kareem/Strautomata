
import time
from typing import List, Tuple, Dict

# Policy entry point
def policy(you: List[int], opponent: List[int]) -> int:
    """
    Choose a house index (0..5) where you[i] > 0.
    Uses negamax with alpha-beta and iterative deepening.
    """
    # Copy inputs to avoid accidental mutation
    you = list(you)
    opponent = list(opponent)

    start_time = time.time()
    TIME_LIMIT = 0.95  # seconds, leave some margin

    # Precompute positions cycle (13 slots: your 6 houses, your store, opponent 6 houses)
    positions = [('you', i) for i in range(6)] + [('you', 6)] + [('opp', i) for i in range(6)]
    CYCLE_LEN = len(positions)  # 13

    # Helper: check legal moves
    legal_moves = [i for i in range(6) if you[i] > 0]
    if not legal_moves:
        # Shouldn't happen per problem statement
        return 0

    # Simulation of a move on the current player's side "you" against "opponent"
    def simulate_move(you_state: List[int], opp_state: List[int], move: int) -> Tuple[List[int], List[int], bool, bool]:
        """
        Apply move from you_state[move].
        Returns (new_you, new_opp, extra_move, game_over)
        """
        y = you_state.copy()
        o = opp_state.copy()

        seeds = y[move]
        y[move] = 0

        # find start index in cycle after ('you', move)
        try:
            idx = positions.index(('you', move))
        except ValueError:
            idx = 0
        start = (idx + 1) % CYCLE_LEN

        last_slot = None
        # Distribute seeds one by one into the cycle
        for k in range(seeds):
            slot = positions[(start + k) % CYCLE_LEN]
            last_slot = slot
            side, pos = slot
            if side == 'you':
                y[pos] += 1
            else:
                o[pos] += 1

        extra_move = (last_slot == ('you', 6))

        # Capture rule: if last seed landed in your house 0..5, and it was empty before the drop,
        # and opposite opponent[5 - i] > 0, then capture both into your store.
        game_over = False
        if last_slot is not None:
            side, pos = last_slot
            if side == 'you' and 0 <= pos <= 5:
                # We need to check if the house was empty before the last seed was placed.
                # After placement, y[pos] >= 1. It was empty before if now it's 1 and the placement was the only (i.e., was 0 before).
                if y[pos] == 1:
                    opp_index = 5 - pos
                    if o[opp_index] > 0:
                        captured = o[opp_index] + y[pos]
                        y[6] += captured
                        y[pos] = 0
                        o[opp_index] = 0

        # Game end check: if either side has all zeros in houses 0..5
        if all(v == 0 for v in y[:6]) or all(v == 0 for v in o[:6]):
            # sweep remaining seeds into the corresponding store
            if not all(v == 0 for v in y[:6]):
                # opponent empty -> you sweep your remaining
                y[6] += sum(y[:6])
                for i in range(6):
                    y[i] = 0
            if not all(v == 0 for v in o[:6]):
                # you empty -> opponent sweeps
                o[6] += sum(o[:6])
                for i in range(6):
                    o[i] = 0
            game_over = True

        return y, o, extra_move, game_over

    # Evaluation function from the perspective of the current 'you' (i.e., positive means good for current side)
    def evaluate(you_state: List[int], opp_state: List[int]) -> int:
        # Primary: store difference
        store_diff = you_state[6] - opp_state[6]
        # Secondary: seed difference on houses, weighted
        house_diff = sum(you_state[:6]) - sum(opp_state[:6])
        # Extra heuristic: potential extra moves and captures are implicitly reflected by seeds distribution
        return store_diff * 1000 + house_diff  # prioritize store heavily (scaled)

    # Transposition table: key -> (depth_reached, value)
    tt: Dict[Tuple[Tuple[int, ...], Tuple[int, ...], int], int] = {}

    # Negamax with alpha-beta pruning
    def negamax(you_state: List[int], opp_state: List[int], depth: int, alpha: int, beta: int, start_time: float) -> int:
        # Time cutoff
        if time.time() - start_time > TIME_LIMIT:
            raise TimeoutError()

        # Terminal or depth 0
        if all(v == 0 for v in you_state[:6]) or all(v == 0 for v in opp_state[:6]):
            # Game over; evaluation is final store difference for current you
            return you_state[6] - opp_state[6]

        if depth <= 0:
            return evaluate(you_state, opp_state)

        key = (tuple(you_state), tuple(opp_state), depth)
        if key in tt:
            return tt[key]

        value = -10**9
        # Move ordering: try moves that give extra move first and those with larger immediate gain
        moves = [i for i in range(6) if you_state[i] > 0]
        # quick heuristic ordering
        scored_moves = []
        for m in moves:
            # simulate just to get ordering metrics cheaply (no deepcopy overhead too large? we simulate)
            y2, o2, extra, _ = simulate_move(you_state, opp_state, m)
            # heuristic: prefer extra moves and higher immediate store gain
            delta_store = y2[6] - you_state[6]
            score = (1000 if extra else 0) + delta_store * 100 + sum(y2[:6]) - sum(o2[:6])
            scored_moves.append((score, m))
        scored_moves.sort(reverse=True)
        ordered_moves = [m for _, m in scored_moves]

        for m in ordered_moves:
            y2, o2, extra, game_over = simulate_move(you_state, opp_state, m)
            if game_over:
                val = y2[6] - o2[6]
            else:
                if extra:
                    # same player moves again: don't swap, value is from this player's perspective
                    val = negamax(y2, o2, depth - 1, alpha, beta, start_time)
                else:
                    # opponent's turn: swap and negate
                    val = -negamax(o2, y2, depth - 1, -beta, -alpha, start_time)
            if val > value:
                value = val
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        tt[key] = value
        return value

    best_move = legal_moves[0]
    best_score = -10**9

    # Iterative deepening
    max_depth_limit = 14  # safety upper bound
    try:
        for depth in range(1, max_depth_limit + 1):
            # small timeout check
            if time.time() - start_time > TIME_LIMIT:
                break

            current_best = None
            current_best_score = -10**9

            # Order top-level moves similarly as in negamax ordering
            moves = [i for i in range(6) if you[i] > 0]
            scored_moves = []
            for m in moves:
                y2, o2, extra, _ = simulate_move(you, opponent, m)
                delta_store = y2[6] - you[6]
                score = (1000 if extra else 0) + delta_store * 100 + sum(y2[:6]) - sum(o2[:6])
                scored_moves.append((score, m))
            scored_moves.sort(reverse=True)
            ordered_moves = [m for _, m in scored_moves]

            for m in ordered_moves:
                # time check
                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutError()
                y2, o2, extra, game_over = simulate_move(you, opponent, m)
                if game_over:
                    val = y2[6] - o2[6]
                else:
                    if extra:
                        val = negamax(y2, o2, depth - 1, -10**9, 10**9, start_time)
                    else:
                        val = -negamax(o2, y2, depth - 1, -10**9, 10**9, start_time)
                # track best (value is from current side's perspective)
                if val > current_best_score or (val == current_best_score and (current_best is None or m < current_best)):
                    current_best_score = val
                    current_best = m

            # if a move found at this depth, update best_move
            if current_best is not None:
                best_move = current_best
                best_score = current_best_score

            # small safety: if score is a sure win (large margin) we can stop early
            if abs(best_score) > 100000:  # effectively decisive (since we scaled stores by 1000)
                break

    except TimeoutError:
        # time ran out, fall back to best_move found so far
        pass
    except Exception:
        # any unexpected error: ensure we still return a legal move
        pass

    # final safety: ensure chosen move is legal
    if not (0 <= best_move <= 5 and you[best_move] > 0):
        for i in range(6):
            if you[i] > 0:
                return i
        return 0

    return best_move


# For simple local testing (will not be executed by grader, kept for completeness)
if __name__ == "__main__":
    # Example starting position: 4 seeds in each house (standard)
    you = [4, 4, 4, 4, 4, 4, 0]
    opp = [4, 4, 4, 4, 4, 4, 0]
    move = policy(you, opp)
    print("Selected move:", move)
