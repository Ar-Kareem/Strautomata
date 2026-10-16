
import copy

def policy(you: list[int], opponent: list[int]) -> int:
    # Minimax to depth 4
    best_move = None
    best_score = float('-inf')
    for i in range(6):
        if you[i] > 0:
            new_you, new_opp, extra_turn = simulate_move(copy.deepcopy(you), copy.deepcopy(opponent), i, True)
            if extra_turn:
                score = minimax(new_you, new_opp, 3, True)  # Depth 4 total, since extra turn counts as your move
            else:
                score = minimax(new_you, new_opp, 3, False)
            if score > best_score:
                best_score = score
                best_move = i
    return best_move

def minimax(you: list[int], opp: list[int], depth: int, maximizing: bool) -> float:
    if depth == 0 or is_game_over(you, opp):
        return evaluate(you, opp)
    if maximizing:
        max_score = float('-inf')
        for i in range(6):
            if you[i] > 0:
                new_you, new_opp, extra_turn = simulate_move(copy.deepcopy(you), copy.deepcopy(opp), i, True)
                if extra_turn:
                    score = minimax(new_you, new_opp, depth - 1, True)
                else:
                    score = minimax(new_you, new_opp, depth - 1, False)
                max_score = max(max_score, score)
        return max_score
    else:
        min_score = float('inf')
        for i in range(6):
            if opp[i] > 0:
                new_opp, new_you, extra_turn = simulate_move(copy.deepcopy(opp), copy.deepcopy(you), i, False)  # Swap for opp's perspective
                if extra_turn:
                    score = minimax(new_you, new_opp, depth - 1, False)  # Opp gets extra turn
                else:
                    score = minimax(new_you, new_opp, depth - 1, True)
                min_score = min(min_score, score)
        return min_score

def evaluate(you: list[int], opp: list[int]) -> float:
    if is_game_over(you, opp):
        # Move remaining seeds to stores
        you_store = you[6] + sum(you[:6])
        opp_store = opp[6] + sum(opp[:6])
        return you_store - opp_store
    else:
        return you[6] - opp[6] + 0.01 * (sum(you[:6]) - sum(opp[:6]))  # Heuristic prefers board control

def is_game_over(you: list[int], opp: list[int]) -> bool:
    return sum(you[:6]) == 0 or sum(opp[:6]) == 0

def simulate_move(you: list[int], opp: list[int], i: int, is_your_turn: bool) -> tuple[list[int], list[int], bool]:
    if not is_your_turn:
        # Swap for opponent's move
        you, opp = opp, you
    seeds = you[i]
    you[i] = 0
    position = i + 1
    extra_turn = False
    while seeds > 0:
        if position < 6:
            you[position] += 1
        elif position == 6:
            you[position] += 1
            if seeds == 1:  # Last seed in your store triggers extra turn
                extra_turn = True
        else:  # Wrap to opponent's side, skipping their store
            pos = (position - 7) % 6
            opp[pos] += 1
        seeds -= 1
        position = (position + 1) % 14  # 6 your pits + 1 store + 6 opp pits = 13, +1 for next
    # Handle capture: last seed in your empty pit, opposite has seeds
    if not extra_turn and (i + 1) <= 6 and position % 14 == i:  # Canonical: seeds drop and last in your pit
        # Wait, simplification: if last position was in your side and you[i] was 0 before?
        # But to simplify, check if landed in you[ something ] was 0 and opp has
        last_pos = (i + 1 + seeds) % 14  # Wait, better way
        actual_farmer = position - 1  # Last drop position
        # If in your pits and was empty and opp opposite has seeds
        if 0 <= actual_farmer <= 5 and you[actual_farmer] == 1 and opp[5 - actual_farmer] > 0:
            you[6] += you[actual_farmer] + opp[5 - actual_farmer]
            you[actual_farmer] = 0
            opp[5 - actual_farmer] = 0
    return you, opp, extra_turn
