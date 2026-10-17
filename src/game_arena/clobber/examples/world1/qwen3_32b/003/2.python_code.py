
def policy(you: list[list[int]], opponent: list[list[int]]) -> str:
    def generate_moves(current_you, current_opponent):
        moves = []
        for row in range(5):
            for col in range(6):
                if current_you[row][col] == 1:
                    for dr, dc, direction in [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]:
                        new_row, new_col = row + dr, col + dc
                        if 0 <= new_row < 5 and 0 <= new_col < 6:
                            if current_opponent[new_row][new_col] == 1:
                                moves.append(f"{row},{col},{direction}")
        return moves

    def apply_move(current_you, current_opponent, move_str):
        row, col, direction = move_str.split(',')
        row, col = int(row), int(col)
        dr, dc = 0, 0
        if direction == 'U':
            dr -= 1
        elif direction == 'D':
            dr += 1
        elif direction == 'L':
            dc -= 1
        elif direction == 'R':
            dc += 1
        new_row, new_col = row + dr, col + dc

        new_you = [r[:] for r in current_you]
        new_opponent = [r[:] for r in current_opponent]

        new_you[row][col] = 0
        new_you[new_row][new_col] = 1
        new_opponent[new_row][new_col] = 0

        return new_you, new_opponent

    def evaluate(current_you, current_opponent):
        current_mobility = len(generate_moves(current_you, current_opponent))
        if current_mobility == 0:
            return float('-inf')
        opponent_mobility = len(generate_moves(current_opponent, current_you))
        return current_mobility - opponent_mobility

    def negamax(current_you, current_opponent, depth, alpha, beta):
        if depth == 0:
            return evaluate(current_you, current_opponent)
        moves = generate_moves(current_you, current_opponent)
        if not moves:
            return evaluate(current_you, current_opponent)

        best_value = float('-inf')
        for move in moves:
            new_you, new_opponent = apply_move(current_you, current_opponent, move)
            eval = -negamax(new_opponent, new_you, depth - 1, -beta, -alpha)
            if eval > best_value:
                best_value = eval
            if best_value >= beta:
                break
            alpha = max(alpha, best_value)
        return best_value

    moves = generate_moves(you, opponent)
    if not moves:
        return ""  # According to problem statement, should always return a legal move
    best_move = moves[0]
    best_score = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    max_depth = 1

    for move in moves:
        new_you, new_opponent = apply_move(you, opponent, move)
        score = -negamax(new_opponent, new_you, max_depth, -beta, -alpha)
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, best_score)

    return best_move
