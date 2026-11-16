def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    return (x, y, z)