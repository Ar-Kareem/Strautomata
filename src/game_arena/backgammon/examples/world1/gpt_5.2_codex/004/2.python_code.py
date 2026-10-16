
import math
from typing import List, Dict, Tuple

def copy_state(st: dict) -> dict:
    return {
        'my_pts': st['my_pts'][:],
        'opp_pts': st['opp_pts'][:],
        'my_bar': st['my_bar'],
        'opp_bar': st['opp_bar'],
        'my_off': st['my_off'],
        'opp_off': st['opp_off']
    }

def all_in_home(st: dict) -> bool:
    return st['my_bar'] == 0 and sum(st['my_pts'][6:]) == 0

def generate_moves_for_die(st: dict, die: int) -> List[Tuple[str, dict, int]]:
    moves = []
    if die is None:
        return moves
    # If bar has checkers, must move from bar
    if st['my_bar'] > 0:
        dest = 24 - die
        if 0 <= dest <= 23 and st['opp_pts'][dest] < 2:
            new_st = copy_state(st)
            new_st['my_bar'] -= 1
            hit = 0
            if new_st['opp_pts'][dest] == 1:
                new_st['opp_pts'][dest] = 0
                new_st['opp_bar'] += 1
                hit = 1
            new_st['my_pts'][dest] += 1
            moves.append(("B", new_st, hit))
        return moves

    in_home = all_in_home(st)
    for i in range(24):
        if st['my_pts'][i] == 0:
            continue
        dest = i - die
        if dest >= 0:
            if st['opp_pts'][dest] >= 2:
                continue
            new_st = copy_state(st)
            new_st['my_pts'][i] -= 1
            hit = 0
            if new_st['opp_pts'][dest] == 1:
                new_st['opp_pts'][dest] = 0
                new_st['opp_bar'] += 1
                hit = 1
            new_st['my_pts'][dest] += 1
            moves.append((f"A{i}", new_st, hit))
        else:
            # Bearing off
            if not in_home:
                continue
            # Can bear off if no checkers on higher points (i+1..5)
            if any(st['my_pts'][j] > 0 for j in range(i+1, 6)):
                continue
            new_st = copy_state(st)
            new_st['my_pts'][i] -= 1
            new_st['my_off'] += 1
            moves.append((f"A{i}", new_st, 0))
    return moves

def generate_sequences(st: dict, dice_order: List[int]) -> List[Tuple[List[str], dict, int]]:
    seqs = [([], st, 0)]
    for die in dice_order:
        new_seqs = []
        for moves, cur_st, hits in seqs:
            legal = generate_moves_for_die(cur_st, die)
            if not legal:
                new_seqs.append((moves + ["P"], cur_st, hits))
            else:
                for frm, nxt_st, h in legal:
                    new_seqs.append((moves + [frm], nxt_st, hits + h))
        seqs = new_seqs
    return seqs

def evaluate(st: dict, hits: int) -> float:
    my_pip = sum((i + 1) * st['my_pts'][i] for i in range(24)) + 25 * st['my_bar']
    opp_pip = sum((24 - i) * st['opp_pts'][i] for i in range(24)) + 25 * st['opp_bar']
    blots = sum(1 for i in range(24) if st['my_pts'][i] == 1)
    points = sum(1 for i in range(24) if st['my_pts'][i] >= 2)

    score = 0.0
    score += 100 * (st['my_off'] - st['opp_off'])
    score += (opp_pip - my_pip)
    score += 15 * hits
    score += 10 * st['opp_bar'] - 20 * st['my_bar']
    score += 2 * points - 2 * blots
    return score

def policy(state: dict) -> str:
    dice = state.get('dice', [])
    if len(dice) == 0:
        return "H:P,P"

    orders = []
    if len(dice) == 1:
        orders.append(([dice[0], None], 'H'))
    else:
        d1, d2 = dice[0], dice[1]
        if d1 == d2:
            orders.append(([d1, d2], 'H'))
        else:
            high, low = max(d1, d2), min(d1, d2)
            orders.append(([high, low], 'H'))
            orders.append(([low, high], 'L'))

    sequences = []
    for dice_order, order_char in orders:
        seqs = generate_sequences(state, dice_order)
        for moves, st, hits in seqs:
            if len(moves) < 2:
                moves = moves + ["P"] * (2 - len(moves))
            sequences.append({
                'order': order_char,
                'moves': moves,
                'state': st,
                'hits': hits
            })

    if not sequences:
        return "H:P,P"

    def used_count(seq):
        return sum(1 for m in seq['moves'] if m != "P")

    max_used = max(used_count(s) for s in sequences)
    sequences = [s for s in sequences if used_count(s) == max_used]

    if len(dice) == 2 and dice[0] != dice[1] and max_used == 1:
        def uses_high(seq):
            if seq['order'] == 'H':
                return seq['moves'][0] != "P"
            else:
                return seq['moves'][1] != "P"
        if any(uses_high(s) for s in sequences):
            sequences = [s for s in sequences if uses_high(s)]

    best = None
    best_score = -1e18
    for s in sequences:
        score = evaluate(s['state'], s['hits'])
        if score > best_score:
            best_score = score
            best = s

    if best is None:
        return "H:P,P"

    return f"{best['order']}:{best['moves'][0]},{best['moves'][1]}"
