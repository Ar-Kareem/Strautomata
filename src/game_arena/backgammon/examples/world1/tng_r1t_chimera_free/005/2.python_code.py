
import numpy as np

def policy(state: dict) -> str:
    def all_in_home(my_pts):
        return all(count == 0 for count in my_pts[6:])

    def can_bear_off(my_pts):
        return all_in_home(my_pts)

    def can_hit(opp_pts, dest):
        return dest >= 0 and opp_pts[dest] == 1

    def can_move(p, die, my_pts, opp_pts, can_bear_off_flag):
        if p < 0 or p >= 24 or my_pts[p] == 0:
            return False
        dest = p - die
        if can_bear_off_flag:
            if dest < -1:
                return False
            if dest < 0:
                return True
            return opp_pts[dest] < 2
        if dest < 0:
            return False
        return opp_pts[dest] < 2

    def generate_bar_actions(state):
        dice = sorted(state['dice'], reverse=True)
        possible_orders = [('H', dice)] if len(dice) == 1 else [('H', dice), ('L', reversed(dice))]
        actions = []

        for order_label, ordered_dice in possible_orders:
            die1, die2 = (ordered_dice[0], ordered_dice[1]) if len(ordered_dice) > 1 else (ordered_dice[0], None)
            entry_point1 = 24 - die1
            if entry_point1 < 0 or entry_point1 >= 24 or state['opp_pts'][entry_point1] >= 2:
                continue
            from1 = 'B'
            from2_candidates = []
            if die2 is not None:
                for p in range(24):
                    if state['my_pts'][p] > 0 and can_move(p, die2, state['my_pts'], state['opp_pts'], all_in_home(state['my_pts'])):
                        from2_candidates.append(f"A{p}")
                if not from2_candidates:
                    from2_candidates.append('P')
            else:
                from2_candidates.append('P')
            for from2 in from2_candidates:
                actions.append((order_label, from1, from2))
        return actions

    def generate_normal_actions(state):
        dice = state['dice']
        if len(dice) == 0:
            return []
        possible_orders = []
        if len(dice) == 1:
            possible_orders.append(('H', [dice[0]]))
        else:
            possible_orders.append(('H', [max(dice), min(dice)]))
            possible_orders.append(('L', [min(dice), max(dice)]))

        actions = []
        can_bear_off_flag = can_bear_off(state['my_pts'])

        for order_label, (die1, die2) in possible_orders if len(dice) > 1 else [('H', (dice[0], None))]:
            for p1 in range(24):
                if state['my_pts'][p1] == 0 or not can_move(p1, die1, state['my_pts'], state['opp_pts'], can_bear_off_flag):
                    continue
                from1 = f"A{p1}"
                used_p1 = (p1 - die1) if (not can_bear_off_flag or p1 - die1 >= 0) else -1
                if die2 is None:
                    actions.append((order_label, from1, 'P'))
                    continue
                for p2 in range(24):
                    if state['my_pts'][p2] == 0 or p2 == p1 and state['my_pts'][p2] < 2:
                        continue
                    if not can_move(p2, die2, state['my_pts'], state['opp_pts'], can_bear_off_flag):
                        continue
                    actions.append((order_label, from1, f"A{p2}"))
                if not any(a[1] == from1 for a in actions):
                    actions.append((order_label, from1, 'P'))
        return actions

    def score_action(action, state):
        order_label, from1, from2 = action
        score = 0
        for move in [from1, from2]:
            if move == 'B':
                die = 24 - int(from1.split(',')[0][2:]) if from1.startswith('A') else 0
                entry_point = 24 - die
                score += (24 - entry_point) * 10
            elif move.startswith('A'):
                p = int(move[2:])
                die = int(from1.split(',')[0][2:]) if move == from1 else int(from2.split(',')[0][2:]) if from2.startswith('A') else 0
                dest = p - die
                if dest < 0:
                    score += 1000
                else:
                    if state['opp_pts'][dest] == 1:
                        score += 500
                    if state['my_pts'][dest] + 1 >= 2:
                        score += 300
                    score += (24 - p) * 10
        return score

    if state['my_bar'] > 0:
        possible_actions = generate_bar_actions(state)
        if not possible_actions:
            return "H:P,P"
    else:
        possible_actions = generate_normal_actions(state)
        if not possible_actions:
            return "H:P,P"

    best_action = max(possible_actions, key=lambda a: score_action(a, state), default=None)
    if not best_action:
        return "H:P,P"
    order_label, from1, from2 = best_action
    return f"{order_label}:{from1},{from2}"
