
def policy(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state['dice']
    
    def make_move(order, moves):
        from1 = 'B' if moves[0] == 'bar' else f"A{moves[0]}" if moves[0] is not None else 'P'
        from2 = 'B' if moves[1] == 'bar' else f"A{moves[1]}" if moves[1] is not None else 'P'
        return f"{order}:{from1},{from2}"
    
    # Handle bar checkers
    if my_bar > 0:
        valid_dice = []
        for d in dice:
            target = 23 - d
            if target >= 0 and opp_pts[target] < 2:
                valid_dice.append(d)
        if not valid_dice:
            return make_move('H', (None, None))
        valid_dice.sort(reverse=True)
        if len(valid_dice) >= 2:
            return make_move('H', ('bar', 'bar'))
        else:
            used_die = valid_dice[0]
            if used_die == max(dice):
                return make_move('H', ('bar', None))
            else:
                return make_move('L', ('bar', None))
    
    # Check bearing off
    if all(count == 0 for count in my_pts[6:]) and my_bar == 0:
        bear_moves = []
        for d in dice:
            moved = False
            for p in range(5, -1, -1):
                if my_pts[p] > 0:
                    if p + 1 == d:
                        bear_moves.append(p)
                        moved = True
                        break
                    elif p + 1 < d and not any(my_pts[p+1:6]):
                        bear_moves.append(p)
                        moved = True
                        break
            if not moved:
                bear_moves.append(None)
        bear_moves = [m for m in bear_moves if m is not None]
        if len(bear_moves) == 0:
            return make_move('H', (None, None))
        elif len(bear_moves) == 1:
            if dice[0] >= dice[-1]:
                return make_move('H', (bear_moves[0], None))
            else:
                return make_move('L', (bear_moves[0], None))
        else:
            if max(dice) == dice[0]:
                return make_move('H', (bear_moves[0], bear_moves[1]))
            else:
                return make_move('L', (bear_moves[1], bear_moves[0]))
    
    # Normal moves
    max_score = -float('inf')
    best_order = 'H'
    best_moves = (None, None)
    sorted_dice = sorted(dice, reverse=True)
    
    for order in ['H', 'L'] if len(dice) > 1 else ['H']:
        first = sorted_dice[0] if order == 'H' else sorted_dice[1] if len(dice) > 1 else sorted_dice[0]
        second = sorted_dice[1] if order == 'H' and len(dice) > 1 else None
        
        # First die moves
        for from1 in range(23, -1, -1):
            if my_pts[from1] == 0:
                continue
            to1 = from1 - first
            if to1 < 0 or opp_pts[to1] >= 2:
                continue
            score = 5 * (opp_pts[to1] == 1)
            if (my_pts[to1] + 1) >= 2:
                score += 3
            if my_pts[from1] >= 3:
                score += 1
            score += first
            
            # Second die moves
            if second is not None:
                temp_pts = my_pts.copy()
                temp_pts[from1] -= 1
                temp_pts[to1] += 1
                for from2 in range(23, -1, -1):
                    if temp_pts[from2] == 0:
                        continue
                    to2 = from2 - second
                    if to2 < 0 or opp_pts[to2] >= 2:
                        continue
                    score2 = score + 5 * (opp_pts[to2] == 1)
                    if (temp_pts[to2] + 1) >= 2:
                        score2 += 3
                    if temp_pts[from2] >= 3:
                        score2 += 1
                    score2 += second
                    if score2 > max_score:
                        max_score = score2
                        best_order = order
                        best_moves = (from1, from2)
            else:
                if score > max_score:
                    max_score = score
                    best_order = order
                    best_moves = (from1, None)
    
    if max_score == -float('inf'):
        return make_move('H', (None, None))
    else:
        return make_move(best_order, best_moves)
