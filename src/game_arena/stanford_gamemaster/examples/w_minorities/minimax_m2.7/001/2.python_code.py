
import sys
from collections import defaultdict

# ----------------------------------------------------------------------
# Pre‑computed board geometry (hex board of side length 5, radius 4)
# ----------------------------------------------------------------------
COLS = ['a','b','c','d','e','f','g','h','i']
ROWS = [str(i) for i in range(1, 10)]

# axial coordinates: column letter -> q, row number -> r
col_to_q = {'a':-4,'b':-3,'c':-2,'d':-1,'e':0,'f':1,'g':2,'h':3,'i':4}
row_to_r = {'1':-4,'2':-3,'3':-2,'4':-1,'5':0,'6':1,'7':2,'8':3,'9':4}

# six unusable cells (they are inside the hex shape but illegal to use)
ILLEGAL_CELLS = {('b','8'), ('d','6'), ('e','2'), ('e','4'), ('f','5'), ('h','5')}

def in_shape(col, row):
    """True iff the cell is inside the hexagonal board (radius 4)."""
    q = col_to_q[col]
    r = row_to_r[row]
    return max(abs(q), abs(r), abs(q + r)) <= 4

# all legal cells on the board
LEGAL_CELLS = [(c, r) for c in COLS for r in ROWS
               if in_shape(c, r) and (c, r) not in ILLEGAL_CELLS]

# ----------------------------------------------------------------------
# Diagonal (vertical) line identification.
# In this game the three directions are:
#   – columns   (constant q)
#   – rows      (constant r)
#   – diagonals (constant q‑r)
# Each diagonal is labelled by its top‑most cell (smallest row number).
# ----------------------------------------------------------------------
# group cells by diagonal value d = q - r
diag_groups = defaultdict(list)
for col, row in LEGAL_CELLS:
    q = col_to_q[col]
    r = row_to_r[row]
    diag_groups[q - r].append((col, row))

# for each diagonal find the top‑most cell → its label
DIAG_ID_OF = {}               # (col,row) -> label string
for d, cells in diag_groups.items():
    # smallest row first, then smallest column
    cells.sort(key=lambda cr: (row_to_r[cr[1]], col_to_q[cr[0]]))
    top_cell = cells[0]
    label = top_cell[0] + top_cell[1]
    for c, r in cells:
        DIAG_ID_OF[(c, r)] = label

# list of all diagonal IDs (for fast iteration)
DIAG_IDS = sorted(set(DIAG_ID_OF.values()))

# ----------------------------------------------------------------------
# State parsing
# ----------------------------------------------------------------------
def parse_state(state):
    """Return three dictionaries (col/row/diag counts) and the set of occupied cells."""
    col_cnt = defaultdict(lambda: {'red': 0, 'blue': 0})
    row_cnt = defaultdict(lambda: {'red': 0, 'blue': 0})
    diag_cnt = defaultdict(lambda: {'red': 0, 'blue': 0})
    occupied = set()
    for fact in state:
        if fact[0] == 'cell':
            _, col, row, player = fact
            occupied.add((col, row))
            col_cnt[col][player] += 1
            row_cnt[row][player] += 1
            diag = DIAG_ID_OF[(col, row)]
            diag_cnt[diag][player] += 1
    return col_cnt, row_cnt, diag_cnt, occupied

# ----------------------------------------------------------------------
# Majority counting
# ----------------------------------------------------------------------
def count_majorities(role, col_cnt, row_cnt, diag_cnt):
    """Return (total_majorities, col_maj, row_maj, diag_maj) for *role*."""
    opp = 'blue' if role == 'red' else 'red'
    col_maj = sum(1 for c in COLS if col_cnt[c][role] > col_cnt[c][opp])
    row_maj = sum(1 for r in ROWS if row_cnt[r][role] > row_cnt[r][opp])
    diag_maj = sum(1 for d in DIAG_IDS if diag_cnt[d][role] > diag_cnt[d][opp])
    return col_maj + row_maj + diag_maj, col_maj, row_maj, diag_maj

# ----------------------------------------------------------------------
# Move evaluation
# ----------------------------------------------------------------------
def evaluate_move(role, col, row, col_cnt, row_cnt, diag_cnt):
    """
    Simulate placing a stone for *role* on (col,row) and return
    (total_maj, col_maj, row_maj, diag_maj, is_winning).
    """
    # copy the current counts (shallow copy of the inner dicts is enough)
    col_tmp = {p: dict(col_cnt[p]) for p in ('red', 'blue')}
    row_tmp = {p: dict(row_cnt[p]) for p in ('red', 'blue')}
    diag_tmp = {p: dict(diag_cnt[p]) for p in ('red', 'blue')}

    # apply the new stone
    col_tmp[role][col] = col_tmp[role].get(col, 0) + 1
    row_tmp[role][row] = row_tmp[role].get(row, 0) + 1
    diag = DIAG_ID_OF[(col, row)]
    diag_tmp[role][diag] = diag_tmp[role].get(diag, 0) + 1

    total, c_maj, r_maj, d_maj = count_majorities(role, col_tmp, row_tmp, diag_tmp)

    # winning condition: majority in at least 5 lines of two different directions
    winning = (c_maj >= 5 and r_maj >= 5) or (c_maj >= 5 and d_maj >= 5) or (r_maj >= 5 and d_maj >= 5)

    return total, c_maj, r_maj, d_maj, winning

# ----------------------------------------------------------------------
# Main policy function
# ----------------------------------------------------------------------
def policy(state, role):
    # ------------------------------------------------------------------
    # Parse the current board position
    # ------------------------------------------------------------------
    col_cnt, row_cnt, diag_cnt, occupied = parse_state(state)

    # ------------------------------------------------------------------
    # Determine all legal empty cells
    # ------------------------------------------------------------------
    empty_cells = [cell for cell in LEGAL_CELLS if cell not in occupied]
    if not empty_cells:                     # should never happen, but be safe
        return "place(a,5)"

    # ------------------------------------------------------------------
    # Current majorities (used to compute the gain of a move)
    # ------------------------------------------------------------------
    cur_total, _, _, _ = count_majorities(role, col_cnt, row_cnt, diag_cnt)

    best_move = None
    best_score = -1          # prefer winning moves →给他们最高的分数
    best_delta = -1
    best_total = -1

    # ------------------------------------------------------------------
    # Try every legal move
    # ------------------------------------------------------------------
    for col, row in empty_cells:
        total, c_maj, r_maj, d_maj, winning = evaluate_move(
            role, col, row, col_cnt, row_cnt, diag_cnt)

        delta = total - cur_total      # how many new majorities we gain

        # Winning moves are best; otherwise prefer larger total majorities
        if winning:
            score = 1000 + total
        else:
            score = total

        # tie‑breaking: larger delta, then larger total
        if (score > best_score) or (score == best_score and delta > best_delta) \
               or (score == best_score and delta == best_delta and total > best_total):
            best_score = score
            best_delta = delta
            best_total = total
            best_move = (col, row)

    col, row = best_move
    return f"place({col},{row})"
