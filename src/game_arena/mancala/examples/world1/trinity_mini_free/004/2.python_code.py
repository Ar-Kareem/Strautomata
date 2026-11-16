
def policy(you: list[int], opponent: list[int]) -> int:
    # Find all non-empty houses
    moves = [i for i in range(6) if you[i] > 0]
    if not moves:
        return None  # Should not happen per problem statement
    
    # Choose the move with the most seeds
    best_move = moves[0]
    best_count = you[best_move]
    for i in moves[1:]:
        if you[i] > best_count:
            best_count = you[i]
            best_move = i
    return best_move
