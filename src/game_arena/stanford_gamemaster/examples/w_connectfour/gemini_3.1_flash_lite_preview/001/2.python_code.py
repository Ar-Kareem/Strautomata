
def policy(state: list[list[object]], role: str) -> str:
    # Build a board representation
    board = {}
    for fact in state:
        if fact[0] == "cell":
            col, row, color = int(fact[1]), int(fact[2]), fact[3]
            board[(col, row)] = color

    # Determine height of each column
    cols = {i: 0 for i in range(1, 8)}
    for (col, row), _ in board.items():
        if row > cols[col]:
            cols[col] = row

    def get_color(c, r):
        return board.get((c, r))

    # A move is legal if the column has < 6 pieces
    legal_moves = [c for c in range(1, 8) if cols[c] < 6]

    # Strategy: 1. Win if possible, 2. Block opponent win, 3. Prefer center
    for col in legal_moves:
        row = cols[col] + 1
        # Check for immediate win (simulated)
        board[(col, row)] = role
        if check_win(board, role):
            del board[(col, row)]
            return f"drop({col})"
        del board[(col, row)]

    opponent = "black" if role == "red" else "red"
    for col in legal_moves:
        row = cols[col] + 1
        board[(col, row)] = opponent
        if check_win(board, opponent):
            del board[(col, row)]
            return f"drop({col})"
        del board[(col, row)]

    # Default: move to center
    return f"drop({sorted(legal_moves, key=lambda c: abs(c - 4))[0]})"

def check_win(board, color):
    for c in range(1, 8):
        for r in range(1, 7):
            if board.get((c, r)) == color:
                # Check horizontal, vertical, diagonal
                for dc, dr in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                    if all(board.get((c + i*dc, r + i*dr)) == color for i in range(1, 4)):
                        return True
    return False
