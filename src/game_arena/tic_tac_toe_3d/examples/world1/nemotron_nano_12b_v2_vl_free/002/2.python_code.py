
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def get_lines():
        lines = []
        # Axis-aligned lines (x, y, z)
        for y in range(3):
            for z in range(3):
                lines.append([(x, y, z) for x in range(3)])
        for x in range(3):
            for z in range(3):
                lines.append([(x, y, z) for y in range(3)])
        for x in range(3):
            for y in range(3):
                lines.append([(x, y, z) for z in range(3)])
        # Face diagonals (xy plane)
        for z in range(3):
            lines.append([(c, c, z) for c in range(3)])
            lines.append([(2 - c, c, z) for c in range(3)])
        # Face diagonals (xz plane)
        for y in range(3):
            lines.append([(c, y, c) for c in range(3)])
            lines.append([(2 - c, y, c) for c in range(3)])
        # Face diagonals (yz plane)
        for x in range(3):
            lines.append([(x, c, c) for c in range(3)])
            lines.append([(x, 2 - c, c) for c in range(3)])
        # Space diagonals
        lines.append([(x, x, x) for x in range(3)])
        lines.append([(2 - x, 2 - x, x) for x in range(3)])
        lines.append([(2 - x, x, 2 - x) for x in range(3)])
        lines.append([(x, x, 2 - x) for x in range(3)])
        return lines

    def check_win_or_block(lines, player, opponent):
        for line in lines:
            player_count = 0
            opp_count = 0
            empty = []
            for (i, j, k) in line:
                val = board[i][j][k]
                if val == player:
                    player_count += 1
                elif val == opponent:
                    opp_count += 1
                else:
                    empty.append((i, j, k))
            if player_count == 2 and opp_count == 0 and len(empty) == 1:
                return empty[0]
            if player_count == 1 and opp_count == 2 and len(empty) == 1:
                return empty[0]
        return None

    lines = get_lines()
    winning_move = check_win_or_block(lines, 1, -1)
    if winning_move:
        return winning_move

    blocking_move = check_win_or_block(lines, -1, 1)
    if blocking_move:
        return blocking_move

    # Heuristic: center, corners, edges, then others
    priority_order = [
        (1, 1, 1),  # center
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2),  # corners
        (0, 1, 1), (2, 1, 1), (1, 0, 1), (1, 2, 1),
        (1, 1, 0), (1, 1, 2),  # edge centers
        (0, 1, 0), (0, 1, 2), (2, 1, 0), (2, 1, 2),
        (0, 0, 1), (2, 0, 1), (0, 2, 1), (2, 2, 1),
        (1, 0, 0), (1, 0, 2), (1, 2, 0), (1, 2, 2),
    ]

    for cell in priority_order:
        i, j, k = cell
        if board[i][j][k] == 0:
            return (i, j, k)
    return (0, 0, 0)  # Fallback (should never reach here)
