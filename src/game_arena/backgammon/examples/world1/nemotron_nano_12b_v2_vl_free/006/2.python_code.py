
import numpy as np

def policy(state):
    dice = state['dice']
    my_bar = state['my_bar']
    my_pts = state['my_pts']
    
    # Handle checkers on bar first
    if my_bar > 0:
        moves = []
        for i, d in enumerate(dice):
            if i == 0:
                continue  # Skip first die for re-entry possibility
            # Try re-entry using current die
            re_point = 24 - d - 1  # Correct conversion from dice to board position
            if re_point < 0 or re_point >= 24:
                continue
            if my_pts[re_point] < 6:
                moves.append(('B', re_point, 'B', float('inf')))
        # Handle double dice properly
        for move in moves:
            _, p1, _, _ = move
            moves_with_dice = []
            for j in range(2):
                if j == 0 and dice[j] == my_pts[p1] + my_bar:
                    continue
                if can_play(state, [dice[j]], 0, [p1], run_play=False)[0]:
                    moves_with_dice.append(move)
            if not moves_with_dice:
                break
        if moves_with_dice:
            # Choose move with best heuristic score
            return max(moves_with_dice, key=lambda x: x[3])[3]
            # Convert to appropriate move string
            return format_move(dice, [move[1], move[3]], move[0], second_moves=move[2])
    
    # No checkers on bar, find all valid moves
    all_playables = []
    for permutation in permute_dice(dice):
        possible_moves = possible_moves(state, permutation)
        if not possible_moves:
            continue
        for move in possible_moves:
            score = evaluate_move(state, *move)
            all_playables.append((move, score))
    
    # Filter out N/A scores (invalid moves)
    valid_moves = [m for m in all_playables if m[1] is not None]
    if not valid_moves:
        return "H:P,P"  # Pass if no valid moves
    
    # Select best move based on heuristic score or random if tied
    best_score = max(m[1] for m in valid_moves)
    best_moves = [m for m in valid_moves if m[1] == best_score]
    chosen_move = random.choice(best_moves)[0]
    return format_move(dice, chosen_move[0], chosen_move[-1], chosen_move[1:-2])
    
# Helper functions (not shown here for brevity)
# Implement steps like checking move legality, scoring moves, etc.
# Ensure format_move correctly applies H/L and handles permutations
