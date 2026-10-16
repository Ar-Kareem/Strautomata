
def policy(state: dict) -> str:
    my_pts = state['my_pts']
    my_bar = state['my_bar']
    dice = state['dice']
    
    if my_bar > 0:
        if len(dice) == 2:
            return "H:B,P"
        else:
            return "H:B,P"
    
    if len(dice) == 2:
        high_die = max(dice)
        low_die = min(dice)
        
        first_move = None
        second_move = None
        
        for i in range(24):
            if my_pts[i] > 0:
                first_move = f"A{i}"
                break
        
        if first_move is None:
            return "H:P,P"
        
        first_point_index = int(first_move[1:])
        if my_pts[first_point_index] >= 2:
            for i in range(24):
                if my_pts[i] > 0:
                    second_move = f"A{i}"
                    break
        else:
            for i in range(24):
                if my_pts[i] > 0 and i != first_point_index:
                    second_move = f"A{i}"
                    break
        
        if second_move is None:
            if my_pts[first_point_index] >= 2:
                second_move = first_move
            else:
                return f"H:{first_move},P"
        
        return f"H:{first_move},{second_move}"
    else:
        first_move = None
        for i in range(24):
            if my_pts[i] > 0:
                first_move = f"A{i}"
                break
        if first_move is None:
            return "H:P,P"
        return f"H:{first_move},P"
