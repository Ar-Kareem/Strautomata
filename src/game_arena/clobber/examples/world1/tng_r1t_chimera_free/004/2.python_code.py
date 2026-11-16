
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    you_board = np.array(you)
    opponent_board = np.array(opponent)
    
    def get_legal_moves(y, o):
        moves = []
        directions = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
        for row in range(5):
            for col in range(6):
                if y[row, col] == 1:
                    for dir, (dr, dc) in directions.items():
                        nr, nc = row + dr, col + dc
                        if 0 <= nr < 5 and 0 <= nc < 6 and o[nr, nc] == 1:
                            moves.append(f"{row},{col},{dir}")
        return moves
    
    legal_moves = get_legal_moves(you_board, opponent_board)
    if not legal_moves:
        return ""
    
    def apply_move(y, o, move):
        r, c, d = move.split(',')
        r, c = int(r), int(c)
        dr, dc = {'U': (-1,0), 'D': (1,0), 'L': (0,-1), 'R': (0,1)}[d]
        new_y = y.copy()
        new_o = o.copy()
        new_y[r, c] = 0
        nr, nc = r + dr, c + dc
        new_y[nr, nc] = 1
        new_o[nr, nc] = 0
        return new_y, new_o
    
    def count_opponent_moves(y, o):
        count = 0
        for row in range(5):
            for col in range(6):
                if o[row, col] == 1:
                    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nr, nc = row + dr, col + dc
                        if 0 <= nr < 5 and 0 <= nc < 6 and y[nr, nc] == 1:
                            count += 1
        return count
    
    def adjacency(o, row, col):
        adj = 0
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < 5 and 0 <= nc < 6 and o[nr, nc] == 1:
                adj += 1
        return adj
    
    move_scores = []
    for move in legal_moves:
        r, c, d = move.split(',')
        r, c = int(r), int(c)
        dr, dc = {'U': -1, 'D': 1, 'L': 0, 'R': 0}[d], {'U': 0, 'D': 0, 'L': -1, 'R': 1}[d]
        cap_r, cap_c = r + dr, c + dc
        new_y, new_o = apply_move(you_board, opponent_board, move)
        opp_moves = count_opponent_moves(new_y, new_o)
        adj = adjacency(opponent_board, cap_r, cap_c)
        move_scores.append((opp_moves, adj, move))
    
    move_scores.sort(key=lambda x: (x[0], x[1]))
    return move_scores[0][2]
