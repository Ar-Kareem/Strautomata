
from typing import List, Tuple, Dict, Optional

Square = Tuple[int, int]
Move = Tuple[Square, Square]

BOARD_SIZE = 8
INF = 10**9

# ---------- Utility ----------

def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8

def dark_square(r: int, c: int) -> bool:
    return (r + c) % 2 == 1

def to_set(lst):
    return set(lst)

def clone_state(state):
    return {
        'my_men': set(state['my_men']),
        'my_kings': set(state['my_kings']),
        'opp_men': set(state['opp_men']),
        'opp_kings': set(state['opp_kings']),
        'color': state['color'],
    }

def make_state(my_men, my_kings, opp_men, opp_kings, color):
    return {
        'my_men': set(my_men),
        'my_kings': set(my_kings),
        'opp_men': set(opp_men),
        'opp_kings': set(opp_kings),
        'color': color,
    }

def promotion_row(color: str) -> int:
    return 0 if color == 'b' else 7

def man_dirs(color: str):
    # black moves downward to lower row values, white upward to higher row values
    return [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]

def king_dirs():
    return [(-1, -1), (-1, 1), (1, -1), (1, 1)]

def occupied(state):
    return state['my_men'] | state['my_kings'] | state['opp_men'] | state['opp_kings']

def swap_perspective(state):
    return {
        'my_men': set(state['opp_men']),
        'my_kings': set(state['opp_kings']),
        'opp_men': set(state['my_men']),
        'opp_kings': set(state['my_kings']),
        'color': 'w' if state['color'] == 'b' else 'b'
    }

# ---------- Move generation ----------
# A move sequence is represented as:
# {
#   'path': [start, ..., final],
#   'captures': int,
#   'promotes': bool
# }

def piece_is_king(state, sq: Square, mine: bool = True) -> bool:
    return sq in (state['my_kings'] if mine else state['opp_kings'])

def piece_is_man(state, sq: Square, mine: bool = True) -> bool:
    return sq in (state['my_men'] if mine else state['opp_men'])

def gen_simple_moves_for_piece(state, sq: Square, is_king: bool) -> List[dict]:
    res = []
    dirs = king_dirs() if is_king else man_dirs(state['color'])
    occ = occupied(state)
    for dr, dc in dirs:
        r, c = sq[0] + dr, sq[1] + dc
        if in_bounds(r, c) and dark_square(r, c) and (r, c) not in occ:
            promotes = (not is_king and r == promotion_row(state['color']))
            res.append({'path': [sq, (r, c)], 'captures': 0, 'promotes': promotes})
    return res

def _gen_captures_from(state, sq: Square, is_king: bool, path: List[Square], results: List[dict]):
    found = False
    occ = occupied(state)
    dirs = king_dirs() if is_king else man_dirs(state['color'])
    for dr, dc in dirs:
        mr, mc = sq[0] + dr, sq[1] + dc
        lr, lc = sq[0] + 2 * dr, sq[1] + 2 * dc
        if not (in_bounds(mr, mc) and in_bounds(lr, lc) and dark_square(lr, lc)):
            continue
        if (mr, mc) in state['opp_men'] or (mr, mc) in state['opp_kings']:
            if (lr, lc) not in occ:
                found = True
                new_state = clone_state(state)
                # remove moving piece
                if is_king:
                    new_state['my_kings'].remove(sq)
                else:
                    new_state['my_men'].remove(sq)
                # remove captured piece
                if (mr, mc) in new_state['opp_men']:
                    new_state['opp_men'].remove((mr, mc))
                else:
                    new_state['opp_kings'].remove((mr, mc))

                landed = (lr, lc)
                now_king = is_king
                # standard checkers commonly stops continuation on promotion; enforce that for safety
                if (not is_king) and lr == promotion_row(state['color']):
                    new_state['my_kings'].add(landed)
                    now_king = True
                    results.append({
                        'path': path + [landed],
                        'captures': len(path),  # corrected later by path length
                        'promotes': True
                    })
                else:
                    if now_king:
                        new_state['my_kings'].add(landed)
                    else:
                        new_state['my_men'].add(landed)
                    _gen_captures_from(new_state, landed, now_king, path + [landed], results)

    if not found and len(path) > 1:
        promotes = (not is_king and path[-1][0] == promotion_row(state['color']))
        results.append({
            'path': path[:],
            'captures': len(path) - 1,
            'promotes': promotes
        })

def gen_captures_for_piece(state, sq: Square, is_king: bool) -> List[dict]:
    results = []
    _gen_captures_from(state, sq, is_king, [sq], results)
    # fix any malformed capture count from promotion termination branch
    for r in results:
        r['captures'] = len(r['path']) - 1
    return results

def legal_sequences(state) -> List[dict]:
    captures = []
    simples = []

    for sq in list(state['my_men']):
        caps = gen_captures_for_piece(state, sq, False)
        if caps:
            captures.extend(caps)
        else:
            simples.extend(gen_simple_moves_for_piece(state, sq, False))

    for sq in list(state['my_kings']):
        caps = gen_captures_for_piece(state, sq, True)
        if caps:
            captures.extend(caps)
        else:
            simples.extend(gen_simple_moves_for_piece(state, sq, True))

    if captures:
        max_caps = max(m['captures'] for m in captures)
        best_caps = [m for m in captures if m['captures'] == max_caps]
        return best_caps
    return simples

def apply_sequence(state, seq: dict):
    path = seq['path']
    start = path[0]
    is_king = start in state['my_kings']

    new_state = clone_state(state)

    if is_king:
        new_state['my_kings'].remove(start)
    else:
        new_state['my_men'].remove(start)

    cur = start
    for nxt in path[1:]:
        if abs(nxt[0] - cur[0]) == 2:
            mr = (cur[0] + nxt[0]) // 2
            mc = (cur[1] + nxt[1]) // 2
            if (mr, mc) in new_state['opp_men']:
                new_state['opp_men'].remove((mr, mc))
            elif (mr, mc) in new_state['opp_kings']:
                new_state['opp_kings'].remove((mr, mc))
        cur = nxt

    end = path[-1]
    if is_king:
        new_state['my_kings'].add(end)
    else:
        if end[0] == promotion_row(state['color']):
            new_state['my_kings'].add(end)
        else:
            new_state['my_men'].add(end)

    return swap_perspective(new_state)

# ---------- Evaluation ----------

def piece_advancement(color: str, sq: Square) -> int:
    r, _ = sq
    return (7 - r) if color == 'b' else r

def vulnerable_after_move(state, sq: Square) -> bool:
    # Approximate: after perspective swap, can opponent capture this square?
    opp_state = swap_perspective(state)
    target = sq
    occ = occupied(opp_state)
    for op in opp_state['my_men']:
        for dr, dc in man_dirs(opp_state['color']):
            mr, mc = op[0] + dr, op[1] + dc
            lr, lc = op[0] + 2 * dr, op[1] + 2 * dc
            if in_bounds(mr, mc) and in_bounds(lr, lc) and dark_square(lr, lc):
                if (mr, mc) == target and (lr, lc) not in occ:
                    return True
    for op in opp_state['my_kings']:
        for dr, dc in king_dirs():
            mr, mc = op[0] + dr, op[1] + dc
            lr, lc = op[0] + 2 * dr, op[1] + 2 * dc
            if in_bounds(mr, mc) and in_bounds(lr, lc) and dark_square(lr, lc):
                if (mr, mc) == target and (lr, lc) not in occ:
                    return True
    return False

def evaluate(state) -> int:
    my_men = len(state['my_men'])
    my_kings = len(state['my_kings'])
    opp_men = len(state['opp_men'])
    opp_kings = len(state['opp_kings'])

    if my_men + my_kings == 0:
        return -100000
    if opp_men + opp_kings == 0:
        return 100000

    score = 0

    # Material
    score += 100 * (my_men - opp_men)
    score += 175 * (my_kings - opp_kings)

    # Advancement and promotion pressure
    for sq in state['my_men']:
        adv = piece_advancement(state['color'], sq)
        score += 8 * adv
        if sq[0] == (1 if state['color'] == 'b' else 6):
            score += 12
    opp_color = 'w' if state['color'] == 'b' else 'b'
    for sq in state['opp_men']:
        adv = piece_advancement(opp_color, sq)
        score -= 8 * adv
        if sq[0] == (1 if opp_color == 'b' else 6):
            score -= 12

    # Center control
    center = {(3, 2), (3, 4), (4, 3), (4, 5), (2, 3), (5, 4)}
    for sq in state['my_men'] | state['my_kings']:
        if sq in center:
            score += 10
    for sq in state['opp_men'] | state['opp_kings']:
        if sq in center:
            score -= 10

    # Back-rank guard
    back = 7 if state['color'] == 'b' else 0
    opp_back = 7 if opp_color == 'b' else 0
    for sq in state['my_men']:
        if sq[0] == back:
            score += 6
    for sq in state['opp_men']:
        if sq[0] == opp_back:
            score -= 6

    # Mobility
    my_moves = legal_sequences(state)
    if not my_moves:
        return -100000
    score += 3 * len(my_moves)

    opp_moves = legal_sequences(swap_perspective(state))
    if not opp_moves:
        return 100000
    score -= 3 * len(opp_moves)

    return score

# ---------- Search ----------

def order_moves(state, moves: List[dict]) -> List[dict]:
    scored = []
    for m in moves:
        s = 0
        s += 500 * m['captures']
        if m['promotes']:
            s += 120
        end = m['path'][-1]
        if end in {(3, 2), (3, 4), (4, 3), (4, 5), (2, 3), (5, 4)}:
            s += 15
        # tentative safety check on applied state
        ns = apply_sequence(state, m)
        # after apply_sequence, perspective swapped; our moved piece is now in opp_*.
        # infer vulnerability from original side by checking before swap on reconstructed state
        pre_swap = swap_perspective(ns)
        if not vulnerable_after_move(pre_swap, end):
            s += 20
        scored.append((s, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]

def alphabeta(state, depth: int, alpha: int, beta: int) -> int:
    moves = legal_sequences(state)
    if depth == 0 or not moves:
        return evaluate(state)

    moves = order_moves(state, moves)

    value = -INF
    for m in moves:
        child = apply_sequence(state, m)
        score = -alphabeta(child, depth - 1, -beta, -alpha)
        if score > value:
            value = score
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break
    return value

# ---------- Public policy ----------

def policy(my_men, my_kings, opp_men, opp_kings, color) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    state = make_state(my_men, my_kings, opp_men, opp_kings, color)
    moves = legal_sequences(state)

    # Guaranteed legal fallback
    if not moves:
        # Should not happen in valid non-terminal inputs, but be defensive.
        all_my = list(state['my_men']) + list(state['my_kings'])
        if all_my:
            return (all_my[0], all_my[0])
        return ((0, 1), (0, 1))

    moves = order_moves(state, moves)

    # Adaptive depth by complexity
    piece_count = len(my_men) + len(my_kings) + len(opp_men) + len(opp_kings)
    if piece_count <= 8:
        depth = 7
    elif piece_count <= 12:
        depth = 6
    elif piece_count <= 18:
        depth = 5
    else:
        depth = 4

    best_move = moves[0]
    best_score = -INF
    alpha = -INF
    beta = INF

    for m in moves:
        child = apply_sequence(state, m)
        score = -alphabeta(child, depth - 1, -beta, -alpha)
        # tie-breakers
        if score > best_score:
            best_score = score
            best_move = m
        elif score == best_score:
            # Prefer more captures, then promotion, then centralization
            bm = best_move
            key_m = (m['captures'], int(m['promotes']), m['path'][-1] in {(3,2),(3,4),(4,3),(4,5),(2,3),(5,4)})
            key_b = (bm['captures'], int(bm['promotes']), bm['path'][-1] in {(3,2),(3,4),(4,3),(4,5),(2,3),(5,4)})
            if key_m > key_b:
                best_move = m
        if score > alpha:
            alpha = score

    path = best_move['path']
    # Return first step only, as required by the API.
    if len(path) >= 2:
        return (path[0], path[1])

    # Final defensive fallback
    m = moves[0]
    p = m['path']
    return (p[0], p[1]) if len(p) >= 2 else (p[0], p[0])
