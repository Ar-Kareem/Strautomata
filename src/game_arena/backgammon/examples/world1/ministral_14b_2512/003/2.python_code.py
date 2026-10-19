
import numpy as np

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    # If no dice rolled (e.g., doubling), pass
    if not dice:
        return "H:P,P"

    # If bar checkers exist, move them first (engine enforces this)
    if my_bar > 0:
        # Try to move the higher die first (L:B,X means lower die from bar, higher die from X)
        # But since we must move bar checkers first, we use the lower die if possible
        # (because bar moves are always with the lower die if both dice are used)
        # So we try to move from bar with the lower die, then higher die if possible
        # But the engine enforces that if we have bar checkers, we must move them first
        # So we pick the best possible bar move with the lower die, then higher die if needed

        # Find all possible bar moves (must land on a point with <=1 opponent checker)
        possible_bar_moves = []
        for die in dice:
            for point in range(24):
                if opp_pts[point] <= 1:
                    possible_bar_moves.append(die)

        # If no possible bar moves, pass (but engine enforces bar moves first, so this shouldn't happen)
        if not possible_bar_moves:
            return "H:P,P"

        # Sort possible bar moves in descending order (prefer higher dice)
        possible_bar_moves_sorted = sorted(possible_bar_moves, reverse=True)

        # Try to move both dice from bar if possible (but bar only allows one die per move)
        # So we pick the highest possible die from bar, then the next highest if possible
        # But since we can only move one die from bar, we need to handle the second die separately

        # For the first move, use the highest possible die from bar
        first_die = possible_bar_moves_sorted[0] if possible_bar_moves_sorted else dice[0]
        first_move = f"L:B,{first_die}"  # Since bar moves are always with lower die if both are used

        # For the second move, if the other die can be played legally (not from bar)
        second_die = dice[1] if len(dice) == 2 else None
        if second_die is not None:
            # Find possible moves with the second die (not from bar)
            possible_second_moves = []
            for point in range(24):
                if my_pts[point] > 0 and (point + second_die) < 24 and opp_pts[point + second_die] <= 1:
                    possible_second_moves.append(point)

            # If no possible second moves, pass
            if not possible_second_moves:
                return first_move.replace(",", ":P")
            else:
                # Choose the best second move (prioritize attacking, then safe moves)
                best_second_move = choose_best_move(my_pts, opp_pts, second_die, possible_second_moves)
                return f"{first_move[:2]}:{first_die},{best_second_move}"
        else:
            return first_move.replace(",", ":P")

    else:
        # No bar checkers; proceed with normal moves
        if len(dice) == 2:
            # Try to find two moves that can be played together (double dice)
            possible_moves = []
            for point in range(24):
                if my_pts[point] > 0:
                    for die in dice:
                        dest = point + die
                        if dest < 24 and opp_pts[dest] <= 1:
                            possible_moves.append((point, die))
                            break  # Only consider one die per point to avoid duplicates

            # If we can double the dice, do so
            if len(possible_moves) >= 2:
                # Sort moves by (attack strength, die value)
                possible_moves_sorted = sorted(possible_moves, key=lambda x: (-get_attack_strength(my_pts, opp_pts, x[0] + x[1]), -x[1]))
                from1, from2 = possible_moves_sorted[0][0], possible_moves_sorted[1][0]
                return f"H:{from1},{from2}"  # Prefer higher die first
            else:
                # If only one die can be played, use the higher die
                possible_moves = []
                for point in range(24):
                    if my_pts[point] > 0:
                        for die in dice:
                            dest = point + die
                            if dest < 24 and opp_pts[dest] <= 1:
                                possible_moves.append((point, die))

                if len(possible_moves) == 1:
                    # Use higher die first
                    point, die = possible_moves[0]
                    return f"H:{point},P" if die == dice[0] else f"L:{point},P"
                elif len(possible_moves) == 0:
                    return "H:P,P"
                else:
                    # Choose the best single move (prioritize higher die)
                    best_move = max(possible_moves, key=lambda x: (-x[1], -get_attack_strength(my_pts, opp_pts, x[0] + x[1])))
                    from1 = best_move[0]
                    return f"H:{from1},P" if best_move[1] == dice[0] else f"L:{from1},P"
        else:
            # Only one die; must use it
            die = dice[0]
            possible_moves = []
            for point in range(24):
                if my_pts[point] > 0:
                    dest = point + die
                    if dest < 24 and opp_pts[dest] <= 1:
                        possible_moves.append(point)

            if not possible_moves:
                return "H:P,P"
            else:
                # Choose the best single move (prioritize attacking)
                best_move = max(possible_moves, key=lambda x: -get_attack_strength(my_pts, opp_pts, x + die))
                return f"H:{best_move},P"

def get_attack_strength(my_pts, opp_pts, dest):
    """Heuristic to evaluate how strong an attack is at a given destination."""
    if dest >= 0 and dest < 24:
        # If opponent has 1 or 2 checkers here, hitting is strong
        if opp_pts[dest] == 1 or opp_pts[dest] == 2:
            return 10  # Very strong attack
        # If opponent has no checkers here but is in my home board, moving toward home is safe
        elif opp_pts[dest] == 0 and dest <= 5:
            return 5
        # If opponent has no checkers here but is in my outer board, moving toward home is good
        elif opp_pts[dest] == 0 and dest <= 11:
            return 3
        # If opponent has no checkers here but is in their outer board, moving toward home is okay
        elif opp_pts[dest] == 0 and dest <= 17:
            return 1
        else:
            return 0  # No attack strength
    return 0

def choose_best_move(my_pts, opp_pts, die, possible_moves):
    """Choose the best move from a list of possible moves, prioritizing attacks."""
    # Evaluate each move and pick the one with highest attack strength
    best_move = max(possible_moves, key=lambda x: get_attack_strength(my_pts, opp_pts, x + die))
    return best_move
