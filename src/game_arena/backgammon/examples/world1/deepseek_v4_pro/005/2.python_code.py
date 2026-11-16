
import copy

def policy(state: dict) -> str:
    # Helper functions
    def copy_state(s):
        return {
            'my_pts': s['my_pts'][:],
            'opp_pts': s['opp_pts'][:],
            'my_bar': s['my_bar'],
            'opp_bar': s['opp_bar'],
            'my_off': s['my_off'],
            'opp_off': s['opp_off'] if 'opp_off' in s else s['opp_off'],  # key spelling
        }
    # fix possible off key typo
    if 'opp_off' not in state:
        state['opp_off'] = state['opp_off']  # just rename? Actually state is as given
    # but we will use state['opp_off'] as in description; code expects exactly that.
    # Let's assume correct keys.

    def legal_moves_single(s, d):
        my_bar = s['my_bar']
        if my_bar > 0:
            entry = 24 - d
            if 18 <= entry <= 23 and s['opp_pts'][entry] < 2:
                return ['B']
            return []
        moves = []
        # check if bearing off stage
        in_home = True
        for p in range(6, 24):
            if s['my_pts'][p] > 0:
                in_home = False
                break
        if in_home:
            high_p = -1
            for p in range(5, -1, -1):
                if s['my_pts'][p] > 0:
                    high_p = p
                    break
            for p in range(6):
                if s['my_pts'][p] > 0:
                    dest = p - d
                    if dest >= 0 and s['opp_pts'][dest] < 2:
                        moves.append(p)
                    if p == d - 1:
                        moves.append(p)
            if high_p != -1 and d > high_p + 1 and high_p not in moves:
                moves.append(high_p)
            # remove duplicates
            return list(set(moves))
        else:
            for p in range(24):
                if s['my_pts'][p] > 0:
                    dest = p - d
                    if dest >= 0 and s['opp_pts'][dest] < 2:
                        moves.append(p)
            return moves

    def apply_move(s, start, d):
        # start: 'B' or int 0..23
        ns = copy_state(s)
        if start == 'B':
            if ns['my_bar'] == 0:
                return None
            entry = 24 - d
            if not (18 <= entry <= 23) or ns['opp_pts'][entry] >= 2:
                return None
            ns['my_bar'] -= 1
            if ns['opp_pts'][entry] == 1:
                ns['opp_pts'][entry] = 0
                ns['opp_bar'] += 1
            ns['my_pts'][entry] += 1
            return ns
        p = start
        if ns['my_pts'][p] == 0:
            return None
        dest = p - d
        if dest < 0:
            # bearing off, must be in home
            in_home = True
            for x in range(6, 24):
                if ns['my_pts'][x] > 0:
                    in_home = False; break
            if ns['my_bar'] > 0: in_home = False
            if not in_home:
                return None
            # check legal bear off
            legal = False
            if p == d - 1:
                legal = True
            else:
                # highest occupied point
                high_p = -1
                for x in range(5, -1, -1):
                    if ns['my_pts'][x] > 0:
                        high_p = x; break
                if p == high_p and d > high_p + 1:
                    legal = True
            if not legal:
                return None
            ns['my_pts'][p] -= 1
            ns['my_off'] += 1
            return ns
        else:
            if ns['opp_pts'][dest] >= 2:
                return None
            ns['my_pts'][p] -= 1
            if ns['opp_pts'][dest] == 1:
                ns['opp_pts'][dest] = 0
                ns['opp_bar'] += 1
            ns['my_pts'][dest] += 1
            return ns

    def gen_sequences(s, dice_list):
        if not dice_list:
            return [[]]
        d = dice_list[0]
        first = legal_moves_single(s, d)
        seqs = []
        for m in first:
            ns = apply_move(s, m, d)
            if ns is None:
                continue
            for rest in gen_sequences(ns, dice_list[1:]):
                seqs.append([m] + rest)
        return seqs

    def evaluate(s):
        my_off = s['my_off']
        opp_off = s['opp_off']
        my_bar = s['my_bar']
        opp_bar = s['opp_bar']
        my_pips = sum(p * s['my_pts'][p] for p in range(24)) + my_bar * 25
        opp_pips = sum((23 - p) * s['opp_pts'][p] for p in range(24)) + opp_bar * 25
        return (opp_pips - my_pips) + (my_off - opp_off)*50 + (opp_bar - my_bar)*30

    def format_loc(loc):
        if loc == 'B':
            return 'B'
        if loc == 'P':
            return 'P'
        return f'A{loc}'

    dice = state['dice']
    if len(dice) == 0:
        return 'H:P,P'
    if len(dice) ==1:
        d = dice[0]
        moves = legal_moves_single(state, d)
        if moves:
            best = max(moves, key=lambda m: evaluate(apply_move(state, m, d)))
            return f'H:{format_loc(best)},P'
        return 'H:P,P'

    d1, d2 = dice
    high = max(d1, d2)
    low = min(d1, d2)

    best_seq = None
    best_val = -float('inf')
    best_order = 'H'

    # try both dice orders
    for order, dies in [('H', [high, low]), ('L', [low, high])]:
        seqs = gen_sequences(state, dies)
        for seq in seqs:
            # apply sequence
            cur = state
            for m, d in zip(seq, dies):
                cur = apply_move(cur, m, d)
                if cur is None: break
            else:
                val = evaluate(cur)
                if val > best_val:
                    best_val = val
                    best_seq = seq
                    best_order = order

    if best_seq is not None:
        loc1 = format_loc(best_seq[0])
        loc2 = format_loc(best_seq[1])
        return f'{best_order}:{loc1},{loc2}'

    # cannot play both, try high die only
    moves_high = legal_moves_single(state, high)
    if moves_high:
        best = max(moves_high, key=lambda m: evaluate(apply_move(state, m, high)))
        return f'H:{format_loc(best)},P'
    # else pass
    return 'H:P,P'
