
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Determine the direction of movement based on color
    direction = -1 if color == 'b' else 1
    home_row = 0 if color == 'b' else 7
    opponent_home_row = 7 if color == 'b' else 0

    # Convert me and opp to sets for faster lookups
    me_set = set(me)
    opp_set = set(opp)

    # Generate all possible legal moves
    legal_moves = []
    for (r, c) in me:
        # Check forward move
        new_r = r + direction
        if 0 <= new_r <= 7:
            if (new_r, c) not in me_set and (new_r, c) not in opp_set:
                legal_moves.append(((r, c), (new_r, c)))
            # Check diagonal left capture
            new_c = c - 1
            if 0 <= new_c <= 7 and (new_r, new_c) in opp_set:
                legal_moves.append(((r, c), (new_r, new_c)))
            # Check diagonal right capture
            new_c = c + 1
            if 0 <= new_c <= 7 and (new_r, new_c) in opp_set:
                legal_moves.append(((r, c), (new_r, new_c)))

    # If no legal moves, return a random move (should not happen as per problem statement)
    if not legal_moves:
        return random.choice(legal_moves)

    # Score each move
    scored_moves = []
    for move in legal_moves:
        (from_r, from_c), (to_r, to_c) = move
        score = 0

        # Priority 1: Winning move (reach opponent's home row)
        if to_r == opponent_home_row:
            score += 1000
        # Priority 2: Capture opponent piece
        elif (to_r, to_c) in opp_set:
            score += 500
            # Bonus for capturing pieces near my home row
            if abs(to_r - home_row) <= 2:
                score += 100
        # Priority 3: Advance toward opponent's home row
        else:
            # Bonus for moving closer to opponent's home row
            distance_to_home = abs(to_r - opponent_home_row)
            score += (7 - distance_to_home) * 10
            # Bonus for moving toward the center (columns 3 or 4)
            if to_c in [3, 4]:
                score += 5

        scored_moves.append((score, move))

    # Select the move with the highest score
    scored_moves.sort(reverse=True, key=lambda x: x[0])
    best_move = scored_moves[0][1]

    return best_move
