
# 3x3x3 Tic Tac Toe AI using alpha-beta minimax with heuristics and optimizations

lines = []

# Lines along x
for y in range(3):
    for z in range(3):
        lines.append([(0, y, z), (1, y, z), (2, y, z)])

# Lines along y
for x in range(3):
    for z in range(3):
        lines.append([(x, 0, z), (x, 1, z), (x, 2, z)])

# Lines along z
for x in range(3):
    for y in range(3):
        lines.append([(x, y, 0), (x, y, 1), (x, y, 2)])

# Diagonals in xy planes (fixed z)
for z in range(3):
    lines.append([(0, 0, z), (1, 1, z), (2, 2, z)])
    lines.append([(0, 2, z), (1, 1, z), (2, 0, z)])

# Diagonals in xz planes (fixed y)
for y in range(3):
    lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
    lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])

# Diagonals in yz planes (fixed x)
for x in range(3):
    lines.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)])
    lines.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)])

# Space diagonals
lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

positions = [(i, j, k) for i in range(3) for j in range(3) for k in range(3)]
degrees = {pos: sum(1 for line in lines if pos in line) for pos in positions}

INF = 1000000

def get_winner(board):
    for p in (1, -1):
        for line in lines:
            if all(board[pos[0]][pos[1]][pos[2]] == p for pos in line):
                return p
    return None

def is_full(board):
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return False
    return True

def heuristic(board):
    score = 0
    for line in lines:
        c1 = sum(1 for pos in line if board[pos[0]][pos[1]][pos[2]] == 1)
        cm1 = sum(1 for pos in line if board[pos[0]][pos[1]][pos[2]] == -1)
        e = 3 - c1 - cm1
        if c1 == 2 and e == 1:
            score += 1000
        if cm1 == 2 and e == 1:
            score -= 1000
        if c1 == 1 and e == 2:
            score += 10
        if cm1 == 1 and e == 2:
            score -= 10
        if c1 == 0 and e == 3:
            score += 1
        if cm1 == 0 and e == 3:
            score -= 1
    # Position value
    for pos, deg in degrees.items():
        b = board[pos[0]][pos[1]][pos[2]]
        if b == 1:
            score += deg // 2
        elif b == -1:
            score -= deg // 2
    return score

def minimax(board, depth, alpha, beta, maximizing):
    winner = get_winner(board)
    if winner is not None:
        return INF if winner == 1 else -INF
    if is_full(board):
        return 0
    if depth == 0:
        return heuristic(board)
    if maximizing:
        value = -INF
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        board[i][j][k] = 1
                        score = minimax(board, depth - 1, alpha, beta, False)
                        board[i][j][k] = 0
                        value = max(value, score)
                        alpha = max(alpha, value)
                        if beta <= alpha:
                            return value
        return value
    else:
        value = INF
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        board[i][j][k] = -1
                        score = minimax(board, depth - 1, alpha, beta, True)
                        board[i][j][k] = 0
                        value = min(value, score)
                        beta = min(beta, value)
                        if beta <= alpha:
                            return value
        return value

def get_moves(board):
    return [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    moves = get_moves(board)
    if not moves:
        return (1, 1, 1)  # shouldn't happen

    # Check for immediate wins (prioritize high degree)
    ordered_moves = sorted(moves, key=lambda p: degrees[p], reverse=True)
    for move in ordered_moves:
        i, j, k = move
        board[i][j][k] = 1
        if get_winner(board) == 1:
            board[i][j][k] = 0
            return move
        board[i][j][k] = 0

    # Check opponent threats and pick best block
    threats = []
    for move in moves:
        i, j, k = move
        board[i][j][k] = -1
        if get_winner(board) == -1:
            threats.append(move)
        board[i][j][k] = 0
    if threats:
        best_block = max(threats, key=lambda p: degrees[p])
        return best_block

    # Alpha-beta search
    remaining = len(moves)
    depth = 8
    if remaining <= 12:
        depth = remaining

    best_score = -INF - 1
    best_move = ordered_moves[0]
    ordered_moves = sorted(moves, key=lambda p: degrees[p], reverse=True)
    for move in ordered_moves:
        i, j, k = move
        board[i][j][k] = 1
        score = minimax(board, depth - 1, -INF, INF, False)
        board[i][j][k] = 0
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
