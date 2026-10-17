
import random

def policy(you: list[int], opponent: list[int]) -> int:
    # Helper function to compute the heuristic score for a move
    def heuristic_score(move: int) -> float:
        # Make a copy of the board to simulate the move
        new_you = you.copy()
        new_opponent = opponent.copy()
        seeds = new_you[move]
        new_you[move] = 0

        # Simulate sowing
        current = move
        while seeds > 0:
            if current < 6:
                new_you[current] += 1
                seeds -= 1
                if seeds == 0:
                    break
            current += 1
            if current == 6:
                new_you[6] += 1
                seeds -= 1
                if seeds == 0:
                    break
            if current == 7:
                current = 0
            if current < 6:
                new_opponent[current] += 1
                seeds -= 1
                if seeds == 0:
                    break
            current += 1

        # Check for capture
        last_house = current - 1 if current > 0 else 5
        if last_house < 6 and new_you[last_house] == 1:
            opposite_house = 5 - last_house
            if new_opponent[opposite_house] > 0:
                # Capture: move all seeds from opposite house to store
                captured = new_opponent[opposite_house] + 1
                new_you[6] += captured
                new_opponent[opposite_house] = 0
                # Check if opponent has no moves left
                if sum(new_opponent[:6]) == 0:
                    # Opponent loses, so this is a winning move
                    return float('inf')

        # Heuristic components
        score = 0.0

        # 1. Immediate capture bonus (already handled above)
        if last_house < 6 and new_you[last_house] == 1 and new_opponent[5 - last_house] > 0:
            score += 100.0  # High priority for captures

        # 2. Store advantage
        store_diff = new_you[6] - opponent[6]
        score += store_diff * 0.1

        # 3. Balance the board (avoid overloading one side)
        your_sum = sum(new_you[:6])
        opponent_sum = sum(new_opponent[:6])
        balance = abs(your_sum - opponent_sum)
        score -= balance * 0.05

        # 4. Opponent's vulnerability (target opponent's houses with few seeds)
        for i in range(6):
            if new_opponent[i] < 2:
                score += 0.5  # Prefer moves that leave opponent with weak houses

        # 5. Avoid moves that leave you with no moves next turn
        if sum(new_you[:6]) == 0:
            score -= 100.0  # Penalize moves that leave you with no moves

        # 6. Prefer moves that leave opponent with no moves next turn
        if sum(new_opponent[:6]) == 0:
            score += 100.0

        return score

    # Generate all legal moves
    legal_moves = [i for i in range(6) if you[i] > 0]

    # Evaluate all legal moves
    move_scores = [(move, heuristic_score(move)) for move in legal_moves]

    # If all moves are equally bad (e.g., in a losing position), default to random
    if all(score == move_scores[0][1] for _, score in move_scores):
        return random.choice(legal_moves)

    # Select the move with the highest score, with some randomness to avoid predictability
    max_score = max(score for _, score in move_scores)
    best_moves = [move for move, score in move_scores if score == max_score]

    # With 80% probability, pick the best move; otherwise, pick randomly among best moves
    if random.random() < 0.8:
        return random.choice(best_moves)
    else:
        return random.choice(legal_moves)
