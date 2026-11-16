
import random

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    dice = state['dice']

    # If no dice rolled, must pass
    if not dice:
        return "H:P,P"

    # If only one die, must use it (higher die if applicable)
    if len(dice) == 1:
        die = dice[0]
        moves = generate_moves(state, [die], single_die=True)
        if moves:
            return f"H:{moves[0][0]},P"
        return "H:P,P"

    # Generate all possible moves
    moves = generate_moves(state, dice)

    # If no legal moves, pass
    if not moves:
        return "H:P,P"

    # Evaluate and select the best move
    best_move = select_best_move(state, moves, dice)
    return best_move

def generate_moves(state, dice, single_die=False):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice_sorted = sorted(dice, reverse=True)
    moves = []

    # Handle bar checkers first
    if my_bar > 0:
        return generate_bar_moves(state, dice_sorted)

    # Generate bearing off moves if possible
    if can_bear_off(state):
        bearing_moves = generate_bearing_moves(state, dice_sorted)
        if bearing_moves:
            return bearing_moves

    # Generate regular moves
    for i in range(24):
        if my_pts[i] > 0:
            for die_idx, die in enumerate(dice_sorted):
                dest = i - die
                if dest < 0:
                    continue  # Can't move beyond point 0
                if opp_pts[dest] >= 2:
                    continue  # Can't land on opponent's point with 2+ checkers

                # For single die case, just return the first valid move
                if single_die:
                    return [(f"A{i}", f"A{dest}")]

                # For two dice, find complementary moves
                remaining_dice = [d for d in dice_sorted if d != die]
                if not remaining_dice:
                    continue

                remaining_die = remaining_dice[0]
                for j in range(24):
                    if j == i and my_pts[i] < 2:
                        continue  # Can't move same checker twice unless it's a double
                    if my_pts[j] > 0:
                        dest2 = j - remaining_die
                        if dest2 < 0:
                            continue
                        if opp_pts[dest2] >= 2:
                            continue
                        if die_idx == 0:
                            moves.append((f"A{i}", f"A{j}"))
                        else:
                            moves.append((f"A{j}", f"A{i}"))

    # If no moves found, try to move one checker with higher die
    if not moves and len(dice_sorted) == 2:
        for i in range(24):
            if my_pts[i] > 0:
                dest = i - dice_sorted[0]
                if dest >= 0 and opp_pts[dest] < 2:
                    moves.append((f"A{i}", "P"))

    return moves

def generate_bar_moves(state, dice):
    opp_pts = state['opp_pts']
    moves = []
    dice_sorted = sorted(dice, reverse=True)

    # Try to enter with higher die first
    for die in dice_sorted:
        dest = 23 - die  # Bar is at position 24, entering at 23-die
        if dest < 0:
            continue
        if opp_pts[dest] < 2:
            if len(dice_sorted) == 2:
                remaining_die = dice_sorted[1] if die == dice_sorted[0] else dice_sorted[0]
                # Try to find a second move after entering
                for i in range(24):
                    if state['my_pts'][i] > 0:
                        dest2 = i - remaining_die
                        if dest2 >= 0 and state['opp_pts'][dest2] < 2:
                            moves.append((f"B", f"A{i}"))
                            return moves
                # If no second move, just enter with higher die
                moves.append((f"B", "P"))
            else:
                moves.append((f"B", "P"))
            return moves

    return moves

def generate_bearing_moves(state, dice):
    my_pts = state['my_pts']
    moves = []
    dice_sorted = sorted(dice, reverse=True)

    # Find the highest point with checkers
    highest_pt = -1
    for i in range(5, -1, -1):
        if my_pts[i] > 0:
            highest_pt = i
            break

    if highest_pt == -1:
        return moves

    # Try to bear off with both dice
    for die1 in dice_sorted:
        for die2 in dice_sorted:
            if die1 == die2 and my_pts[highest_pt] < 2:
                continue  # Can't use same die twice unless there are at least 2 checkers

            # Check if we can bear off with both dice
            if highest_pt + 1 <= die1 and highest_pt + 1 <= die2:
                moves.append(("P", "P"))
                return moves

            # Check if we can bear off with one die
            if highest_pt + 1 <= die1:
                # Try to find a second move
                for i in range(24):
                    if my_pts[i] > 0 and i != highest_pt:
                        dest = i - die2
                        if dest >= 0 and state['opp_pts'][dest] < 2:
                            moves.append((f"A{highest_pt}", f"A{i}"))
                            return moves
                moves.append((f"A{highest_pt}", "P"))
                return moves

            if highest_pt + 1 <= die2:
                # Try to find a second move
                for i in range(24):
                    if my_pts[i] > 0 and i != highest_pt:
                        dest = i - die1
                        if dest >= 0 and state['opp_pts'][dest] < 2:
                            moves.append((f"A{i}", f"A{highest_pt}"))
                            return moves
                moves.append((f"A{highest_pt}", "P"))
                return moves

    return moves

def can_bear_off(state):
    my_pts = state['my_pts']
    # All checkers must be in home board (points 0-5)
    for i in range(6, 24):
        if my_pts[i] > 0:
            return False
    return True

def select_best_move(state, moves, dice):
    if not moves:
        return "H:P,P"

    # Simple heuristic: prefer moves that advance checkers the most
    best_score = -float('inf')
    best_move_str = None

    for move in moves:
        from1, from2 = move
        score = 0

        # Score for moving from higher points
        if from1 != "P":
            if from1 == "B":
                score += 10  # Getting off bar is good
            else:
                pt = int(from1[1:])
                score += (23 - pt)  # Higher points get higher score

        if from2 != "P":
            if from2 == "B":
                score += 10
            else:
                pt = int(from2[1:])
                score += (23 - pt)

        # Prefer using both dice
        if from2 != "P":
            score += 5

        if score > best_score:
            best_score = score
            # Determine order based on which die is used first
            if from1 == "P" and from2 == "P":
                order = "H"
            elif from1 == "P":
                order = "L" if dice[1] > dice[0] else "H"
            elif from2 == "P":
                order = "H"
            else:
                # Determine which die is used for which move
                # This is simplified - in a real implementation you'd track which die is used
                order = "H" if random.random() > 0.5 else "L"

            best_move_str = f"{order}:{from1},{from2}"

    return best_move_str if best_move_str else "H:P,P"
