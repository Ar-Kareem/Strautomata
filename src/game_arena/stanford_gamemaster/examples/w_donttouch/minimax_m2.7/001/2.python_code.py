
import sys
sys.setrecursionlimit(10000)

# Pre‑computed orthogonal neighbours for each of the 16 cells (0‑based index)
NEIGH = []
for r in range(4):
    for c in range(4):
        idx = r * 4 + c
        mask = 0
        if r > 0:   mask |= 1 << (idx - 4)      # up
        if r < 3:   mask |= 1 << (idx + 4)      # down
        if c > 0:   mask |= 1 << (idx - 1)      # left
        if c < 3:   mask |= 1 << (idx + 1)      # right
        NEIGH.append(mask)

FULL_MASK = (1 << 16) - 1          # all 16 cells set
OTHER = {'x': 'o', 'o': 'x'}

# Memoisation tables: win[state] = True/False, best_move[state] = cell index
win_table = {}
best_move_table = {}

def win_state(x_mask: int, o_mask: int, role: str) -> bool:
    """
    Returns True if the player to move (role) has a forced win from the
    given configuration, otherwise False.  The result is memoised.
    """
    key = (x_mask, o_mask, role)
    if key in win_table:
        return win_table[key]

    # Choose masks for the current player and opponent
    if role == 'x':
        my_mask = x_mask
        opp_mask = o_mask
    else:
        my_mask = o_mask
        opp_mask = x_mask

    empty = FULL_MASK ^ (x_mask | o_mask)   # bits of free cells

    # Iterate over safe moves first; if we find one that makes opponent lose,
    # the current player wins.
    for cell in range(16):
        if not (empty >> cell) & 1:
            continue            # not an empty cell
        if NEIGH[cell] & my_mask:
            continue            # would be adjacent to own mark – immediate loss, ignore
        # Safe move – place the piece
        new_my_mask = my_mask | (1 << cell)
        if role == 'x':
            new_x = new_my_mask
            new_o = opp_mask
        else:
            new_o = new_my_mask
            new_x = opp_mask

        # Recurse: if opponent cannot win from the resulting state, we win.
        if not win_state(new_x, new_o, OTHER[role]):
            win_table[key] = True
            best_move_table[key] = cell
            return True

    # No safe winning move – the position is losing for the player to move.
    win_table[key] = False
    return False


# Pre‑compute the whole game (both roles) at import time.
# This builds the tables for all reachable states.
win_state(0, 0, 'x')
win_state(0, 0, 'o')


def policy(state, role):
    """
    Stanford GameMaster policy for 'donttouch'.
    Returns a legal move in Stanford syntax, e.g. 'mark(2,3)'.
    """
    # Parse the state into two bit masks.
    x_mask = 0
    o_mask = 0
    for prop in state:
        if prop[0] == 'cell':
            row = int(prop[1]) - 1
            col = int(prop[2]) - 1
            idx = row * 4 + col
            mark = prop[3]
            if mark == 'x':
                x_mask |= (1 << idx)
            elif mark == 'o':
                o_mask |= (1 << idx)
            # 'b' cells are ignored (they are empty)

    # Ensure the tables are filled for this state (they may already be).
    win_state(x_mask, o_mask, role)

    key = (x_mask, o_mask, role)
    move_idx = best_move_table.get(key)

    # If we have no stored winning move, fall back to any safe move,
    # or any empty cell if none are safe.
    if move_idx is None:
        my_mask = x_mask if role == 'x' else o_mask
        empty = FULL_MASK ^ (x_mask | o_mask)
        for cell in range(16):
            if (empty >> cell) & 1:
                # safe cell?
                if not (NEIGH[cell] & my_mask):
                    move_idx = cell
                    break
        # Still no safe cell? Just pick any empty one.
        if move_idx is None:
            for cell in range(16):
                if (empty >> cell) & 1:
                    move_idx = cell
                    break

    # Convert the index back to 1‑based row/col.
    row = move_idx // 4 + 1
    col = move_idx % 4 + 1
    return f"mark({row},{col})"
