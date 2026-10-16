
import random
import copy

# ----------------------------------------------------------------------
# Pre‑computed board structure
# ----------------------------------------------------------------------
# letters a‑i -> indices 1‑9
LETTERS = [chr(ord('a') + i) for i in range(9)]
LET2IDX = {l: i + 1 for i, l in enumerate(LETTERS)}   # a->1, b->2, ...

# Diagonal line names for sums 6‑14
SUM_TO_DIAG = {
    6: 'a5', 7: 'a6', 8: 'a7', 9: 'a8', 10: 'a9',
    11: 'b9', 12: 'c9', 13: 'd9', 14: 'e9'
}
DIAG_LINES = list(SUM_TO_DIAG.values())   # 9 diagonal line names

# All lines (as keys) -------------------------------------------------
LETTER_LINES = LETTERS                     # a … i
NUMBER_LINES = [str(i) for i in range(1, 10)]   # '1' … '9'
ALL_LINES = LETTER_LINES + NUMBER_LINES + DIAG_LINES   # 27 line names

# Pre‑compute which cells belong to which lines
# cell -> list of line names it belongs to
CELL_TO_LINES = {}
# line -> list of cells belonging to it
LINE_TO_CELLS = {line: [] for line in ALL_LINES}

# shape: letter index + number (both 1‑9) must be in [6,14]
for l in LETTERS:
    li = LET2IDX[l]
    for n in range(1, 10):
        s = li + n
        if s < 6 or s > 14:
            continue
        cell = (l, n)
        # letter line
        ll = l
        # number line
        nl = str(n)
        # diagonal line
        dl = SUM_TO_DIAG[s]
        CELL_TO_LINES[cell] = [ll, nl, dl]
        LINE_TO_CELLS[ll].append(cell)
        LINE_TO_CELLS[nl].append(cell)
        LINE_TO_CELLS[dl].append(cell)

# List of all usable cells (as (letter, number) pairs)
ALL_CELLS = list(CELL_TO_LINES.keys())

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def parse_state(state):
    """Return a dict {(letter,number): owner} from the list of facts."""
    board = {}
    for fact in state:
        if fact[0] == 'cell':
            # fact = ["cell", "a", "5", "red"]
            letter = fact[1]
            number = int(fact[2])
            owner = fact[3]
            board[(letter, number)] = owner
    return board

def generate_candidates(board):
    """Return list of empty (letter,number) pairs that can be played."""
    return [c for c in ALL_CELLS if c not in board]

def simulate_move(board, move, player):
    """Return a new board after placing 'player' at 'move'."""
    new_board = copy.copy(board)
    new_board[move] = player
    return new_board

def evaluate_board(board, player):
    """
    Heuristic evaluation of the board from the point of view of 'player'.
    Returns a numeric score (larger is better).
    """
    opponent = 'blue' if player == 'red' else 'red'

    # ---- count stones per line -----------------------------------------
    # line_counts[line] = [red_count, blue_count]
    line_counts = {line: [0, 0] for line in ALL_LINES}
    stones = {'red': 0, 'blue': 0}
    for (letter, number), owner in board.items():
        stones[owner] += 1
        idx = 0 if owner == 'red' else 1
        for ln in CELL_TO_LINES[(letter, number)]:
            line_counts[ln][idx] += 1

    # ---- determine line winners ----------------------------------------
    line_winners = {}   # line -> 'red', 'blue' or None
    for line, cnt in line_counts.items():
        if cnt[0] > cnt[1]:
            line_winners[line] = 'red'
        elif cnt[1] > cnt[0]:
            line_winners[line] = 'blue'
        else:
            line_winners[line] = None

    # ---- count line wins per direction ---------------------------------
    # direction categories
    dirs = {
        'letter': LETTER_LINES,
        'number': NUMBER_LINES,
        'vertical': DIAG_LINES
    }
    dir_line_wins = {'red': 0, 'blue': 0}
    line_wins = {'red': 0, 'blue': 0}
    for line, winner in line_winners.items():
        if winner:
            line_wins[winner] += 1

    # ---- direction winners (need at least 5 line wins) -----------------
    dir_points = {'red': 0, 'blue': 0}
    for d_name, d_lines in dirs.items():
        rw = sum(1 for l in d_lines if line_winners.get(l) == 'red')
        bw = sum(1 for l in d_lines if line_winners.get(l) == 'blue')
        if rw >= 5 and rw > bw:
            dir_points['red'] += 1
        elif bw >= 5 and bw > rw:
            dir_points['blue'] += 1

    # ---- check game end -------------------------------------------------
    if dir_points[player] >= 2:
        return 1000
    if dir_points[opponent] >= 2:
        return -1000

    # ---- otherwise combine several terms --------------------------------
    # direction advantage (dominates)
    dir_score = (dir_points[player] - dir_points[opponent]) * 1000
    # line‑win advantage
    line_score = line_wins[player] - line_wins[opponent]
    # stone‑count tie‑breaker (small weight)
    stone_score = stones[player] - stones[opponent]

    return dir_score + line_score + stone_score

# ----------------------------------------------------------------------
# Main policy function (depth‑2 minimax with simple alpha‑beta)
# ----------------------------------------------------------------------
def policy(state: list, role: str) -> str:
    board = parse_state(state)
    candidates = generate_candidates(board)

    # No legal moves – should not happen in a real game
    if not candidates:
        # Return a dummy legal move (won’t be called in practice)
        return "place(a,5)"

    opponent = 'blue' if role == 'red' else 'red'
    best_move = None
    best_score = -10**9   # lower than any realistic score

    # Iterate over all our possible moves
    for mv in candidates:
        new_board = simulate_move(board, mv, role)

        # Immediate winning test
        if evaluate_board(new_board, role) >= 1000:
            # Winning move – return immediately
            letter, number = mv
            return f"place({letter},{number})"

        # opponent's best reply (worst case for us)
        opp_candidates = generate_candidates(new_board)
        worst_opp_score = 10**9   # larger = better for us, so start high
        if not opp_candidates:
            # No reply possible – use current evaluation
            worst_opp_score = evaluate_board(new_board, role)
        else:
            for opp_mv in opp_candidates:
                opp_board = simulate_move(new_board, opp_mv, opponent)
                sc = evaluate_board(opp_board, role)
                if sc < worst_opp_score:
                    worst_opp_score = sc
                    # prune: if worst already worse than current best, stop
                    if worst_opp_score <= best_score:
                        break
        # After exploring opponent replies, worst_opp_score is our lower bound
        if worst_opp_score > best_score:
            best_score = worst_opp_score
            best_move = mv
            # optional early exit if we already achieve maximal possible
            if best_score >= 1000:
                break

    # If for some reason best_move stayed None (should not happen), pick randomly
    if best_move is None:
        best_move = random.choice(candidates)

    letter, number = best_move
    return f"place({letter},{number})"
