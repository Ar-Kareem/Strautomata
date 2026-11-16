
import collections

def policy(you, opponent) -> str:
    # Convert inputs to a mutable 2D list for simulation
    # 1 for 'you', -1 for 'opponent', 0 for empty
    board = [[0]*6 for _ in range(6)]
    empty_cells = []
    for r in range(6):
        for c in range(6):
            if you[r][c] == 1:
                board[r][c] = 1
            elif opponent[r][c] == 1:
                board[r][c] = -1
            else:
                empty_cells.append((r, c))

    def check_win(b, player_val):
        # Check rows
        for r in range(6):
            for c in range(2):
                if all(b[r][c+i] == player_val for i in range(5)): return True
        # Check cols
        for c in range(6):
            for r in range(2):
                if all(b[r+i][c] == player_val for i in range(5)): return True
        # Check diagonals
        for r in range(2):
            for c in range(2):
                if all(b[r+i][c+i] == player_val for i in range(5)): return True
            for c in range(4, 6):
                if all(b[r+i][c-i] == player_val for i in range(5)): return True
        return False

    def get_rotated_quad(b, quad, direction):
        # quad 0: 0..2, 0..2 | 1: 0..2, 3..5 | 2: 3..5, 0..2 | 3: 3..5, 3..5
        r_start = 0 if quad < 2 else 3
        c_start = 0 if quad % 2 == 0 else 3
        
        original = [row[c_start:c_start+3] for row in b[r_start:r_start+3]]
        rotated = [[0]*3 for _ in range(3)]
        
        for r in range(3):
            for c in range(3):
                if direction == 'R':
                    rotated[c][2-r] = original[r][c]
                else:
                    rotated[2-c][r] = original[r][c]
        return r_start, c_start, rotated

    def apply_move(b, r, c, quad, direction):
        new_board = [row[:] for row in b]
        new_board[r][c] = 1  # Place marble
        
        rs, cs, quad_data = get_rotated_quad(new_board, quad, direction)
        for i in range(3):
            for j in range(3):
                new_board[rs+i][cs+j] = quad_data[i][j]
        return new_board

    # 1. Search for immediate winning move
    for r, c in empty_cells:
        for quad in range(4):
            for direction in ['L', 'R']:
                sim_board = apply_move(board, r, c, quad, direction)
                if check_win(sim_board, 1):
                    return f"{r+1},{c+1},{quad},{direction}"

    # 2. Heuristic: Center-weighted move
    # Center cells are more valuable in Pentago
    def dist_to_center(r, c):
        return abs(r - 2.5) + abs(c - 2.5)

    empty_cells.sort(key=lambda x: dist_to_center(x[0], x[1]))
    best_move = empty_cells[0]
    
    # Return first available center-ish move
    return f"{best_move[0]+1},{best_move[1]+1},0,R"
