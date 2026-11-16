
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Helper function to check if a player has won
    def has_won(b, player):
        for i in range(4):
            if all(b[i][j] == player for j in range(4)):
                return True
            if all(b[j][i] == player for j in range(4)):
                return True
        if all(b[i][i] == player for i in range(4)):
            return True
        if all(b[i][3-i] == player for i in range(4)):
            return True
        return False

    # Helper function to evaluate the board from a player's perspective
    def evaluate_board(b, player):
        total = 0
        for i in range(4):
            count_player = 0
            count_opponent = 0
            for j in range(4):
                if b[i][j] == player:
                    count_player += 1
                elif b[i][j] == -player:
                    count_opponent += 1
            if count_opponent == 0:
                if count_player == 3:
                    total += 1000
                elif count_player == 2:
                    total += 100
                elif count_player == 1:
                    total += 10
        for i in range(4):
            count_player = 0
            count_opponent = 0
            for j in range(4):
                if b[j][i] == player:
                    count_player += 1
                elif b[j][i] == -player:
                    count_opponent += 1
            if count_opponent == 0:
                if count_player == 3:
                    total += 1000
                elif count_player == 2:
                    total += 100
                elif count_player == 1:
                    total += 10
        count_player = 0
        count_opponent = 0
        for i in range(4):
            if b[i][i] == player:
                count_player += 1
            elif b[i][i] == -player:
                count_opponent += 1
        if count_opponent == 0:
            if count_player == 3:
                total += 1000
            elif count_player == 2:
                total += 100
            elif count_player == 1:
                total += 10
        count_player = 0
        count_opponent = 0
        for i in range(4):
            if b[i][3-i] == player:
                count_player += 1
            elif b[i][3-i] == -player:
                count_opponent += 1
        if count_opponent == 0:
            if count_player == 3:
                total += 1000
            elif count_player == 2:
                total += 100
            elif count_player == 1:
                total += 10
        return total

    empty_cells = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    if not empty_cells:
        return (0, 0)

    for (i, j) in empty_cells:
        board[i][j] = 1
        if has_won(board, 1):
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0

    for (i, j) in empty_cells:
        board[i][j] = -1
        if has_won(board, -1):
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0

    best_moves = []
    best_score = -10**9
    for (i, j) in empty_cells:
        board[i][j] = 1
        our_score = evaluate_board(board, 1)
        opp_score = evaluate_board(board, -1)
        total_score = our_score - opp_score
        if total_score > best_score:
            best_score = total_score
            best_moves = [(i, j)]
        elif total_score == best_score:
            best_moves.append((i, j))
        board[i][j] = 0

    if not best_moves:
        return (0, 0)
    
    if len(best_moves) == 1:
        return best_moves[0]
    
    center_i = 1.5
    center_j = 1.5
    best_move = best_moves[0]
    min_dist = float('inf')
    for (i, j) in best_moves:
        dist = abs(2*i - 3) + abs(2*j - 3)
        if dist < min_dist:
            min_dist = dist
            best_move = (i, j)
    return best_move
