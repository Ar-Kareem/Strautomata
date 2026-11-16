
import time
import random
from typing import Tuple, List

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
INF = float('inf')
WIN_SCORE = 10000          # large enough to dominate any heuristic
LOSE_SCORE = -WIN_SCORE
MAX_DEPTH = 12             # safe upper bound – search stops earlier on time out
TIME_LIMIT = 0.9           # seconds, keep a margin under the 1 s limit

# ----------------------------------------------------------------------
# Core game mechanics
# ----------------------------------------------------------------------
def simulate_move(
    you: Tuple[int, ...], opp: Tuple[int, ...], move: int
) -> Tuple[Tuple[int, ...], Tuple[int, ...], bool]:
    """
    Simulate a move for the player whose perspective is ``you``.
    :param you: 7‑tuple – houses 0‑5 and store (index 6) of the moving player
    :param opp: 7‑tuple – houses and store of the opponent
    :param move: which house (0‑5) to play (must have seeds > 0)
    :return: (new_you, new_opp, extra_move)  (tuples are immutable)
    """
    # Convert to mutable lists for the simulation
    you_list = list(you)
    opp_list = list(opp)

    seeds = you_list[move]
    you_list[move] = 0

    # Flat board representation (13 pits, opponent store is omitted)
    # indices 0‑5: our houses, 6: our store, 7‑12: opponent houses
    flat = you_list[:6] + [you_list[6]] + opp_list[:6]

    start = move                     # the house we are sowing from
    cur = start

    while seeds > 0:
        cur = (cur + 1) % 13
        if cur == start:            # never sow back into the original house
            continue
        flat[cur] += 1
        seeds -= 1

    # Did we finish in our store -> extra move?
    extra_move = (cur == 6)

    # Capture rule (only if the last seed landed in one of our houses)
    if not extra_move and cur < 6:
        # the house must now contain exactly one stone (the one we just dropped)
        if flat[cur] == 1:
            opp_house_idx = 5 - cur
            opp_flat_idx = 7 + opp_house_idx          # location in the flat array
            if flat[opp_flat_idx] > 0:
                captured = flat[opp_flat_idx] + 1      # our stone + opponent's stones
                flat[6] += captured                     # all go to our store
                flat[cur] = 0
                flat[opp_flat_idx] = 0

    # Re‑construct the two 7‑tuples
    new_you_houses = tuple(flat[:6])
    new_your_store = flat[6]
    new_opp_houses = tuple(flat[7:13])
    new_opp_store = opp_list[6]               # opponent store never changes here

    new_you = new_you_houses + (new_your_store,)
    new_opp = new_opp_houses + (new_opp_store,)

    return new_you, new_opp, extra_move


def check_game_end(state: Tuple[Tuple[int, ...], Tuple[int, ...]]
) -> Tuple[Tuple[Tuple[int, ...], Tuple[int, ...]], bool]:
    """
    Apply the Kalah end‑game rule: if one side has no seeds in its houses,
    the other side moves all its remaining house‑seeds into its store.
    Returns the (possibly) updated state and a flag indicating termination.
    """
    you, opp = state
    sum_your = sum(you[:6])
    sum_opp = sum(opp[:6])

    if sum_your == 0 or sum_opp == 0:
        # move remaining seeds to the store of the player that still has them
        your_store = you[6] + (sum_your if sum_opp == 0 else 0)
        opp_store = opp[6] + (sum_opp if sum_your == 0 else 0)

        your_houses = (0,) * 6 if sum_opp == 0 else you[:6]
        opp_houses = (0,) * 6 if sum_your == 0 else opp[:6]

        final_state = (your_houses + (your_store,),
                       opp_houses + (opp_store,))
        return final_state, True
    else:
        return state, False


def is_terminal(state: Tuple[Tuple[int, ...], Tuple[int, ...]]) -> bool:
    """Return True if the game has finished (one side has no house‑seeds)."""
    you, opp = state
    return sum(you[:6]) == 0 or sum(opp[:6]) == 0


def evaluate(state: Tuple[Tuple[int, ...], Tuple[int, ...]]) -> float:
    """
    Heuristic evaluation from the original player's perspective.
    For terminal states the result is a large win/lose/draw constant.
    Otherwise: store difference + 0.5 * house‑seed difference + a small
    bonus for every empty house of ours that faces a non‑empty opponent house
    (potential capture).
    """
    you, opp = state
    your_store, opp_store = you[6], opp[6]

    # Terminal positions
    if is_terminal(state):
        if your_store > opp_store:
            return WIN_SCORE
        if your_store < opp_store:
            return LOSE_SCORE
        return 0.0

    # Non‑terminal heuristic
    sum_your = sum(you[:6])
    sum_opp = sum(opp[:6])
    store_diff = your_store - opp_store
    house_diff = sum_your - sum_opp

    # Bonus for potential captures (empty house opposite a loaded opponent house)
    pot_bonus = 0.0
    for i in range(6):
        if you[i] == 0 and opp[5 - i] > 0:
            pot_bonus += opp[5 - i]   # count the seeds we could capture

    return store_diff + 0.5 * house_diff + 0.3 * pot_bonus


def legal_moves(state: Tuple[Tuple[int, ...], Tuple[int, ...]], player: int) -> List[int]:
    """Return a list of legal house indices for the given player (0 = us, 1 = opponent)."""
    you, opp = state
    pits = you if player == 0 else opp
    return [i for i in range(6) if pits[i] > 0]


def get_child_state(state: Tuple[Tuple[int, ...], Tuple[int, ...]],
                    move: int,
                    player: int
) -> Tuple[Tuple[Tuple[int, ...], Tuple[int, ...]], bool]:
    """
    Apply ``move`` for ``player`` to ``state`` and return the resulting
    (state, extra_move) after the end‑game rule has been applied.
    """
    you, opp = state
    if player == 0:
        new_you, new_opp, extra_move = simulate_move(you, opp, move)
        child_state = (new_you, new_opp)
    else:
        # Opponent move – swap perspective, then swap back
        new_opp_for_opp, new_you_for_opp, extra_move = simulate_move(opp, you, move)
        child_state = (new_you_for_opp, new_opp_for_opp)

    # apply the Kalah “end of game” rule
    final_state, _ = check_game_end(child_state)
    return final_state, extra_move


def minimax(state: Tuple[Tuple[int, ...], Tuple[int, ...]],
            depth: int,
            alpha: float,
            beta: float,
            player: int) -> float:
    """
    Classic alpha‑beta minimax. ``player`` is the side to move
    (0 = our player, 1 = opponent).  Depth decreases by one each ply.
    """
    if depth == 0 or is_terminal(state):
        return evaluate(state)

    if player == 0:                     # Maximising node (our turn)
        value = -INF
        moves = legal_moves(state, 0)
        # Order moves by heuristic value of the child (descending)
        children = []
        for m in moves:
            child_state, extra_move = get_child_state(state, m, 0)
            children.append((m, child_state, extra_move, evaluate(child_state)))
        children.sort(key=lambda x: x[3], reverse=True)

        for _, child_state, extra_move, _ in children:
            nxt = 0 if extra_move else 1
            child_val = minimax(child_state, depth - 1, alpha, beta, nxt)
            value = max(value, child_val)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value

    else:                               # Minimising node (opponent)
        value = INF
        moves = legal_moves(state, 1)
        children = []
        for m in moves:
            child_state, extra_move = get_child_state(state, m, 1)
            children.append((m, child_state, extra_move, evaluate(child_state)))
        children.sort(key=lambda x: x[3])          # worst for us first

        for _, child_state, extra_move, _ in children:
            nxt = 1 if extra_move else 0
            child_val = minimax(child_state, depth - 1, alpha, beta, nxt)
            value = min(value, child_val)
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value


def search_at_depth(state: Tuple[Tuple[int, ...], Tuple[int, ...]],
                    depth: int,
                    start_time: float) -> Tuple[int, float]:
    """
    Search the current position with a fixed depth.  Returns the best move
    and its backed‑up value.  If time runs out before any child is examined,
    the function may return (None, -∞).
    """
    moves = legal_moves(state, 0)
    if not moves:
        # Should never happen (no legal move – game already ended)
        return None, -INF

    if len(moves) == 1:                 # only one possible move
        return moves[0], 0.0

    best_val = -INF
    best_moves = []

    # Order our moves by heuristic value of the child (descending)
    children = []
    for m in moves:
        child_state, extra_move = get_child_state(state, m, 0)
        children.append((m, child_state, extra_move, evaluate(child_state)))
    children.sort(key=lambda x: x[3], reverse=True)

    for m, child_state, extra_move, _ in children:
        # Time check – stop early if we are out of time
        if time.perf_counter() - start_time > TIME_LIMIT:
            break

        nxt = 0 if extra_move else 1
        val = minimax(child_state, depth - 1, -INF, INF, nxt)

        if val > best_val:
            best_val = val
            best_moves = [m]
        elif val == best_val:
            best_moves.append(m)

    if not best_moves:                  # time out before any child examined
        return None, -INF

    # Break ties randomly to avoid deterministic play
    return random.choice(best_moves), best_val


def choose_move(state: Tuple[Tuple[int, ...], Tuple[int, ...]]) -> int:
    """Iterative deepening until time runs out, then return the best move found."""
    start = time.perf_counter()
    best_move = None

    for depth in range(1, MAX_DEPTH + 1):
        move, _ = search_at_depth(state, depth, start)
        if move is not None:
            best_move = move
        # If we have consumed the allocated time, stop deepening
        if time.perf_counter() - start > TIME_LIMIT:
            break

    # Ultimate fallback (should never be needed)
    if best_move is None:
        moves = legal_moves(state, 0)
        best_move = moves[0] if moves else 0

    return best_move


def policy(you: List[int], opponent: List[int]) -> int:
    """
    Main entry point for the tournament.
    ``you`` and ``opponent`` are the current 7‑element lists describing the board.
    Returns a legal house index (0‑5) to play.
    """
    # Convert the lists into immutable tuples for the search
    state = (tuple(you), tuple(opponent))
    return choose_move(state)
