
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Determine the direction of movement based on color
    direction = -1 if color == 'b' else 1
    home_row = 0 if color == 'w' else 7

    # Convert lists to sets for faster lookups
    me_set = set(me)
    opp_set = set(opp)

    # Check for winning moves (reaching the opponent's home row)
    for (r, c) in me:
        # Check straight move to home row
        if r + direction == home_row and (r + direction, c) not in me_set and (r + direction, c) not in opp_set:
            return ((r, c), (r + direction, c))
        # Check diagonal moves to home row
        for dc in [-1, 1]:
            if 0 <= c + dc < 8:
                if r + direction == home_row and (r + direction, c + dc) not in me_set and (r + direction, c + dc) not in opp_set:
                    return ((r, c), (r + direction, c + dc))

    # Check for captures
    captures = []
    for (r, c) in me:
        for dc in [-1, 1]:
            if 0 <= c + dc < 8:
                if (r + direction, c + dc) in opp_set:
                    captures.append(((r, c), (r + direction, c + dc)))
    if captures:
        # Prioritize captures that are closer to the opponent's home row
        captures.sort(key=lambda move: abs(move[1][0] - home_row))
        return captures[0]

    # Check for advancing moves (non-capture)
    advances = []
    for (r, c) in me:
        # Straight move
        if (r + direction, c) not in me_set and (r + direction, c) not in opp_set:
            advances.append(((r, c), (r + direction, c)))
        # Diagonal moves
        for dc in [-1, 1]:
            if 0 <= c + dc < 8:
                if (r + direction, c + dc) not in me_set and (r + direction, c + dc) not in opp_set:
                    advances.append(((r, c), (r + direction, c + dc)))
    if advances:
        # Prioritize moves that are closer to the opponent's home row
        advances.sort(key=lambda move: abs(move[1][0] - home_row))
        return advances[0]

    # If no moves found (should not happen as per rules), return a random legal move
    # This is a fallback to ensure a legal move is always returned
    all_moves = []
    for (r, c) in me:
        # Straight move
        if (r + direction, c) not in me_set and (r + direction, c) not in opp_set:
            all_moves.append(((r, c), (r + direction, c)))
        # Diagonal moves
        for dc in [-1, 1]:
            if 0 <= c + dc < 8:
                if (r + direction, c + dc) in opp_set:
                    all_moves.append(((r, c), (r + direction, c + dc)))
                elif (r + direction, c + dc) not in me_set and (r + direction, c + dc) not in opp_set:
                    all_moves.append(((r, c), (r + direction, c + dc)))
    return random.choice(all_moves)
