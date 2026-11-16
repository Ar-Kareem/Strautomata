
import itertools

def policy(state: dict) -> str:
    def evaluate_move(move_str, state):
        score = 0
        order, moves_part = move_str.split(':')
        moves = moves_part.split(',')
        dice = sorted(state['dice'], reverse=(order == 'H'))
        all_in_home = sum(state['my_pts'][:18]) == 0

        for i in range(len(moves)):
            move = moves[i]
            if move == 'P' or i >= len(dice):
                continue
            die = dice[i]
            if move == 'B':
                dest = die - 1
                if state['opp_pts'][dest] == 1:
                    score += 200  # Hitting opponent blot
                if dest >= 18:
                    score += 50  # Entering into home board
                if state['my_pts'][dest] + 1 >= 2:
                    score += 100  # Making a point
            else:
                from_pos = int(move[1:]) if move.startswith('A') else None
                if from_pos is None:
                    continue
                dest = from_pos - die
                if dest < 0:
                    if all_in_home:
                        score += 1000  # Bearing off
                    continue
                if state['opp_pts'][dest] >= 2:
                    continue  # Blocked, invalid move
                if state['opp_pts'][dest] == 1:
                    score += 200  # Hitting opponent blot
                current_my = state['my_pts'][dest]
                if current_my == 1:
                    score += 150  # Making a point
                elif current_my == 0:
                    score += 50  # New point
                if state['my_pts'][from_pos] == 1 and from_pos < 18:
                    score -= 100  # Leaving a blot in outer board
        return score

    def generate_bar_moves(state):
        bar_moves = []
        dice = state['dice']
        if not dice or state['my_bar'] == 0:
            return []
        for order in ['H', 'L']:
            sorted_dice = sorted(dice, reverse=(order == 'H'))
            usable = []
            from1 = from2 = 'P'
            die1 = sorted_dice[0] if len(sorted_dice) > 0 else None
            die2 = sorted_dice[1] if len(sorted_dice) > 1 else None

            if die1 is not None:
                entry1 = die1 - 1
                if state['opp_pts'][entry1] < 2:
                    from1 = 'B'
                    usable.append(die1)
            if die2 is not None:
                entry2 = die2 - 1
                remaining_bar = state['my_bar'] - (1 if from1 == 'B' else 0)
                if remaining_bar > 0 and state['opp_pts'][entry2] < 2:
                    from2 = 'B'
                    usable.append(die2)
                else:
                    if from1 == 'B' and die2 is not None:
                        possible_from = entry1
                        dest = possible_from - die2
                        if dest >= 0 and state['opp_pts'][dest] < 2:
                            from2 = f"A{possible_from}"
                        elif dest < 0 and sum(state['my_pts'][:18]) == 0:
                            from2 = f"A{possible_from}"
                        else:
                            from2 = 'P'
            move_str = f"{order}:{from1},{from2}"
            bar_moves.append(move_str)
        return bar_moves

    def generate_regular_moves(state):
        regular_moves = []
        dice = state['dice']
        all_in_home = sum(state['my_pts'][:18]) == 0
        if not dice:
            return ['H:P,P']

        for order in ['H', 'L']:
            sorted_dice = sorted(dice, reverse=(order == 'H'))
            die1 = sorted_dice[0] if len(sorted_dice) > 0 else None
            die2 = sorted_dice[1] if len(sorted_dice) > 1 else None

            possible_first = []
            for from_pos in range(24):
                if state['my_pts'][from_pos] == 0:
                    continue
                dest = from_pos - die1 if die1 is not None else -1
                if dest < 0:
                    if all_in_home:
                        possible_first.append(f"A{from_pos}")
                    continue
                if state['opp_pts'][dest] < 2:
                    possible_first.append(f"A{from_pos}")

            if die2 is None:
                for from1 in possible_first:
                    move_str = f"{order}:{from1},P"
                    regular_moves.append(move_str)
            else:
                for from1 in possible_first:
                    pos1 = int(from1[1:])
                    count1 = state['my_pts'][pos1]
                    remaining_die2 = die2
                    possible_second = []
                    for from_pos in range(24):
                        if state['my_pts'][from_pos] == 0:
                            continue
                        if pos1 == from_pos and count1 < 2:
                            continue  # Can't move same checker twice if only one
                        dest = from_pos - remaining_die2
                        if dest < 0:
                            if all_in_home:
                                possible_second.append(f"A{from_pos}")
                            continue
                        if state['opp_pts'][dest] < 2:
                            possible_second.append(f"A{from_pos}")
                    for from2 in possible_second:
                        move_str = f"{order}:{from1},{from2}"
                        regular_moves.append(move_str)
                    if not possible_second:
                        move_str = f"{order}:{from1},P"
                        regular_moves.append(move_str)
        return regular_moves

    if state['my_bar'] > 0:
        bar_moves = generate_bar_moves(state)
        legal_bar_moves = [move for move in bar_moves if not move.endswith('P,P') or len(state['dice']) == 0]
        if not legal_bar_moves:
            return 'H:P,P' if len(state['dice']) else 'L:P,P'
        best_move = max(legal_bar_moves, key=lambda m: evaluate_move(m, state))
        return best_move
    else:
        regular_moves = generate_regular_moves(state)
        legal_regular_moves = [move for move in regular_moves if not move.endswith('P,P') or len(state['dice']) == 0]
        if not legal_regular_moves:
            return 'H:P,P' if len(state['dice']) else 'L:P,P'
        best_move = max(legal_regular_moves, key=lambda m: evaluate_move(m, state))
        return best_move
