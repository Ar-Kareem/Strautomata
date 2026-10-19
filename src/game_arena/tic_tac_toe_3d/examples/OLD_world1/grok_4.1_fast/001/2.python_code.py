
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    n = 3
    size = n * n * n  # 27

    def pos_to_idx(x: int, y: int, z: int) -> int:
        return x * n * n + y * n + z

    def idx_to_pos(idx: int) -> tuple[int, int, int]:
        x = idx // (n * n)
        y = (idx // n) % n
        z = idx % n
        return x, y, z

    def get_winning_lines(n: int) -> list[list[tuple[int, int, int]]]:
        lines = []
        # Orthogonal lines
        # Along x
        for y in range(n):
            for z in range(n):
                lines.append([(0, y, z), (1, y, z), (2, y, z)])
        # Along y
        for x in range(n):
            for z in range(n):
                lines.append([(x, 0, z), (x, 1, z), (x, 2, z)])
        # Along z
        for x in range(n):
            for y in range(n):
                lines.append([(x, y, 0), (x, y, 1), (x, y, 2)])
        # Planar diagonals in xy (fixed z)
        for z in range(n):
            lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
            lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])
        # Planar diagonals in xz (fixed y)
        for y in range(n):
            lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
            lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
        # Planar diagonals in yz (fixed x)
        for x in range(n):
            lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
            lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])
        # Space diagonals
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
        return lines

    winning_lines = get_winning_lines(n)
    lines_idx = [[pos_to_idx(*pos) for pos in line] for line in winning_lines]

    def board_to_tuple(b: list[list[list[int]]]) -> tuple[int, ...]:
        flat = [0] * size
        for x in range(n):
            for y in range(n):
                for z in range(n):
                    flat[pos_to_idx(x, y, z)] = b[x][y][z]
        return tuple(flat)

    def is_win(player: int, flat: tuple[int, ...], lines: list[list[int]]) -> bool:
        for line in lines:
            if all(flat[i] == player for i in line):
                return True
        return False

    def is_board_full(flat: tuple[int, ...]) -> bool:
        return 0 not in flat

    def player_to_move(flat: tuple[int, ...]) -> int:
        moves_made = size - flat.count(0)
        return 1 if moves_made % 2 == 0 else -1

    memo: dict[tuple[int, ...], int] = {}

    def minimax(flat: tuple[int, ...], alpha: int = -2, beta: int = 2) -> int:
        if flat in memo:
            return memo[flat]

        if is_win(1, flat, lines_idx):
            res = 1
        elif is_win(-1, flat, lines_idx):
            res = -1
        elif is_board_full(flat):
            res = 0
        else:
            player = player_to_move(flat)
            legal_moves = [i for i in range(size) if flat[i] == 0]
            legal_moves.sort(key=lambda i: sum(abs(c - 1) for c in idx_to_pos(i)))
            if player == 1:
                res = -2
                for i in legal_moves:
                    new_board = list(flat)
                    new_board[i] = 1
                    score = minimax(tuple(new_board), alpha, beta)
                    res = max(res, score)
                    alpha = max(alpha, res)
                    if alpha >= beta:
                        break
            else:
                res = 2
                for i in legal_moves:
                    new_board = list(flat)
                    new_board[i] = -1
                    score = minimax(tuple(new_board), alpha, beta)
                    res = min(res, score)
                    beta = min(beta, res)
                    if alpha >= beta:
                        break
            memo[flat] = res
            return res

        memo[flat] = res
        return res

    flat = board_to_tuple(board)

    # Quick win check
    for i in range(size):
        if flat[i] == 0:
            new_board = list(flat)
            new_board[i] = 1
            if is_win(1, tuple(new_board), lines_idx):
                x, y, z = idx_to_pos(i)
                return (x, y, z)

    # Legal moves ordered by center preference
    legal_moves = [i for i in range(size) if flat[i] == 0]
    legal_moves.sort(key=lambda i: sum(abs(c - 1) for c in idx_to_pos(i)))

    best_score = -2
    best_idx = -1
    for i in legal_moves:
        new_board = list(flat)
        new_board[i] = 1
        new_t = tuple(new_board)
        memo.clear()  # Clear memo for each root move to avoid invalid bounds, simplify
        score = minimax(new_t)
        if score > best_score:
            best_score = score
            best_idx = i

    x, y, z = idx_to_pos(best_idx)
    return (x, y, z)
