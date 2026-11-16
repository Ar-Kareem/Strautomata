
def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    # Sort dice to always have the larger one first
    dice.sort(reverse=True)
    high_die = dice[0]
    low_die = dice[1] if len(dice) == 2 else None

    def can_bear_off():
        return my_off == 0 and all(checker == 0 for checker in my_pts[6:])

    def get_legal_moves(from_point, die):
        to_point = from_point - die
        if to_point < 0:
            return None
        if opp_pts[to_point] < 2:  # Can land on empty or single opponent checkers
            return to_point
        return None

    if my_bar > 0:
        # Must move checker from the bar
        bar_move = get_legal_moves(-1, high_die)  # -1 indicates bar move (B)
        if bar_move is not None:
            if low_die is not None:
                bar_move_low = get_legal_moves(-1, low_die)
                if bar_move_low is not None:
                    return f'H:B,A{bar_move},A{bar_move_low}'
            return f'H:B,A{bar_move}'

    if can_bear_off():
        # Prefer to bear off if possible
        if low_die and (my_pts[high_die] > 0):
            return f'H:A{high_die},A{high_die - low_die}' if (my_pts[high_die - low_die] > 0) else f'H:A{high_die},P'
        
        if my_pts[high_die] > 0:
            return f'H:A{high_die},P'
        
        if low_die and my_pts[low_die] > 0:
            return f'H:A{low_die},P'

    # Regular moves without bearing off
    moves = []
    for move_die, order in [(high_die, 'H'), (low_die, 'L')]:
        if move_die is None:
            continue
        for from_point in range(23, -1, -1):
            legal_move = get_legal_moves(from_point, move_die)
            if legal_move is not None and my_pts[from_point] > 0:
                moves.append(f'{order}:A{from_point},A{legal_move}')
                if low_die:
                    for other_from in range(23, -1, -1):
                        if other_from != from_point:
                            other_legal_move = get_legal_moves(other_from, low_die)
                            if other_legal_move is not None and my_pts[other_from] > 0:
                                return f'{order}:A{from_point},A{other_from}'
                else:
                    return f'{order}:A{from_point},P'

    return 'H:P,P'  # No legal moves
