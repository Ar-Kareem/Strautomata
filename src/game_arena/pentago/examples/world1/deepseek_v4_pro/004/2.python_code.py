
import numpy as np
import random
import math
import time

WIN_COUNT = 5

def policy(you, opponent):
    you_np = np.array(you, dtype=np.int32)
    opp_np = np.array(opponent, dtype=np.int32)
    
    start_time = time.time()
    time_limit = 0.8
    
    empty_cells = [(r, c) for r in range(6) for c in range(6) 
                   if you_np[r][c] == 0 and opp_np[r][c] == 0]
    
    if not empty_cells:
        r, c = 0, 0
        return f"{r+1},{c+1},0,L"
    
    all_moves = []
    for r, c in empty_cells:
        for quad in range(4):
            for direction in ['L', 'R']:
                all_moves.append((r, c, quad, direction))
    
    def check_win_after_move(board_you, board_opp, move):
        r, c, quad, direction = move
        temp_you = board_you.copy()
        temp_opp = board_opp.copy()
        
        temp_you[r][c] = 1
        
        qr_start = (quad // 2) * 3
        qc_start = (quad % 2) * 3
        
        sub_you = temp_you[qr_start:qr_start+3, qc_start:qc_start+3].copy()
        sub_opp = temp_opp[qr_start:qr_start+3, qc_start:qc_start+3].copy()
        
        if direction == 'R':
            sub_you = np.rot90(sub_you, k=-1)
            sub_opp = np.rot90(sub_opp, k=-1)
        else:
            sub_you = np.rot90(sub_you, k=1)
            sub_opp = np.rot90(sub_opp, k=1)
        
        temp_you[qr_start:qr_start+3, qc_start:qc_start+3] = sub_you
        temp_opp[qr_start:qr_start+3, qc_start:qc_start+3] = sub_opp
        
        return has_5_in_a_row(temp_you), has_5_in_a_row(temp_opp)
    
    def has_5_in_a_row(board):
        for r in range(6):
            for c in range(2):
                if sum(board[r][c:c+5]) >= WIN_COUNT:
                    return True
        
        for c in range(6):
            for r in range(2):
                if sum(board[r:r+5, c]) >= WIN_COUNT:
                    return True
        
        for r in range(2):
            for c in range(2):
                diag1 = [board[r+i][c+i] for i in range(5)]
                if sum(diag1) >= WIN_COUNT:
                    return True
        
        for r in range(2):
            for c in range(4, 6):
                diag2 = [board[r+i][c-i] for i in range(5)]
                if sum(diag2) >= WIN_COUNT:
                    return True
        
        return False
    
    immediate_wins = []
    safe_moves = []
    
    for move in all_moves:
        you_win, opp_win = check_win_after_move(you_np, opp_np, move)
        if you_win:
            immediate_wins.append(move)
        elif not opp_win:
            safe_moves.append(move)
    
    if immediate_wins:
        move = random.choice(immediate_wins)
        return f"{move[0]+1},{move[1]+1},{move[2]},{move[3]}"
    
    if not safe_moves:
        safe_moves = all_moves
    
    def count_lines(board, player_board, length):
        count = 0
        for r in range(6):
            for c in range(6 - length + 1):
                if all(board[r][c+i] == 1 for i in range(length)):
                    count += 1
        
        for c in range(6):
            for r in range(6 - length + 1):
                if all(board[r+i][c] == 1 for i in range(length)):
                    count += 1
        
        for r in range(6 - length + 1):
            for c in range(6 - length + 1):
                if all(board[r+i][c+i] == 1 for i in range(length)):
                    count += 1
        
        for r in range(6 - length + 1):
            for c in range(length - 1, 6):
                if all(board[r+i][c-i] == 1 for i in range(length)):
                    count += 1
        
        return count
    
    def heuristic(board_you, board_opp):
        you_2 = count_lines(board_you, board_you, 2)
        you_3 = count_lines(board_you, board_you, 3)
        you_4 = count_lines(board_you, board_you, 4)
        
        opp_2 = count_lines(board_opp, board_opp, 2)
        opp_3 = count_lines(board_opp, board_opp, 3)
        opp_4 = count_lines(board_opp, board_opp, 4)
        
        score = (you_2 * 1 + you_3 * 10 + you_4 * 100 - 
                 opp_2 * 1 - opp_3 * 15 - opp_4 * 200)
        
        for r in range(6):
            for c in range(6):
                if board_you[r][c] == 1:
                    dist_center = abs(r - 2.5) + abs(c - 2.5)
                    score += max(0, (5 - dist_center) * 2)
        
        return score
    
    class MCTSNode:
        def __init__(self, board_you, board_opp, move=None, parent=None):
            self.board_you = board_you
            self.board_opp = board_opp
            self.move = move
            self.parent = parent
            self.children = []
            self.visits = 0
            self.value = 0
            self.untried_moves = None
        
        def ucb1(self, exploration=1.4):
            if self.visits == 0:
                return float('inf')
            return self.value / self.visits + exploration * math.sqrt(
                math.log(self.parent.visits) / self.visits)
    
    def simulate_move(board_you, board_opp, move):
        r, c, quad, direction = move
        temp_you = board_you.copy()
        temp_opp = board_opp.copy()
        
        temp_you[r][c] = 1
        
        qr_start = (quad // 2) * 3
        qc_start = (quad % 2) * 3
        
        sub_you = temp_you[qr_start:qr_start+3, qc_start:qc_start+3].copy()
        sub_opp = temp_opp[qr_start:qr_start+3, qc_start:qc_start+3].copy()
        
        if direction == 'R':
            sub_you = np.rot90(sub_you, k=-1)
            sub_opp = np.rot90(sub_opp, k=-1)
        else:
            sub_you = np.rot90(sub_you, k=1)
            sub_opp = np.rot90(sub_opp, k=1)
        
        temp_you[qr_start:qr_start+3, qc_start:qc_start+3] = sub_you
        temp_opp[qr_start:qr_start+3, qc_start:qc_start+3] = sub_opp
        
        return temp_you, temp_opp
    
    def get_rollout_moves(board_you, board_opp):
        empty = [(r, c) for r in range(6) for c in range(6) 
                 if board_you[r][c] == 0 and board_opp[r][c] == 0]
        
        if not empty:
            return []
        
        scored_moves = []
        for r, c in empty:
            score = 0
            
            if has_potential_win(board_you, r, c):
                score += 1000
            
            temp_board = board_you.copy()
            temp_board[r][c] = 1
            if has_potential_win(temp_board, r, c):
                score += 500
            
            temp_board_opp = board_opp.copy()
            if has_potential_win(temp_board_opp, r, c):
                score += 800
            
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 6 and 0 <= nc < 6:
                        if board_you[nr][nc] == 1:
                            score += 10
            
            scored_moves.append((score, r, c))
        
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        
        top_n = min(10, len(scored_moves))
        selected = scored_moves[:top_n]
        
        quads = [0, 1, 2, 3]
        dirs = ['L', 'R']
        
        rollout_moves = []
        for _, r, c in selected:
            quad_scores = []
            for q in quads:
                for d in dirs:
                    qr_start = (q // 2) * 3
                    qc_start = (q % 2) * 3
                    if qr_start <= r < qr_start + 3 and qc_start <= c < qc_start + 3:
                        quad_scores.append((1, q, d))
                    else:
                        quad_scores.append((0, q, d))
            
            for _, q, d in quad_scores:
                rollout_moves.append((r, c, q, d))
        
        return rollout_moves
    
    def has_potential_win(board, r, c):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            count = 1
            for i in range(1, 5):
                nr, nc = r + dr * i, c + dc * i
                if 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == 1:
                    count += 1
                else:
                    break
            
            for i in range(1, 5):
                nr, nc = r - dr * i, c - dc * i
                if 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == 1:
                    count += 1
                else:
                    break
            
            if count >= 4:
                return True
        
        return False
    
    def rollout(board_you, board_opp, depth=0):
        current_you = board_you.copy()
        current_opp = board_opp.copy()
        player_turn = False
        max_depth = 10
        
        while depth < max_depth:
            empty = np.sum(current_you == 0) - np.sum(np.logical_and(
                current_you == 0, current_opp == 0))
            empty_count = np.sum((current_you == 0) & (current_opp == 0))
            
            if empty_count == 0:
                break
            
            if not player_turn:
                moves = get_rollout_moves(current_you, current_opp)
                if not moves:
                    break
                move = random.choice(moves)
                current_you, current_opp = simulate_move(
                    current_you, current_opp, move)
                
                if has_5_in_a_row(current_you):
                    return 1.0
            else:
                moves = get_rollout_moves(current_opp, current_you)
                if not moves:
                    break
                move = random.choice(moves)
                current_opp, current_you = simulate_move(
                    current_opp, current_you, move)
                
                if has_5_in_a_row(current_opp):
                    return -1.0
            
            player_turn = not player_turn
            depth += 1
        
        return heuristic(current_you, current_opp) / 1000.0
    
    root = MCTSNode(you_np, opp_np)
    
    iterations = 0
    while time.time() - start_time < time_limit:
        node = root
        
        if node.untried_moves is None:
            node.untried_moves = list(safe_moves)
            random.shuffle(node.untried_moves)
        
        while node.untried_moves == [] and node.children:
            node = max(node.children, key=lambda n: n.ucb1())
        
        if node.untried_moves:
            move = node.untried_moves.pop()
            new_you, new_opp = simulate_move(node.board_you, node.board_opp, move)
            child = MCTSNode(new_you, new_opp, move, node)
            node.children.append(child)
            node = child
        
        result = rollout(node.board_you, node.board_opp)
        
        while node:
            node.visits += 1
            node.value += result
            node = node.parent
        
        iterations += 1
        if iterations > 5000:
            break
    
    if root.children:
        best_child = max(root.children, key=lambda n: n.visits)
        move = best_child.move
    else:
        move = random.choice(safe_moves)
    
    return f"{move[0]+1},{move[1]+1},{move[2]},{move[3]}"
