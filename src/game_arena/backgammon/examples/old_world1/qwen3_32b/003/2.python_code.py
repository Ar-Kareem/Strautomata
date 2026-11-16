
import numpy as np

def policy(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    my_off = state['my_off']
    dice = state['dice']
    if not dice:
        return "H:P,P"
    
    def is_bearable(s, die):
        return s - die < 0 and all(my_pts[pos] == 0 for pos in range(6, 24))
    
    def get_home_points():
        return sum(p for p in my_pts[:6])
    
    def find_best_move(die, from_the_bar=False):
        if from_the_bar:
            dest_bar = 24 - die
            if not (0 <= dest_bar < 24) or opp_pts[dest_bar] >= 2:
                return None
            return "B"
        else:
            for s in range(23, -1, -1):
                if my_pts[s] > 0:
                    if is_bearable(s, die):
                        return s
                    dest = s - die
                    if 0 <= dest < 24 and (opp_pts[dest] < 2):
                        return s
            return None
    
    # Check mandatory bar moves
    if my_bar > 0:
        # Try to use higher die first for bar entry
        for d in [dice[0]] if len(dice) == 1 else [dice[1], dice[0]]:
            first_move = find_best_move(d, from_the_bar=True)
            if first_move is None:
                # Try other orders
                for d2 in [dice[0]] if len(dice) == 1 else [dice[0]]:
                    first_move = find_best_move(d2, from_the_bar=True)
                    if first_move is not None:
                        return f"L:{first_move},P"
        if first_move is None:
            return "H:P,P"
        # After first bar move, handle second move
        new_my_bar = my_bar -1
        new_my_pts = my_pts.copy()
        new_my_pts[24 - first_move] += 1
        second_dice = dice[0] if dice[1] == first_move else dice[1]
        for s in range(23, -1, -1):
            if new_my_pts[s] > 0:
                dest = s - second_dice
                if is_bearable(s, second_dice):
                    return f"H:B,A{s}"
                elif 0 <= dest < 24 and opp_pts[dest] < 2:
                    return f"H:B,A{s}"
        if new_my_pts[dest_higher] > 0:
            return f"H:B,A{24 - first_move}" if len(dice) == 1 else f"H:B,A{24 - first_move}"
        else:
            return "H:B,P"
    
    # Check if bearing off is allowed
    home_checkers = all(p == 0 for p in my_pts[6:])
    if home_checkers:
        # Bearing-off strategy
        s_high, s_low = -1, -1
        for s in range(5, -1, -1):
            if my_pts[s] > 0:
                if dice[0] <= s and all(my_pts[pos] == 0 for pos in range(s, 6, 18)):
                    if s_high == -1:
                        s_high = s
                    elif s_high >=0 and s > s_high:
                        s_low = s_high
                        s_high = s
                    else:
                        s_low = s
        if s_high >= 0 and s_low >=0:
            return f"H:A{s_high},A{s_low}"
        elif s_high >=0:
            return f"H:A{s_high},P"
        else:
            # cannot use any die to bear off
            return "H:P,P"
    
    # Normal move strategy
    first_move, second_move = None, None
    # Use higher die first
    for s in range(23, -1, -1):
        if my_pts[s] >0:
            dest = s - max(dice)
            if 0 <= dest <24 and opp_pts[dest] <2:
                first_move = s
                break
    if first_move is not None:
        moved = my_pts.copy()
        moved[first_move] -=1
        moved[dest] +=1
        for s2 in range(23, -1, -1):
            if moved[s2] >0:
                dest2 = s2 - min(dice) if max(dice) != min(dice) else s2 - max(dice)
                if 0 <= dest2 <24 and opp_pts[dest2] <2 and (is_bearable(s2, min(dice)) or s2 - min(dice) >=0):
                    second_move = s2
                    break
        if second_move is not None:
            return f"H:A{first_move},A{second_move}"
        else:
            return f"H:A{first_move},P"
    # If only lower die is playable
    elif max(dice) != min(dice):
        for s in range(23, -1, -1):
            if my_pts[s] >0:
                if s - min(dice) <0:
                    return f"L:A{s},P"
                elif opp_pts[s - min(dice)] <2:
                    return f"L:A{s},P"
        return "H:P,P"
    return "H:P,P"
