
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Directions: forward, diagonal forward (left and right)
    if color == 'w':
        directions = [(1, 0), (1, -1), (1, 1)]  # White moves up (row increases)
    else:
        directions = [(-1, 0), (-1, -1), (-1, 1)]  # Black moves down (row decreases)

    # Generate all legal moves
    legal_moves = []
    for (r, c) in me:
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if (nr, nc) not in me and (nr, nc) not in opp:
                    legal_moves.append(((r, c), (nr, nc)))
                elif (nr, nc) in opp:
                    legal_moves.append(((r, c), (nr, nc)))

    if not legal_moves:
        return ((0, 0), (0, 0))  # Should not happen per problem statement

    # Evaluate moves using a heuristic
    def evaluate_move(move, me, opp, color):
        from_r, from_c = move[0]
        to_r, to_c = move[1]
        new_me = me.copy()
        new_opp = opp.copy()
        new_me.remove((from_r, from_c))
        new_me.append((to_r, to_c))
        if (to_r, to_c) in opp:
            new_opp.remove((to_r, to_c))

        # Heuristic: prioritize moves that bring pieces closer to opponent's home row
        if color == 'w':
            opp_home_row = 7
        else:
            opp_home_row = 0

        # Score for my pieces: closer to opponent's home row is better
        my_score = sum(abs(p[0] - opp_home_row) for p in new_me)
        # Score for opponent pieces: farther from my home row is better
        if color == 'w':
            my_home_row = 0
        else:
            my_home_row = 7
        opp_score = sum(abs(p[0] - my_home_row) for p in new_opp)

        # Bonus for captures
        if (to_r, to_c) in opp:
            my_score += 10  # Capture is good

        # Bonus for pieces that can promote next turn
        for (r, c) in new_me:
            if color == 'w' and r == 6:
                my_score += 5  # One step from promotion
            elif color == 'b' and r == 1:
                my_score += 5

        # Penalty for leaving pieces vulnerable
        for (r, c) in new_me:
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if (nr, nc) in opp:
                        my_score -= 3  # Vulnerable to capture

        return my_score - opp_score

    # Evaluate all legal moves and pick the best one
    best_move = None
    best_score = -float('inf')
    for move in legal_moves:
        score = evaluate_move(move, me, opp, color)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move
