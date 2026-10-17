
import copy

def policy(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state['dice']
    
    if my_bar > 0:
        return handle_bar_case(state)
    else:
        return handle_no_bar_case(state)

def handle_bar_case(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state['dice']
    valid_dice = [d for d in dice if opp_pts[24 - d] < 2]
    
    if not valid_dice:
        return 'H:P,P'
    
    if len(dice) == 1:
        return 'H:B,P' if dice[0] in valid_dice else 'H:P,P'
    
    d1, d2 = sorted(dice, reverse=True)
    
    if d1 in valid_dice and d2 in valid_dice:
        if my_bar >= 2:
            return 'H:B,B'
        else:
            from2 = find_valid_move_for_single_die(my_pts, opp_pts, d2)
            if from2 is not None:
                return f'H:B,A{from2}'
            else:
                return 'H:B,P'
    elif d1 in valid_dice:
        return 'H:B,P'
    elif d2 in valid_dice:
        return 'L:B,P'
    else:
        return 'H:P,P'

def find_valid_move_for_single_die(my_pts, opp_pts, die):
    for x in range(23, -1, -1):
        if my_pts[x] > 0:
            dest = x - die
            if dest >= 0:
                if opp_pts[dest] < 2:
                    return x
            else:
                all_home = all(my_pts[i] == 0 for i in range(6, 24))
                if all_home:
                    return x
    return None

def handle_no_bar_case(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    dice = state['dice']
    all_in_home = all(my_pts[i] == 0 for i in range(6, 24))
    
    if all_in_home:
        return handle_bear_off(state)
    else:
        return handle_regular_moves(state)

def handle_bear_off(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    dice = state['dice']
    
    if len(dice) == 1:
        die = dice[0]
        for x in range(5, -1, -1):
            if my_pts[x] > 0:
                # Can bear off if die >= x or all checkers in home
                if die >= x or all(my_pts[i] == 0 for i in range(6, 24)):
                    return f'H:A{x},P'
        return 'H:P,P'
    else:
        d1, d2 = sorted(dice, reverse=True)
        from1 = None
        from2 = None
        
        for x in range(5, -1, -1):
            if my_pts[x] > 0:
                if d1 >= x or all(my_pts[i] == 0 for i in range(6, 24)):
                    from1 = x
        for x in range(5, -1, -1):
            if my_pts[x] > 0 and x != from1:
                if d2 >= x or all(my_pts[i] == 0 for i in range(6, 24)):
                    from2 = x
        
        if from1 is not None and from2 is not None:
            return f'H:A{from1},A{from2}'
        elif from1 is not None:
            return f'H:A{from1},P'
        else:
            for x in range(5, -1, -1):
                if my_pts[x] > 0:
                    if d2 >= x or all(my_pts[i] == 0 for i in range(6, 24)):
                        from2 = x
                        return f'L:A{from2},P'
            return 'H:P,P'

def handle_regular_moves(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    dice = state['dice']
    
    if len(dice) == 1:
        die = dice[0]
        from1 = find_valid_move_for_single_die(my_pts, opp_pts, die)
        if from1 is not None:
            return f'H:A{from1},P'
        else:
            return 'H:P,P'
    else:
        d1, d2 = sorted(dice, reverse=True)
        from1_higher = find_valid_move_for_single_die(my_pts, opp_pts, d1)
        from2_lower = find_valid_move_for_single_die(my_pts, opp_pts, d2)
        from1_lower = find_valid_move_for_single_die(my_pts, opp_pts, d2)
        from2_higher = find_valid_move_for_single_die(my_pts, opp_pts, d1)
        
        if from1_higher is not None and from2_lower is not None:
            return f'H:A{from1_higher},A{from2_lower}'
        elif from1_higher is not None:
            return f'H:A{from1_higher},P'
        elif from1_lower is not None and from2_higher is not None:
            return f'L:A{from1_lower},A{from2_higher}'
        elif from1_lower is not None:
            return f'L:A{from1_lower},P'
        else:
            return 'H:P,P'
