
def policy(you, opponent):
    # Find the first empty cell in row-major order
    placed_r, placed_c = -1, -1
    for r in range(6):
        for c in range(6):
            if you[r][c] == 0 and opponent[r][c] == 0:
                placed_r, placed_c = r, c
                break
        if placed_r != -1:
            break

    # Determine the quadrant of the placed cell
    if placed_r < 3:
        if placed_c < 3:
            quad = 0
        else:
            quad = 1
    else:
        if placed_c < 3:
            quad = 2
        else:
            quad = 3

    # Choose rotation direction based on the quadrant
    direction = 'L' if quad % 2 == 0 else 'R'
    return f"{placed_r + 1},{placed_c + 1},{quad},{direction}"
