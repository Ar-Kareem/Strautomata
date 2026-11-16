
from functools import lru_cache

WIN_LINES = ((0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6))

def _winner_state(s):
    for a,b,c in WIN_LINES:
        tot = s[a]+s[b]+s[c]
        if tot == 3:
            return 1
        if tot == -3:
            return -1
    return 0

@lru_cache(maxsize=None)
def _solve(state, turn):
    # state: tuple of 9 ints, turn: 1 or -1 to move
    # returns (value from perspective of 1, depth to terminal)
    w = _winner_state(state)
    if w == 1:
        return (1, 0)
    if w == -1:
        return (-1, 0)
    if 0 not in state:
        return (0, 0)
    moves = [i for i, v in enumerate(state) if v == 0]
    # order for deterministic search: center/corner/edge not critical
    # put center first for pruning, but result is exact
    if turn == 1:
        best_v = -2
        best_d = 0
        first = True
        for i in moves:
            lst = list(state)
            lst[i] = 1
            v, d = _solve(tuple(lst), -1)
            d += 1
            if first or v > best_v or (v == best_v and (
                (v == 1 and d < best_d) or
                (v == 0 and d > best_d) or
                (v == -1 and d > best_d)
            )):
                best_v, best_d = v, d
                first = False
        return (best_v, best_d)
    else:
        best_v = 2
        best_d = 0
        first = True
        for i in moves:
            lst = list(state)
            lst[i] = -1
            v, d = _solve(tuple(lst), 1)
            d += 1
            if first or v < best_v or (v == best_v and (
                (v == -1 and d < best_d) or
                (v == 0 and d > best_d) or
                (v == 1 and d > best_d)
            )):
                best_v, best_d = v, d
                first = False
        return (best_v, best_d)

def _priority(r, c):
    if (r, c) in ((0,0),(0,2),(2,0),(2,2)):
        return 0
    if (r, c) == (1,1):
        return 1
    return 2

def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        empties = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
        if not empties:
            return (0, 0)
        if len(empties) == 1:
            return empties[0]

        # immediate win
        for r, c in empties:
            # check if placing 1 wins
            # row
            # fast check without full copy
            win = False
            # simulate
            # row r
            if board[r][0] + board[r][1] + board[r][2] == 2:  # two 1s + empty (this cell)
                # need this cell empty (it is) and other two are 1
                if board[r][(c+1)%3] == 1 and board[r][(c+2)%3] == 1:
                    win = True
            if not win and board[0][c] + board[1][c] + board[2][c] == 2:
                if board[(r+1)%3][c] == 1 and board[(r+2)%3][c] == 1:
                    win = True
            if not win and r == c and board[0][0]+board[1][1]+board[2][2] == 2:
                if board[(r+1)%3][(c+1)%3] == 1 and board[(r+2)%3][(c+2)%3] == 1:
                    # only valid on diagonal, r==c ensures cells are diagonal
                    win = True
            if not win and r + c == 2 and board[0][2]+board[1][1]+board[2][0] == 2:
                # anti-diagonal
                # verify other two are 1
                cells = [(0,2),(1,1),(2,0)]
                cells.remove((r,c))
                if board[cells[0][0]][cells[0][1]] == 1 and board[cells[1][0]][cells[1][1]] == 1:
                    win = True
            if win:
                return (r, c)

        # immediate block (opponent has two -1)
        for r, c in empties:
            block = False
            if board[r][0] + board[r][1] + board[r][2] == -2:
                if board[r][(c+1)%3] == -1 and board[r][(c+2)%3] == -1:
                    block = True
            if not block and board[0][c] + board[1][c] + board[2][c] == -2:
                if board[(r+1)%3][c] == -1 and board[(r+2)%3][c] == -1:
                    block = True
            if not block and r == c and board[0][0]+board[1][1]+board[2][2] == -2:
                if board[(r+1)%3][(c+1)%3] == -1 and board[(r+2)%3][(c+2)%3] == -1:
                    block = True
            if not block and r + c == 2 and board[0][2]+board[1][1]+board[2][0] == -2:
                cells = [(0,2),(1,1),(2,0)]
                cells.remove((r,c))
                if board[cells[0][0]][cells[0][1]] == -1 and board[cells[1][0]][cells[1][1]] == -1:
                    block = True
            if block:
                # only block if no win (wins already returned)
                # store first block but continue to check wins? wins done.
                # return block immediately; minimax would also find it,
                # but explicit for safety.
                # To allow winning over blocking, wins already handled.
                # So return:
                return (r, c)

        # full search
        state = tuple(board[r][c] for r in range(3) for c in range(3))
        # sort empties by priority for deterministic tie break
        ordered = sorted(empties, key=lambda x: _priority(x[0], x[1]))

        infos = []  # (r,c,v,d)
        for r, c in ordered:
            idx = r*3+c
            lst = list(state)
            lst[idx] = 1
            s1 = tuple(lst)
            # if this move already wins, _solve returns (1,0)
            v1, d1 = _solve(s1, -1)
            infos.append((r, c, v1, d1, s1))

        best_v = max(x[2] for x in infos)
        best_infos = [x for x in infos if x[2] == best_v]

        if best_v == 1:
            # fastest win
            best_infos.sort(key=lambda x: x[3])
            return (best_infos[0][0], best_infos[0][1])

        # for draw / loss: maximize trap score
        # trap = sum(v2 - best_v) over opponent replies
        scored = []
        for r, c, v1, d1, s1 in best_infos:
            opp_moves = [i for i, v in enumerate(s1) if v == 0]
            if not opp_moves:
                trap = 0
            else:
                trap = 0
                for j in opp_moves:
                    lst2 = list(s1)
                    lst2[j] = -1
                    s2 = tuple(lst2)
                    v2, _ = _solve(s2, 1)
                    if v2 > best_v:
                        trap += (v2 - best_v)
            scored.append((trap, d1, r, c))

        # max trap, then max depth (delay / prolong), then priority order preserved
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return (scored[0][2], scored[0][3])
    except Exception:
        try:
            for r in range(3):
                for c in range(3):
                    if board[r][c] == 0:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
