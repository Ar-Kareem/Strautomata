
import random

def policy(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    dice = state['dice']

    # Helper functions
    def is_home_board(point):
        return point >= 18  # Assuming home board is points 18-23 for the player

    def can_bear_off():
        for i in range(18):
            if my_pts[i] > 0:
                return False
        return True

    def get_legal_moves():
        moves = []
        if my_bar > 0:
            # Must move from bar first
            for die in dice:
                target = die - 1  # Bar is point 0 for opponent, but we need to enter at 24 - die
                if opp_pts[target] < 2:
                    moves.append(('B', die))
            return moves

        # Check for bearing off
        if can_bear_off():
            for i in range(24):
                if my_pts[i] > 0:
                    for die in dice:
                        if i + die >= 24:
                            moves.append((f'A{i}', die))
            return moves

        # Regular moves
        for i in range(24):
            if my_pts[i] > 0:
                for die in dice:
                    target = i + die
                    if target < 24 and opp_pts[target] < 2:
                        moves.append((f'A{i}', die))
                    elif target >= 24 and can_bear_off():
                        moves.append((f'A{i}', die))
        return moves

    def evaluate_move(move):
        # Simple evaluation: prefer hitting, then bearing off, then moving forward
        from_pt, die = move
        if from_pt == 'B':
            return 3  # High priority to get off bar
        if from_pt.startswith('A'):
            pt = int(from_pt[1:])
            target = pt + die
            if target < 24 and opp_pts[target] == 1:
                return 4  # Hit opponent's blot
            if target >= 24:
                return 2  # Bear off
            if is_home_board(target):
                return 1  # Move to home board
        return 0

    legal_moves = get_legal_moves()

    if not legal_moves:
        return "H:P,P"

    # Sort moves by evaluation
    legal_moves.sort(key=evaluate_move, reverse=True)

    # Try to use both dice if possible
    if len(dice) == 2:
        # Find two different moves
        for i in range(len(legal_moves)):
            for j in range(i+1, len(legal_moves)):
                if legal_moves[i][1] != legal_moves[j][1]:
                    # Check if we can use both dice
                    if (legal_moves[i][1] == max(dice) and legal_moves[j][1] == min(dice)):
                        return f"H:{legal_moves[i][0]},{legal_moves[j][0]}"
                    elif (legal_moves[i][1] == min(dice) and legal_moves[j][1] == max(dice)):
                        return f"L:{legal_moves[i][0]},{legal_moves[j][0]}"

    # If can't use both dice, use the best single move
    best_move = legal_moves[0]
    if len(dice) == 2:
        # Need to specify which die is used
        if best_move[1] == max(dice):
            return f"H:{best_move[0]},P"
        else:
            return f"L:{best_move[0]},P"
    else:
        return f"H:{best_move[0]},P"
