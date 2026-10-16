
import random
from typing import Dict, List, Tuple, Set

# ----------------------------------------------------------------------
# Board geometry
# ----------------------------------------------------------------------
LETTERS = [chr(ord('a') + i) for i in range(9)]          # a … i
NUMBERS = [str(i) for i in range(1, 10)]                  # '1' … '9'
SUMS = list(range(6, 15))                                   # 6 … 14 inclusive

# Mapping sum -> diagonal line name
SUM_TO_NAME = {
    6: 'a5', 7: 'a6', 8: 'a7', 9: 'a8', 10: 'a9',
    11: 'b9', 12: 'c9', 13: 'd9', 14: 'e9'
}
NAME_TO_SUM = {v: k for k, v in SUM_TO_NAME.items()}

# Index of letters (a=1, …, i=9)
LETTER_IDX = {l: i + 1 for i, l in enumerate(LETTERS)}

# ----------------------------------------------------------------------
# Pre‑compute usable cells and the three lines each cell belongs to
# ----------------------------------------------------------------------
def cell_in_board(letter: str, number: str) -> bool:
    """True if the cell lies inside the hexagonal board."""
    return 6 <= LETTER_IDX[letter] + int(number) <= 14

# All usable cells
USABLE_CELLS: Set[Tuple[str, str]] = set()
for l in LETTERS:
    for n in NUMBERS:
        if cell_in_board(l, n):
            USABLE_CELLS.add((l, n))

# For each cell, the three line names it belongs to
CELL_TO_LINES: Dict[Tuple[str, str], List[str]] = {}
for l, n in USABLE_CELLS:
    # letter line
    letter_line = l
    # number line
    number_line = n
    # diagonal line (vertical)
    diag_line = SUM_TO_NAME[LETTER_IDX[l] + int(n)]
    CELL_TO_LINES[(l, n)] = [letter_line, number_line, diag_line]

# List of all line names (27 in total)
ALL_LINES = LETTERS[:] + NUMBERS[:] + list(SUM_TO_NAME.values())

# ----------------------------------------------------------------------
# Helper functions for evaluating a position
# ----------------------------------------------------------------------
def parse_state(state: List[List[object]]) -> Tuple[Dict[Tuple[str, str], int],
                                                       Dict[Tuple[str, str], str]]:
    """
    Extract line counts and occupied cells from the raw state.
    line_counts[(line_name, role)] = count
    occupied[(letter, number)] = role
    """
    line_counts: Dict[Tuple[str, str], int] = {}
    occupied: Dict[Tuple[str, str], str] = {}
    for fact in state:
        if fact[0] == 'cell':
            _, letter, number, role = fact
            occupied[(letter, number)] = role
        elif fact[0] == 'line_count':
            _, line, role, cnt = fact
            line_counts[(line, role)] = int(cnt)
        # other facts are ignored
    return line_counts, occupied


def compute_scores(line_counts: Dict[Tuple[str, str], int],
                   role: str, opponent: str) -> Tuple[int, int]:
    """Return (score_for_role, score_for_opponent) according to the game rule."""
    score_role = 0
    score_opp = 0
    for line in ALL_LINES:
        cnt_role = line_counts.get((line, role), 0)
        cnt_opp = line_counts.get((line, opponent), 0)
        if cnt_role > cnt_opp:
            score_role += cnt_role
        elif cnt_opp > cnt_role:
            score_opp += cnt_opp
    return score_role, score_opp


def apply_move(line_counts: Dict[Tuple[str, str], int],
               occupied: Dict[Tuple[str, str], str],
               move: Tuple[str, str], player: str) -> Tuple[Dict[Tuple[str, str], int],
                                                               Dict[Tuple[str, str], str]]:
    """Return new line‑count dict and occupied dict after placing `player` on `move`."""
    new_counts = dict(line_counts)
    new_occupied = dict(occupied)
    new_occupied[move] = player
    for line in CELL_TO_LINES[move]:
        key = (line, player)
        new_counts[key] = new_counts.get(key, 0) + 1
    return new_counts, new_occupied


def all_moves(occupied: Dict[Tuple[str, str], str]) -> List[Tuple[str, str]]:
    """List of currently empty usable cells."""
    return [cell for cell in USABLE_CELLS if cell not in occupied]

# ----------------------------------------------------------------------
# Main policy function
# ----------------------------------------------------------------------
def policy(state: List[List[object]], role: str) -> str:
    """
    Choose a legal move for `role` in the given `state`.
    The algorithm performs a depth‑2 lookahead (our move + opponent’s best reply)
    and picks the move that maximises our advantage after the reply.
    """
    # ------------------------------------------------------------------
    # 1. Parse the state
    # ------------------------------------------------------------------
    line_counts, occupied = parse_state(state)
    opponent = 'blue' if role == 'red' else 'red'

    # ------------------------------------------------------------------
    # 2. Generate all our possible moves
    # ------------------------------------------------------------------
    our_moves = all_moves(occupied)
    if not our_moves:                     # should not happen in a real game
        # fallback – just return a dummy legal move
        return 'place(a,5)'

    # ------------------------------------------------------------------
    # 3. Evaluate each move with depth‑2 lookahead
    # ------------------------------------------------------------------
    best_net = -10**9
    best_move = None
    best_our_score = -10**9   # tie‑breaker

    for move in our_moves:
        # ---- simulate our move ----
        new_counts, new_occupied = apply_move(line_counts, occupied, move, role)
        our_score_after_us, opp_score_after_us = compute_scores(new_counts, role, opponent)

        # ---- opponent replies ----
        opp_moves = all_moves(new_occupied)
        if not opp_moves:                     # board full after us
            net = our_score_after_us - opp_score_after_us
        else:
            # opponent picks the reply that maximises his own score
            worst_net_for_us = 10**9   # we will keep the smallest net (i.e. best opponent)
            for opp_move in opp_moves:
                opp_counts, _ = apply_move(new_counts, new_occupied, opp_move, opponent)
                opp_score, _ = compute_scores(opp_counts, opponent, role)   # opponent's score
                # after opponent's reply our score stays the same, opponent's score is opp_score
                net = our_score_after_us - opp_score
                if net < worst_net_for_us:
                    worst_net_for_us = net
            net = worst_net_for_us

        # ---- keep the best move ----
        if net > best_net or (net == best_net and our_score_after_us > best_our_score):
            best_net = net
            best_move = move
            best_our_score = our_score_after_us

    # In the extremely unlikely case best_move is still None, pick a random move
    if best_move is None:
        best_move = random.choice(our_moves)

    letter, number = best_move
    return f'place({letter},{number})'
