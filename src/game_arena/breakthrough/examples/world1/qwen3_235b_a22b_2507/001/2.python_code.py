
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Convert lists to sets for faster lookup
    me_set = set(me)
    opp_set = set(opp)
    
    # Define direction of movement based on color
    if color == 'w':  # White moves upward (row increases)
        forward = 1
        opponent_home_row = 7  # Reach row 7 to win
    else:  # Black moves downward (row decreases)
        forward = -1
        opponent_home_row = 0  # Reach row 0 to win

    # Build list of legal moves
    moves = []
    for r, c in me:
        # Move forward (straight)
        nr = r + forward
        if 0 <= nr < 8:
            # Straight forward: must be empty
            if (nr, c) not in me_set and (nr, c) not in opp_set:
                moves.append(((r, c), (nr, c)))
            
            # Diagonal left capture
            if c > 0:
                nc = c - 1
                if (nr, nc) in opp_set:
                    moves.append(((r, c), (nr, nc)))
                elif (nr, nc) not in me_set:
                    moves.append(((r, c), (nr, nc)))
            
            # Diagonal right capture
            if c < 7:
                nc = c + 1
                if (nr, nc) in opp_set:
                    moves.append(((r, c), (nr, nc)))
                elif (nr, nc) not in me_set:
                    moves.append(((r, c), (nr, nc)))

    # If no moves (should not happen in valid game), return a dummy (should not occur)
    if not moves:
        return ((0,0), (0,0))  # This case should never happen

    # Evaluate moves: prioritize winning, then capturing, then forward progress
    def evaluate_move(move):
        (fr, fc), (tr, tc) = move
        score = 0

        # Winning move: reach opponent's home row
        if tr == opponent_home_row:
            score += 1000

        # Capture bonus
        if (tr, tc) in opp_set:
            score += 10

        # Forward progress: value based on how far we are advancing (black: lower rows better, white: higher)
        progress = tr if color == 'w' else (7 - tr)
        score += progress

        # Prefer central columns slightly
        score += (3 - abs(tc - 3.5))  # Center bias around column 3.5

        return score

    # Sort moves by score (descending)
    moves.sort(key=evaluate_move, reverse=True)

    # Return the best move
    return moves[0]
