
import random

def policy(you: list[int], opponent: list[int]) -> int:
    # List of legal moves (indices of non-empty houses)
    legal_moves = [i for i in range(6) if you[i] > 0]

    # Check for immediate captures
    capture_moves = []
    for move in legal_moves:
        # Simulate the move
        seeds = you[move]
        you_copy = you.copy()
        opponent_copy = opponent.copy()
        you_copy[move] = 0

        # Distribute seeds
        current_pos = move + 1
        while seeds > 0:
            if current_pos == 6:
                you_copy[6] += 1
                seeds -= 1
                if seeds == 0:
                    # Check if the last seed lands in the store (extra move)
                    pass
                current_pos = 7  # Move to opponent's side
            elif current_pos < 13:
                if current_pos < 7:
                    you_copy[current_pos] += 1
                else:
                    opponent_copy[current_pos - 7] += 1
                seeds -= 1
                if seeds == 0:
                    # Check for capture
                    if current_pos < 6 and you_copy[current_pos] == 1 and opponent_copy[5 - current_pos] > 0:
                        capture_moves.append(move)
                current_pos += 1
            else:
                current_pos = 0

    if capture_moves:
        return random.choice(capture_moves)

    # Check for moves that land in the store
    store_moves = []
    for move in legal_moves:
        seeds = you[move]
        current_pos = move + 1
        while seeds > 0:
            if current_pos == 6:
                if seeds == 1:
                    store_moves.append(move)
                    break
                you_copy = you.copy()
                you_copy[6] += 1
                seeds -= 1
                current_pos = 7
            elif current_pos < 13:
                seeds -= 1
                current_pos += 1
            else:
                current_pos = 0

    if store_moves:
        return random.choice(store_moves)

    # Use a simple heuristic: maximize the difference in stores
    best_move = None
    best_score = -float('inf')
    for move in legal_moves:
        # Simulate the move
        seeds = you[move]
        you_copy = you.copy()
        opponent_copy = opponent.copy()
        you_copy[move] = 0

        # Distribute seeds
        current_pos = move + 1
        while seeds > 0:
            if current_pos == 6:
                you_copy[6] += 1
                seeds -= 1
                if seeds == 0:
                    # Check for capture
                    pass
                current_pos = 7
            elif current_pos < 13:
                if current_pos < 7:
                    you_copy[current_pos] += 1
                else:
                    opponent_copy[current_pos - 7] += 1
                seeds -= 1
                if seeds == 0:
                    # Check for capture
                    if current_pos < 6 and you_copy[current_pos] == 1 and opponent_copy[5 - current_pos] > 0:
                        you_copy[6] += you_copy[current_pos] + opponent_copy[5 - current_pos]
                        you_copy[current_pos] = 0
                        opponent_copy[5 - current_pos] = 0
                current_pos += 1
            else:
                current_pos = 0

        # Calculate the score
        score = you_copy[6] - opponent_copy[6]
        if score > best_score:
            best_score = score
            best_move = move

    if best_move is not None:
        return best_move

    # If no move is found based on the heuristic, return a random legal move
    return random.choice(legal_moves)
