
def policy(board):
    def compute_line_count(r, c, dr, dc):
        if dr == 0:
            # Horizontal line (row)
            return sum(board[r][col] != 0 for col in range(8))
        elif dc == 0:
            # Vertical line (column)
            return sum(board[row][c] != 0 for row in range(8))
        else:
            # Diagonal line (r - c is constant)
            dir_val = r - c
            count = 0
            for x in range(8):
                y = x - dir_val
                if 0 <= y < 8:
                    count += board[x][y] != 0
            return count

    valid_moves = []
    directions = [ (0, 1), (0, -1), (1, 0), (-1, 0),
                  (-1, 1), (1, -1), (-1, -1), (1, 1) ]

    for r in range(8):
        for c in range(8):
            if board[r][c] == 1:
                for (dr, dc) in directions:
                    line_count = compute_line_count(r, c, dr, dc)
                    if line_count == 0:
                        continue  # Shouldn't happen since current cell is 1

                    k = line_count
                    new_r = r + dr * k
                    new_c = c + dc * k

                    # Check new position is on the board
                    if not (0 <= new_r < 8 and 0 <= new_c < 8):
                        continue

                    # Ensure target cell is not our own piece
                    if board[new_r][new_c] == 1:
                        continue

                    # Check path for enemy pieces between start and new position
                    valid = True
                    for i in range(1, k):  # Check intermediate cells up to k-1
                        x = r + dr * i
                        y = c + dc * i
                        if x < 0 or x >= 8 or y < 0 or y >= 8:
                            valid = False
                            break
                        if board[x][y] == -1:
                            valid = False
                            break

                    if valid:
                        valid_moves.append((r, c, new_r, new_c))

    # Categorize moves into captures and non-captures
    capture_moves = []
    other_moves = []

    for move in valid_moves:
        fr, fc, tr, tc = move
        if board[tr][tc] == -1:
            capture_moves.append(move)

    # Select the best move based on priority
    def distance_to_center(r, c):
        return (r - 3.5)**2 + (c - 3.5)**2

    if capture_moves:
        # Select capture move closest to the center
        best_cm = None
        best_distance = float('inf')
        for move in capture_moves:
            tr, tc = move[2], move[3]
            d = distance_to_center(tr, tc)
            if d < best_distance:
                best_capture = move
                best_distance = d
        best_move = best_capture
    else:
        # Select non-capture move closest to the center
        best_dist = float('inf')
        best_move = None
        for move in other_moves:
            tr, tc = move[2], move[3]
            d = distance_to_center(tr, tc)
            if d < best_dist:
                best_dist = d
                best_move = move

        # Fallback if no moves found (problem states there must be a move)
        if not best_move:
            best_move = valid_moves[0]

    fr, fc, tr, tc = best_move
    return f"{fr},{fc}:{tr},{tc}"
