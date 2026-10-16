
import random

# ---------------------------------------------------------------------------
# Cell (r, c) <-> bit i = 3*r + c. Winning-line bitmasks for a 3x3 board:
#   rows {0,1,2}=7, {3,4,5}=56, {6,7,8}=448
#   cols {0,3,6}=73, {1,4,7}=146, {2,5,8}=292
#   diag {0,4,8}=273, anti-diag {2,4,6}=84
_WIN_MASKS = (7, 56, 448, 73, 146, 292, 273, 84)
_FULL = 511

_IS_WIN = [False] * 512
_POPCNT = [0] * 512
for _m in range(512):
    _POPCNT[_m] = bin(_m).count("1")
    for _w in _WIN_MASKS:
        if (_m & _w) == _w:
            _IS_WIN[_m] = True
            break

# Positional weights, used ONLY as a low-priority tie-break:
# center (3) > corners (2) > edges (1).
_WEIGHT = {1: 2, 2: 1, 4: 2, 8: 1, 16: 3, 32: 1, 64: 2, 128: 1, 256: 2}

_memo = {}


def _negamax(me, opp):
    """Exact game value for the player to move ('me' = that player's stones).

    Scores (mover's perspective):
        win  : 10 - (pieces on board when the win completes)   [1..9]
        draw : 0
        loss : -(10 - (pieces on board at the loss))           [-9..-1]
    so faster wins and slower losses are strictly preferred.
    Wins / full boards are detected BEFORE recursing, so recursion only
    happens on live positions. Results memoized on (me, opp).
    """
    key = (me << 9) | opp
    cached = _memo.get(key)
    if cached is not None:
        return cached

    d_after = _POPCNT[me | opp] + 1      # pieces after the move to be made
    best = -100
    m = _FULL ^ (me | opp)               # empty cells
    while m:
        bit = m & (-m)
        m ^= bit
        nme = me | bit
        if _IS_WIN[nme]:                 # immediate win
            v = 10 - d_after
        elif (nme | opp) == _FULL:       # last cell -> draw
            v = 0
        else:
            v = -_negamax(opp, nme)
        if v > best:
            best = v
    _memo[key] = best
    return best


def _threat_score(me, opp):
    """(#lines where 'me' has an open two) - (#lines where 'opp' has an open two)."""
    t = 0
    for w in _WIN_MASKS:
        if _POPCNT[me & w] == 2 and (opp & w) == 0:
            t += 1
        elif _POPCNT[opp & w] == 2 and (me & w) == 0:
            t -= 1
    return t


def policy(board):
    """Return (row, col) of the optimal move for player '1'."""
    try:
        me = 0
        opp = 0
        for r in range(3):
            row = board[r]
            for c in range(3):
                v = row[c]
                if v == 1:
                    me |= 1 << (3 * r + c)
                elif v == -1:
                    opp |= 1 << (3 * r + c)

        filled = me | opp
        empties = _FULL ^ filled
        if empties == 0:                  # degenerate: no legal move exists
            return (0, 0)

        d_after = _POPCNT[filled] + 1
        best_val = -1000
        best_t = -10
        best_w = -1
        best_moves = []
        m = empties
        while m:
            bit = m & (-m)
            m ^= bit
            nme = me | bit
            if _IS_WIN[nme]:
                v = 10 - d_after          # this move wins immediately
            elif (nme | opp) == _FULL:
                v = 0                     # this move fills the board: draw
            else:
                v = -_negamax(opp, nme)

            if v > best_val:
                best_val = v
                best_t = _threat_score(nme, opp)
                best_w = _WEIGHT[bit]
                best_moves = [bit]
            elif v == best_val:
                t = _threat_score(nme, opp)
                if t > best_t:
                    best_t = t
                    best_w = _WEIGHT[bit]
                    best_moves = [bit]
                elif t == best_t:
                    w = _WEIGHT[bit]
                    if w > best_w:
                        best_w = w
                        best_moves = [bit]
                    elif w == best_w:
                        best_moves.append(bit)

        bit = random.choice(best_moves)   # randomize among equally optimal moves
        idx = bit.bit_length() - 1
        return (idx // 3, idx % 3)

    except Exception:
        # Ultra-defensive fallback: always emit some empty cell.
        try:
            for r in range(len(board)):
                row = board[r]
                for c in range(len(row)):
                    if row[c] == 0:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
