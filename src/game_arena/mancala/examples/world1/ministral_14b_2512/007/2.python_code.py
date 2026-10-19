
import random

def policy(you: list[int], opponent: list[int]) -> int:
    # Check if the game is in the endgame (few seeds left)
    endgame = sum(you[0:6]) <= 6 or sum(opponent[0:6]) <= 6

    # Get all legal moves (houses with seeds)
    legal_moves = [i for i in range(6) if you[i] > 0]

    # If no legal moves, return any (though problem states policy is never called in this case)
    if not legal_moves:
        return random.choice(range(6))

    # Evaluate all possible moves
    scores = []
    for move in legal_moves:
        # Simulate the move to compute the score
        score = evaluate_move(you, opponent, move, endgame)
        scores.append(score)

    # Choose the move with the highest score, with randomness to avoid predictability
    best_move = random.choices(legal_moves, weights=[max(0.1, s) for s in scores], k=1)[0]

    return best_move

def evaluate_move(you: list[int], opponent: list[int], move: int, endgame: bool) -> float:
    # Make a copy of the board to simulate the move
    you_copy = you.copy()
    opponent_copy = opponent.copy()

    # Remove all seeds from the chosen house
    seeds = you_copy[move]
    you_copy[move] = 0

    # Sow seeds one by one
    i = move
    while seeds > 0:
        i = (i + 1) % 14  # 6 houses + store + 6 houses = 13, but modulo 14 to handle store correctly
        if i == 6:  # Your store
            you_copy[i] += 1
        elif i == 13:  # Wrap around to your houses
            i = 0
            you_copy[i] += 1
        elif i < 6:  # Your houses (after move)
            you_copy[i] += 1
        else:  # Opponent's houses (i ranges 7..12)
            opponent_copy[i - 7] += 1

        seeds -= 1

    # Check if the last seed landed in your store (extra move)
    if i == 6:
        return float('inf')  # Extra move is very valuable

    # Check for captures (if last seed landed in empty house and opponent has seeds in opposite house)
    if seeds == 0 and you_copy[i] == 1 and opponent_copy[5 - (i % 6)] > 0:
        # Capture all seeds from opponent's opposite house and the current house
        captured = you_copy[i] + opponent_copy[5 - (i % 6)]
        you_copy[i] = 0
        opponent_copy[5 - (i % 6)] = 0
        you_copy[6] += captured
        return float('inf')  # Capture is very valuable

    # Compute the score for this move
    score = 0.0

    # Board balance: avoid making your houses too uneven
    your_house_variance = sum((you_copy[i] - you_copy[6] / 6) ** 2 for i in range(6))
    score += -your_house_variance  # Lower variance is better

    # Opponent's potential captures: avoid moves that leave them with an easy capture
    for opp_move in range(6):
        if opponent_copy[opp_move] > 0:
            # Simulate opponent's move (for simplicity, assume they capture if possible)
            seeds = opponent_copy[opp_move]
            opponent_copy[opp_move] = 0
            j = opp_move
            while seeds > 0:
                j = (j + 1) % 14
                if j == 6:  # Opponent's store
                    opponent_copy[j] += 1
                elif j == 13:  # Wrap around to opponent's houses
                    j = 7
                    opponent_copy[j - 7] += 1
                elif j < 6:  # Your houses (if opponent sows into them)
                    you_copy[j] += 1
                else:  # Opponent's houses
                    opponent_copy[j - 7] += 1
                seeds -= 1

            # Check if opponent can capture in their move
            if seeds == 0 and opponent_copy[j] == 1 and you_copy[5 - ((j % 6) if j < 6 else (j - 7) % 6)] > 0:
                # Opponent can capture, so penalize this move
                score -= 10.0
            opponent_copy[opp_move] = opponent_copy[opp_move] + seeds  # Revert

    # Store advantage: prioritize moves that increase your store relative to theirs
    store_diff = you_copy[6] - opponent_copy[6]
    score += store_diff * 0.1  # Small weight to avoid overfitting

    # Endgame: prioritize moves that maximize your store advantage
    if endgame:
        score += sum(you_copy[0:6]) * 0.5  # More seeds left = better chance to win

    return score
