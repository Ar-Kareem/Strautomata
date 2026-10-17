
import random
from collections import deque, defaultdict

def policy(board) -> str:
    def get_legal_moves(board_state, current_player):
        rows = 8
        cols = 8
        directions = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]
        legal_moves = []
        
        row_counts = [sum(1 for cell in board_state[row] if cell != 0) for row in range(rows)]
        col_counts = [sum(1 for row in range(rows) if board_state[row][col] != 0) for col in range(cols)]
        
        main_diag_counts = defaultdict(int)
        anti_diag_counts = defaultdict(int)
        for i in range(rows):
            for j in range(cols):
                if board_state[i][j] != 0:
                    main_diag_counts[i - j] += 1
                    anti_diag_counts[i + j] += 1
        
        for r in range(rows):
            for c in range(cols):
                if board_state[r][c] != current_player:
                    continue
                for dx, dy in directions:
                    if dx == 0 and dy != 0:  # Horizontal
                        s = row_counts[r]
                    elif dy == 0 and dx != 0:  # Vertical
                        s = col_counts[c]
                    else:  # Diagonal
                        if dx == dy:
                            s = main_diag_counts[r - c]
                        else:
                            s = anti_diag_counts[r + c]
                    
                    tr = r + dx * s
                    tc = c + dy * s
                    
                    if 0 <= tr < rows and 0 <= tc < cols:
                        valid = True
                        for step in range(1, s):
                            cr = r + dx * step
                            cc = c + dy * step
                            if not (0 <= cr < rows and 0 <= cc < cols):
                                valid = False
                                break
                            if board_state[cr][cc] == -current_player:
                                valid = False
                                break
                        if not valid:
                            continue
                        if board_state[tr][tc] != current_player:
                            legal_moves.append((r, c, tr, tc))
        return legal_moves
    
    def apply_move(board_state, move, player):
        r1, c1, r2, c2 = move
        new_board = [row[:] for row in board_state]
        new_board[r1][c1] = 0
        new_board[r2][c2] = player
        return new_board
    
    def evaluate_board(board_state):
        def largest_cluster_size(player):
            visited = set()
            max_size = 0
            for i in range(8):
                for j in range(8):
                    if board_state[i][j] == player and (i, j) not in visited:
                        q = deque([(i, j)])
                        visited.add((i, j))
                        size = 1
                        while q:
                            x, y = q.popleft()
                            for dx in [-1, 0, 1]:
                                for dy in [-1, 0, 1]:
                                    if dx == 0 and dy == 0:
                                        continue
                                    nx, ny = x + dx, y + dy
                                    if 0 <= nx < 8 and 0 <= ny < 8:
                                        if board_state[nx][ny] == player and (nx, ny) not in visited:
                                            visited.add((nx, ny))
                                            q.append((nx, ny))
                                            size += 1
                        max_size = max(max_size, size)
            return max_size
        
        my_cluster = largest_cluster_size(1)
        opp_cluster = largest_cluster_size(-1)
        my_pieces = sum(row.count(1) for row in board_state)
        opp_pieces = sum(row.count(-1) for row in board_state)
        return my_cluster * 100 - opp_cluster * 100 + (my_pieces - opp_pieces) * 10
    
    legal_moves = get_legal_moves(board, 1)
    if not legal_moves:
        return ""
    
    best_score = -float('inf')
    best_moves = []
    
    for move in legal_moves:
        new_board = apply_move(board, move, 1)
        score = evaluate_board(new_board)
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)
    
    chosen_move = random.choice(best_moves)
    return f"{chosen_move[0]},{chosen_move[1]}:{chosen_move[2]},{chosen_move[3]}"
