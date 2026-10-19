
import numpy as np

# Directions for queen‑like movement (row change, column change)
DIRS = [
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (1, -1), (-1, 1), (-1, -1)
]

def _in_bounds(r, c):
    return 0 <= r < 6 and 0 <= c < 6

def policy(board) -> str:
    """
    Return a legal Amazons move for the player whose pieces are marked with 1.
    The board is a 6x6 numpy array with values:
        0 : empty
        1 : our amazon
        2 : opponent amazon
       -1 : arrow (blocked)
    Move format: "fr,fc:tr,tc:ar,ac"
    """
    # Locate all our amazons
    my_amazons = list(zip(*np.where(board == 1)))

    for fr, fc in my_amazons:
        # Try every queen‑like move from (fr,fc)
        for dr, dc in DIRS:
            tr, tc = fr, fc
            while True:
                tr += dr
                tc += dc
                if not _in_bounds(tr, tc):
                    break
                if board[tr, tc] != 0:          # blocked
                    break

                # Simulate moving the amazon: vacate (fr,fc), occupy (tr,tc)
                sim_board = board.copy()
                sim_board[fr, fc] = 0
                sim_board[tr, tc] = 1

                # From the new position, try every arrow shot
                for adr, adc in DIRS:
                    ar, ac = tr, tc
                    while True:
                        ar += adr
                        ac += adc
                        if not _in_bounds(ar, ac):
                            break
                        if sim_board[ar, ac] != 0:   # blocked for arrow
                            break
                        # Found a legal triple; return it
                        return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

    # According to the problem statement this should never happen,
    # but raise a clear error if it does.
    raise RuntimeError("No legal move found for the given board.")
