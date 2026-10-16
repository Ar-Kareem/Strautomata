
from __future__ import annotations

from collections import deque

N = 11
SIZE = N * N
INF = 10**9

DIRS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1))

RC = [(i // N, i % N) for i in range(SIZE)]

NEI = [[] for _ in range(SIZE)]
for r in range(N):
    for c in range(N):
        i = r * N + c
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                NEI[i].append(rr * N + cc)

# Side definitions
START_BLACK = [0 * N + c for c in range(N)]
START_WHITE = [r * N + 0 for r in range(N)]

TARGET_BLACK = [False] * SIZE
TARGET_WHITE = [False] * SIZE
for c in range(N):
    TARGET_BLACK[(N - 1) * N + c] = True
for r in range(N):
    TARGET_WHITE[r * N + (N - 1)] = True

STARTS = {1: START_BLACK, 2: START_WHITE}
TARGETS = {1: TARGET_BLACK, 2: TARGET_WHITE}

# Central preference order for move iteration / tie-breaking
def _pref_key_black(i: int):
    r, c = RC[i]
    return (abs(c - 5), abs(r - 5) + abs(c - 5), abs(r - 5))

def _pref_key_white(i: int):
    r, c = RC[i]
    return (abs(r - 5), abs(r - 5) + abs(c - 5), abs(c - 5))

ORDER_BLACK = sorted(range(SIZE), key=_pref_key_black)
ORDER_WHITE = sorted(range(SIZE), key=_pref_key_white)

# Precompute bridge-like pairs: non-adjacent cells with exactly two common neighbors
_nei_sets = [set(x) for x in NEI]
BRIDGE = [[] for _ in range(SIZE)]
for a in range(SIZE):
    na = _nei_sets[a]
    for b in range(a + 1, SIZE):
        if b in na:
            continue
        inter = na & _nei_sets[b]
        if len(inter) == 2:
            x, y = tuple(inter)
            BRIDGE[a].append((b, x, y))
            BRIDGE[b].append((a, x, y))


def _winner(board: list[int], colorv: int) -> bool:
    target = TARGETS[colorv]
    seen = [False] * SIZE
    dq = deque()

    for s in STARTS[colorv]:
        if board[s] == colorv:
            seen[s] = True
            dq.append(s)

    while dq:
        u = dq.popleft()
        if target[u]:
            return True
        for v in NEI[u]:
            if not seen[v] and board[v] == colorv:
                seen[v] = True
                dq.append(v)
    return False


def _path_cost(board: list[int], colorv: int) -> int:
    oppv = 3 - colorv
    starts = STARTS[colorv]
    target = TARGETS[colorv]

    dist = [INF] * SIZE
    dq = deque()

    for s in starts:
        cell = board[s]
        if cell == oppv:
            continue
        w = 0 if cell == colorv else 1
        if w < dist[s]:
            dist[s] = w
            if w == 0:
                dq.appendleft(s)
            else:
                dq.append(s)

    while dq:
        u = dq.popleft()
        du = dist[u]
        if target[u]:
            return du
        for v in NEI[u]:
            cell = board[v]
            if cell == oppv:
                continue
            w = 0 if cell == colorv else 1
            nd = du + w
            if nd < dist[v]:
                dist[v] = nd
                if w == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)

    return INF


def _static_eval(board: list[int], myv: int) -> float:
    myc = _path_cost(board, myv)
    oppc = _path_cost(board, 3 - myv)

    if myc >= INF:
        myc = 200
    if oppc >= INF:
        oppc = 200

    return 100.0 * (oppc - myc)


def _local_bonus(board: list[int], move: int, myv: int) -> float:
    oppv = 3 - myv
    r, c = RC[move]

    own_adj = 0
    opp_adj = 0
    empty_adj = 0
    for nb in NEI[move]:
        v = board[nb]
        if v == myv:
            own_adj += 1
        elif v == oppv:
            opp_adj += 1
        else:
            empty_adj += 1

    bonus = 0.0
    bonus += 10.0 * own_adj
    bonus += 4.0 * opp_adj
    bonus += 0.5 * empty_adj

    # Center and axis preference
    center_bonus = 5.0 - 0.5 * (abs(r - 5) + abs(c - 5))
    axis_bonus = (5.0 - abs(c - 5)) if myv == 1 else (5.0 - abs(r - 5))
    bonus += 1.5 * center_bonus + 2.5 * axis_bonus

    # Slight preference for touching own sides; slight penalty for useless far edge hugging
    if myv == 1:
        if r == 0 or r == N - 1:
            bonus += 2.0
        if c == 0 or c == N - 1:
            bonus -= 1.0
    else:
        if c == 0 or c == N - 1:
            bonus += 2.0
        if r == 0 or r == N - 1:
            bonus -= 1.0

    # Bridge / virtual connection bonuses
    for other, x, y in BRIDGE[move]:
        ov = board[other]
        if ov == myv:
            if board[x] != oppv and board[y] != oppv:
                bonus += 8.0
                if board[x] == 0 and board[y] == 0:
                    bonus += 4.0
                elif board[x] == myv or board[y] == myv:
                    bonus += 2.0
        elif ov == oppv:
            if board[x] != myv and board[y] != myv:
                bonus += 2.0

    return bonus


def _immediate_wins(board: list[int], colorv: int, ordered_legal: list[int]) -> list[int]:
    wins = []
    for m in ordered_legal:
        board[m] = colorv
        if _winner(board, colorv):
            wins.append(m)
        board[m] = 0
    return wins


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    myv = 1 if color == "b" else 2
    oppv = 3 - myv

    board = [0] * SIZE
    for r, c in me:
        if 0 <= r < N and 0 <= c < N:
            board[r * N + c] = myv
    for r, c in opp:
        if 0 <= r < N and 0 <= c < N:
            board[r * N + c] = oppv

    order_me = ORDER_BLACK if myv == 1 else ORDER_WHITE
    order_opp = ORDER_BLACK if oppv == 1 else ORDER_WHITE

    legal = [i for i in order_me if board[i] == 0]
    if not legal:
        return (0, 0)

    total_stones = len(me) + len(opp)
    center = 5 * N + 5

    # Simple strong opening bias
    if total_stones <= 1 and board[center] == 0:
        return RC[center]

    # Immediate win
    my_wins = _immediate_wins(board, myv, legal)
    if my_wins:
        return RC[my_wins[0]]

    # Mandatory blocks
    opp_legal = [i for i in order_opp if board[i] == 0]
    opp_wins = _immediate_wins(board, oppv, opp_legal)
    if len(opp_wins) == 1:
        return RC[opp_wins[0]]

    # Candidate selection
    if opp_wins:
        candidates = opp_wins[:]  # if multiple threats, probably losing; still choose best block
    else:
        scored = []
        for m in legal:
            board[m] = myv
            s = _static_eval(board, myv) + _local_bonus(board, m, myv)
            board[m] = 0
            scored.append((s, m))
        scored.sort(reverse=True)
        top_k = 10 if total_stones >= 6 else 14
        candidates = [m for _, m in scored[:min(top_k, len(scored))]]
        if not candidates:
            candidates = [legal[0]]

    # Shallow minimax: choose move with best worst-case opponent reply
    best_move = candidates[0]
    best_value = -1e18

    for m in candidates:
        board[m] = myv

        # Safety check
        if _winner(board, myv):
            board[m] = 0
            return RC[m]

        worst_reply_value = 1e18
        any_reply = False

        for r in order_opp:
            if board[r] != 0:
                continue
            any_reply = True
            board[r] = oppv

            if _winner(board, oppv):
                val = -1e9
            else:
                val = _static_eval(board, myv)

            board[r] = 0

            if val < worst_reply_value:
                worst_reply_value = val

            if worst_reply_value <= best_value:
                break

        if not any_reply:
            worst_reply_value = _static_eval(board, myv)

        board[m] = 0

        # Small bonus from local shape helps break close ties
        final_value = worst_reply_value + 0.25 * _local_bonus(board[:m] + [myv] + board[m+1:], m, myv) if False else worst_reply_value

        if final_value > best_value:
            best_value = final_value
            best_move = m

    # Final legality guard
    if 0 <= best_move < SIZE and board[best_move] == 0:
        return RC[best_move]

    for m in legal:
        return RC[m]

    return (0, 0)
