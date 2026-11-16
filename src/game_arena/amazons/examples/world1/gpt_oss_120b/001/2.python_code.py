
import numpy as np

# Directions for queen‑like movement (row change, column change)
_DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1),
               (-1, -1), (-1, 1), (1, -1), (1, 1)]

def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 6 and 0 <= c < 6

def policy(board: np.ndarray) -> str:
    """
    Return a legal Amazons move for the player whose pieces are marked with 1.
    The board is a 6x6 numpy array with values:
        0  = empty
        1  = our amazon
        2  = opponent amazon
        -1 = arrow / blocked square
    The returned string has the format "fr,fc:tr,tc:ar,ac".
    """
    # Ensure we are working with a mutable view
    b = board  # alias for brevity

    # Iterate over all our amazons
    for fr in range(6):
        for fc in range(6):
            if b[fr, fc] != 1:
                continue

            # Try every queen direction for the amazon move
            for dr, dc in _DIRECTIONS:
                tr, tc = fr + dr, fc + dc
                while _in_bounds(tr, tc) and b[tr, tc] == 0:
                    # ----- simulate moving the amazon -----
                    b[fr, fc] = 0
                    b[tr, tc] = 1

                    # From the new position, look for a legal arrow shot
                    for adr, adc in _DIRECTIONS:
                        ar, ac = tr + adr, tc + adc
                        while _in_bounds(ar, ac) and b[ar, ac] == 0:
                            # Found a complete legal move – restore board and return
                            b[fr, fc] = 1
                            b[tr, tc] = 0
                            return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

                    # ----- restore board before trying next arrow direction -----
                    b[fr, fc] = 1
                    b[tr, tc] = 0

                    # Advance further along the same direction for the amazon
                    tr += dr
                    tc += dc

    # Should never reach here if the environment guarantees a move.
    raise RuntimeError("No legal Amazons move found – board may be terminal.")
