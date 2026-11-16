
def policy(you: list[int], opponent: list[int]) -> str:
    possible_moves = []
    for row in range(5):
        for col in range(6):
            if you[row][col] == 1:
                if row - 1 >= 0 and opponent[row - 1][col] == 1:
                    possible_moves.append((row, col, 'U'))
                if row + 1 < 5 and opponent[row + 1][col] == 1:
                    possible_moves.append((row, col, 'D'))
                if col - 1 >= 0 and opponent[row][col - 1] == 1:
                    possible_moves.append((row, col, 'L'))
                if col + 1 < 6 and opponent[row][col + 1] == 1:
                    possible_moves.append((row, col, 'R'))

    if not possible_moves:
        return ''

    best_move = None
    min_score = float('inf')
    best_value = -1

    for move in possible_moves:
        r, c, d = move
        if d == 'U':
            nr, nc = r - 1, c
        elif d == 'D':
            nr, nc = r + 1, c
        elif d == 'L':
            nr, nc = r, c - 1
        else:
            nr, nc = r, c + 1

        new_you = [row[:] for row in you]
        new_opponent = [row[:] for row in opponent]
        new_you[r][c] = 0
        new_you[nr][nc] = 1
        new_opponent[nr][nc] = 0

        opponent_moves_count = 0
        for row_opp in range(5):
            for col_opp in range(6):
                if new_opponent[row_opp][col_opp] == 1:
                    if row_opp - 1 >= 0 and new_you[row_opp - 1][col_opp] == 1:
                        opponent_moves_count += 1
                    if row_opp + 1 < 5 and new_you[row_opp + 1][col_opp] == 1:
                        opponent_moves_count += 1
                    if col_opp - 1 >= 0 and new_you[row_opp][col_opp - 1] == 1:
                        opponent_moves_count += 1
                    if col_opp + 1 < 6 and new_you[row_opp][col_opp + 1] == 1:
                        opponent_moves_count += 1

        value = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr_adj = nr + dr
            nc_adj = nc + dc
            if 0 <= nr_adj < 5 and 0 <= nc_adj < 6:
                if you[nr_adj][nc_adj] == 1:
                    value += 1

        if opponent_moves_count < min_score:
            min_score = opponent_moves_count
            best_move = move
            best_value = value
        elif opponent_moves_count == min_score:
            if value > best_value:
                best_move = move
                best_value = value

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
