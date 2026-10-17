
import time

# Precompute board geometry on a 6x6 grid
BOARD_SIZE = 6
NUM_SQUARES = 36

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

QUEEN_RAYS = [[] for _ in range(NUM_SQUARES)]
KING_NEIGHBORS = [[] for _ in range(NUM_SQUARES)]

for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        idx = r * BOARD_SIZE + c
        for dr, dc in DIRS:
            ray = []
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                KING_NEIGHBORS[idx].append(nr * BOARD_SIZE + nc)
            while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                ray.append(nr * BOARD_SIZE + nc)
                nr += dr
                nc += dc
            if ray:
                QUEEN_RAYS[idx].append(ray)


def get_queen_destinations(sq, b):
    dest = []
    for ray in QUEEN_RAYS[sq]:
        for nxt in ray:
            if b[nxt] == 0:
                dest.append(nxt)
            else:
                break
    return dest


def generate_legal_moves(b, player):
    amazons = [i for i in range(NUM_SQUARES) if b[i] == player]
    moves = []
    for f_sq in amazons:
        b[f_sq] = 0
        destinations = get_queen_destinations(f_sq, b)
        for t_sq in destinations:
            b[t_sq] = player
            arrow_destinations = get_queen_destinations(t_sq, b)
            for a_sq in arrow_destinations:
                moves.append((f_sq, t_sq, a_sq))
            b[t_sq] = 0
        b[f_sq] = player
    return moves


def evaluate(b, my_p=1, opp_p=2):
    my_amazons = []
    opp_amazons = []
    for i in range(NUM_SQUARES):
        val = b[i]
        if val == my_p:
            my_amazons.append(i)
        elif val == opp_p:
            opp_amazons.append(i)

    # 1. Mobility
    opp_mob = 0
    for sq in opp_amazons:
        opp_mob += len(get_queen_destinations(sq, b))
    if opp_mob == 0:
        return 1000000.0

    my_mob = 0
    for sq in my_amazons:
        my_mob += len(get_queen_destinations(sq, b))
    if my_mob == 0:
        return -1000000.0

    # 2. Multi-source BFS for territory control
    d1 = [-1] * NUM_SQUARES
    d2 = [-1] * NUM_SQUARES

    q1 = list(my_amazons)
    for sq in q1:
        d1[sq] = 0
    head = 0
    while head < len(q1):
        curr = q1[head]
        head += 1
        dist = d1[curr] + 1
        for nxt in KING_NEIGHBORS[curr]:
            if b[nxt] == 0 and d1[nxt] == -1:
                d1[nxt] = dist
                q1.append(nxt)

    q2 = list(opp_amazons)
    for sq in q2:
        d2[sq] = 0
    head = 0
    while head < len(q2):
        curr = q2[head]
        head += 1
        dist = d2[curr] + 1
        for nxt in KING_NEIGHBORS[curr]:
            if b[nxt] == 0 and d2[nxt] == -1:
                d2[nxt] = dist
                q2.append(nxt)

    # Territory score
    t_score = 0.0
    for i in range(NUM_SQUARES):
        if b[i] == 0:
            dist1 = d1[i]
            dist2 = d2[i]
            if dist1 != -1 and dist2 != -1:
                diff = dist2 - dist1
                if diff > 0:
                    t_score += 1.0 + 0.1 * min(diff, 4)
                elif diff < 0:
                    t_score -= 1.0 + 0.1 * min(-diff, 4)
            elif dist1 != -1:
                t_score += 1.5
            elif dist2 != -1:
                t_score -= 1.5

    # Combined score
    return t_score * 4.0 + (my_mob - 2.5 * opp_mob)


def policy(board) -> str:
    start_time = time.time()
    time_limit = 0.85

    # Convert 6x6 numpy array to 1D flat list
    b = [int(board[r, c]) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)]

    legal_moves = generate_legal_moves(b, 1)
    if not legal_moves:
        return "0,0:0,0:0,0"

    if len(legal_moves) == 1:
        f, t, a = legal_moves[0]
        return f"{f // 6},{f % 6}:{t // 6},{t % 6}:{a // 6},{a % 6}"

    # 1-ply evaluation to sort moves
    scored_moves = []
    for f, t, a in legal_moves:
        b[f] = 0
        b[t] = 1
        b[a] = -1

        score = evaluate(b, 1, 2)

        b[a] = 0
        b[t] = 0
        b[f] = 1

        if score >= 999999.0:
            return f"{f // 6},{f % 6}:{t // 6},{t % 6}:{a // 6},{a % 6}"

        scored_moves.append((score, (f, t, a)))

    scored_moves.sort(key=lambda x: x[0], reverse=True)

    best_move = scored_moves[0][1]
    best_val = -float("inf")
    alpha = -float("inf")

    # 2-ply search with alpha-beta pruning over top candidate moves
    top_candidates = scored_moves[:35]

    for ply1_score, (f1, t1, a1) in top_candidates:
        if time.time() - start_time > time_limit:
            break

        b[f1] = 0
        b[t1] = 1
        b[a1] = -1

        opp_moves = generate_legal_moves(b, 2)
        if not opp_moves:
            # Immediate win
            b[a1] = 0
            b[t1] = 0
            b[f1] = 1
            return f"{f1 // 6},{f1 % 6}:{t1 // 6},{t1 % 6}:{a1 // 6},{a1 % 6}"

        opp_min_score = float("inf")

        for f2, t2, a2 in opp_moves:
            b[f2] = 0
            b[t2] = 2
            b[a2] = -1

            eval_val = evaluate(b, 1, 2)

            b[a2] = 0
            b[t2] = 0
            b[f2] = 2

            if eval_val < opp_min_score:
                opp_min_score = eval_val

            # Alpha cutoff (opponent minimizing player 1's score)
            if opp_min_score <= alpha:
                break

        b[a1] = 0
        b[t1] = 0
        b[f1] = 1

        if opp_min_score > best_val:
            best_val = opp_min_score
            best_move = (f1, t1, a1)

        if opp_min_score > alpha:
            alpha = opp_min_score

    f, t, a = best_move
    return f"{f // 6},{f % 6}:{t // 6},{t % 6}:{a // 6},{a % 6}"
