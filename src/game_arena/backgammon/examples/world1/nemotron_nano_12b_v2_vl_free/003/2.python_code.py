
import itertools
import functools

def policy(state):
    my_pts = state['my_pts']
    opp_pts = [x if x == state['opp_pts'][i] else [] for i, x in enumerate(my_pts)]
    my_bar = state['my_bar']
    dice = state['dice']
    all_moves = []

    # Generate possible bar moves first
    if my_bar > 0:
        sorted_dice = sorted(dice, reverse=True)
        entry_candidates = []

        # First, find all entry points for each die
        entry_per_die = []
        for die in dice:
            if die - 1 >= 0 and die - 1 < 24 and opp_pts[die] <= 1:
                entry_per_die.append(die)

        # Generate all combinations of entries
        entry_moves = []
        if len(entry_per_die) >= len(dice):
            for entry in itertools.combinations(entry_per_die, len(dice)):
                if len(entry) == len(dice):
                    hs = list(sorted(entry, reverse=True))
                    ls = list(sorted(entry, reverse=False))
                    move_str = build_bar_entry_move('H', hs, 'L', ls)
                    entry_moves.append(move_str)

        all_moves.extend(entry_moves)
    else:
        # Generate normal moves (non-bar)
        normal_moves = []
        sorted_dice = sorted(dice, reverse=True)
        for move in itertools.permutations(sorted_dice, len(dice)):
            move_moves = generate_checker_moves(my_pts, my_bar, opp_pts, move, 0)
            valid_move_str = None
            for move_str, trailing_moves in move_moves[:2]:
                if valid_move_str is None:
                    valid_move_str = move_str

            if valid_move_str is not None:
                normal_moves.append(valid_move_str)

        # Filter out moves with gaps
        valid_normal_moves = []
        for move_str in normal_moves:
            for checker in get_all_checkers_from_move(move_str, my_bar, opp_pts):
                if checker in my_pts:
                    if checker not in valid_normal_moves:
                        valid_normal_moves.append(move_str)

        all_moves.extend(valid_normal_moves)

    # Select best move using greedy H/L strategy for ordering
    best_move = None
    for move in all_moves:
        potential_score = get_score(my_pts, opp_pts, dice, move)
        if best_move is None or potential_score > best_score:
            best_move = move
            best_score = potential_score

    # Default to first ordered move if no valid one found
    return best_move or ordered_first_descent_h_move()
