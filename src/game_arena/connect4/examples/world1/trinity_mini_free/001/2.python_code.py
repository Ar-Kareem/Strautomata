
def policy(board: list[list[int]]) -> int:
    # Helper function to check if placing a disc at (i, j) creates a four-in-a-row for a given player
    def check_win(i: int, j: int, player: int) -> bool:
        directions = [(0, -1), (0, 1), (-1, 0), (-1, -1), (-1, 1)]
        for dx, dy in directions:
            count = 1  # Current cell
            for step in range(1, 4):
                ni = i + dx * step
                nj = j + dy * step
                if 0 <= ni < 6 and 0 <= nj < 7:
                    if board[ni][nj] == player:
                        count += 1
                    else:
                        break
                else:
                    break
            if count >= 4:
                return True
        return False

    # Check for winning moves (current player's win)
    for j in range(7):
        for i in range(5, -1, -1):
            if board[i][j] == 0:
                if check_win(i, j, 1):
                    return j

    # Check for blocking moves (opponent's win)
    for j in range(7):
        for i in range(5, -1, -1):
            if board[i][j] == 0:
                if check_win(i, j, -1):
                    return j

    # Strategic move: choose column with most empty cells
    empty_counts = [0] * 7
    for j in range(7):
        count = 0
        for i in range(6):
            if board[i][j] == 0:
                count += 1
        empty_counts[j] = count

    max_empty = max(empty_counts)
    for j in range(7):
        if empty_counts[j] == max_empty:
            return j
