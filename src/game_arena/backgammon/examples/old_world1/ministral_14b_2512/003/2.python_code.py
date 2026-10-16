
import numpy as np
from collections import defaultdict

def policy(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']

    # Helper functions
    def is_legal_move(from_pt, die):
        if from_pt == 'B':
            if my_bar == 0:
                return False
            return True

        if from_pt == 'P':
            return True

        pt_idx = int(from_pt[1:])
        if my_pts[pt_idx] == 0:
            return False

        # Calculate destination
        direction = 1 if pt_idx < 12 else -1
        dest = pt_idx + direction * die
        if dest < 0 or dest > 23:
            return False

        # Check if destination is blocked
        if opp_pts[dest] >= 2:
            return False

        # Check if we can bear off
        if my_off + my_bar + my_pts[pt_idx] == 15 and pt_idx >= 1 and pt_idx <= 6:
            return True

        return True

    def get_legal_moves():
        moves = []
        if my_bar > 0:
            # Must move from bar first
            for die in dice:
                dest = 24 - die  # Bar entry points are 24 - die
                if opp_pts[dest] < 2:
                    moves.append(('B', die))
        else:
            # Check all points
            for pt in range(24):
                if my_pts[pt] > 0:
                    for die in dice:
                        if is_legal_move(f'A{pt}', die):
                            moves.append((f'A{pt}', die))

        # Also consider bearing off if all checkers are in home board
        if my_off + my_bar == 0 and all(my_pts[pt] == 0 for pt in range(7, 17)):
            for pt in range(1, 7):  # Home board points
                if my_pts[pt] > 0:
                    for die in dice:
                        if pt - die >= 0:
                            moves.append((f'A{pt}', die))

        return moves

    def evaluate_move(move):
        from_pt, die = move
        pt_idx = int(from_pt[1:]) if from_pt != 'B' else None

        # Score based on different factors
        score = 0

        # 1. Bar moves are good for creating threats
        if from_pt == 'B':
            score += 10
            dest = 24 - die
            if opp_pts[dest] == 1:  # Hit opponent's blot
                score += 15
            elif opp_pts[dest] == 0:  # Safe entry
                score += 5

        # 2. Protecting blots
        elif my_pts[pt_idx] == 1 and opp_pts[pt_idx] == 1:
            score += 20  # Critical blot protection

        # 3. Building anchors (multiple checkers on same point)
        elif my_pts[pt_idx] >= 2:
            score += 5

        # 4. Moving into home board
        if pt_idx is not None:
            if 1 <= pt_idx <= 6:  # Already in home board
                score += 3
            elif 7 <= pt_idx <= 12:  # Moving toward home board
                dest = pt_idx + (1 if pt_idx < 12 else -1) * die
                if 1 <= dest <= 6:
                    score += 10
            elif 13 <= pt_idx <= 18:  # Middle of board
                dest = pt_idx + (1 if pt_idx < 12 else -1) * die
                if 7 <= dest <= 12:
                    score += 5
            elif 19 <= pt_idx <= 23:  # Opponent's home board
                dest = pt_idx + (1 if pt_idx < 12 else -1) * die
                if 13 <= dest <= 18:
                    score += 2

        # 5. Bearing off
        if pt_idx is not None and my_off + my_bar + my_pts[pt_idx] == 15 and pt_idx >= 1 and pt_idx <= 6:
            score += 20 + (6 - (pt_idx - die)) * 2  # Prefer bearing off higher checkers

        # 6. Avoiding opponent's blots
        dest = pt_idx + (1 if pt_idx < 12 else -1) * die
        if opp_pts[dest] == 1:
            score -= 10

        # 7. Dice value preference (higher dice are generally better)
        score += die * 0.5

        return score

    def find_best_move():
        legal_moves = get_legal_moves()
        if not legal_moves:
            return "H:P,P"

        # Sort dice in descending order
        sorted_dice = sorted(dice, reverse=True)

        # Try to use both dice if possible
        if len(dice) == 2:
            # Find all possible pairs of moves
            best_score = -float('inf')
            best_move = None

            # Generate all possible move combinations
            for i in range(len(legal_moves)):
                for j in range(len(legal_moves)):
                    if i == j:
                        continue
                    from1, die1 = legal_moves[i]
                    from2, die2 = legal_moves[j]

                    # Check if we can use both dice
                    if (die1 == sorted_dice[0] and die2 == sorted_dice[1]) or \
                       (die1 == sorted_dice[1] and die2 == sorted_dice[0]):
                        score1 = evaluate_move((from1, die1))
                        score2 = evaluate_move((from2, die2))
                        total_score = score1 + score2

                        if total_score > best_score:
                            best_score = total_score
                            best_move = (from1, from2, 'H' if die1 > die2 else 'L')

            if best_move:
                order, from1, from2 = best_move
                return f"{order}:{from1},{from2}"

        # If we can't use both dice, use the higher die
        best_score = -float('inf')
        best_move = None

        for move in legal_moves:
            from_pt, die = move
            if die == sorted_dice[0]:
                score = evaluate_move(move)
                if score > best_score:
                    best_score = score
                    best_move = (from_pt, die)

        if best_move:
            from_pt, die = best_move
            # Check if we can use the other die as well
            remaining_dice = [d for d in dice if d != die]
            if remaining_dice:
                for move in legal_moves:
                    if move[1] == remaining_dice[0]:
                        score = evaluate_move(move)
                        if score > 0:  # Even a small positive score is worth it
                            return f"H:{from_pt},{move[0]}"

            return f"H:{from_pt},P"

        # Fallback: just use the highest scoring single move
        best_move = max(legal_moves, key=lambda x: evaluate_move(x))
        return f"H:{best_move[0]},P"

    return find_best_move()
