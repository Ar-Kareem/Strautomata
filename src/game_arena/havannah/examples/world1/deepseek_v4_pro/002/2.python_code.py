
import numpy as np
from collections import deque
import time

class HavannahAI:
    def __init__(self, size=15):
        self.size = size
        self.directions = [(0, 1), (1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1)]
        self.corners = [(0, 0), (0, size-1), (size-1, 0), (size-1, size-1), (0, size//2), (size-1, size//2)]
        self.edge_indices = self._init_edges()
        self.real_corners = {(0, 0), (0, size-1), (size-1, 0), (size-1, size-1)}
        self.start_time = 0
        self.time_limit = 0.9
        
    def _init_edges(self):
        edges = {0: set(), 1: set(), 2: set(), 3: set(), 4: set(), 5: set()}
        for i in range(self.size):
            for j in range(self.size):
                if i == 0 and j == 0:
                    continue
                if i == 0:
                    edges[0].add((i, j))
                if j == self.size - 1:
                    edges[1].add((i, j))
                if i == self.size - 1:
                    edges[2].add((i, j))
                if j == 0:
                    edges[3].add((i, j))
        edge_left = {(i, j) for i in range(1, self.size-1) for j in range(self.size) if i + j == self.size - 1}
        edge_right = {(i, j) for i in range(1, self.size-1) for j in range(self.size) if i + j == self.size - 1}
        edges[4] = edge_left
        edges[5] = edge_right
        return edges
    
    def get_neighbors(self, pos):
        r, c = pos
        neighbors = []
        for dr, dc in self.directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbors.append((nr, nc))
        return neighbors
    
    def is_connected_to_edge(self, pos, board, edge_type):
        r, c = pos
        if board[r][c] != 1:
            return False
        visited = set()
        queue = deque([pos])
        visited.add(pos)
        
        while queue:
            curr = queue.popleft()
            cr, cc = curr
            
            if edge_type == 'top' and cr == 0 and cc not in [0, self.size-1]:
                return True
            if edge_type == 'bottom' and cr == self.size - 1 and cc not in [0, self.size-1]:
                return True
            if edge_type == 'left' and cc == 0 and cr not in [0, self.size-1]:
                return True
            if edge_type == 'right' and cc == self.size - 1 and cr not in [0, self.size-1]:
                return True
            if edge_type == 'topleft_corner':
                if cr == 0 and cc == 0:
                    return True
            if edge_type == 'topright_corner':
                if cr == 0 and cc == self.size - 1:
                    return True
            if edge_type == 'bottomleft_corner':
                if cr == self.size - 1 and cc == 0:
                    return True
            if edge_type == 'bottomright_corner':
                if cr == self.size - 1 and cc == self.size - 1:
                    return True
            
            for nr, nc in self.get_neighbors(curr):
                if (nr, nc) not in visited and board[nr][nc] == 1:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return False
    
    def get_connected_group(self, pos, board):
        if board[pos[0]][pos[1]] != 1:
            return set()
        visited = set()
        queue = deque([pos])
        visited.add(pos)
        
        while queue:
            curr = queue.popleft()
            for nr, nc in self.get_neighbors(curr):
                if (nr, nc) not in visited and board[nr][nc] == 1:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return visited
    
    def check_bridge(self, board):
        corner_set = {(0, 0), (0, self.size-1), (self.size-1, 0), (self.size-1, self.size-1)}
        for c1 in corner_set:
            if board[c1[0]][c1[1]] == 1:
                for c2 in corner_set:
                    if c1 < c2 and board[c2[0]][c2[1]] == 1:
                        group1 = self.get_connected_group(c1, board)
                        if c2 in group1:
                            return True
        return False
    
    def check_fork(self, board):
        edge_names = ['top', 'bottom', 'left', 'right']
        touched_edges = set()
        
        for i in range(self.size):
            for j in range(self.size):
                if board[i][j] == 1:
                    pos = (i, j)
                    for edge in edge_names:
                        if self.is_connected_to_edge(pos, board, edge):
                            touched_edges.add(edge)
        
        return len(touched_edges) >= 3
    
    def check_ring(self, board):
        empty_board = [[0 for _ in range(self.size)] for _ in range(self.size)]
        for i in range(self.size):
            for j in range(self.size):
                if board[i][j] == 1:
                    # Check if removing this stone breaks connectivity
                    pass
        return False
    
    def would_win(self, board, move):
        r, c = move
        board[r][c] = 1
        wins = self.check_fork(board) or self.check_bridge(board)
        board[r][c] = -1
        return wins
    
    def build_board(self, stones1, stones2):
        board = [[-1 for _ in range(self.size)] for _ in range(self.size)]
        for r, c in stones1:
            board[r][c] = 1
        for r, c in stones2:
            board[r][c] = 0
        for i in range(self.size):
            for j in range(self.size):
                if not valid_mask_global[i][j]:
                    board[i][j] = -2
        return board
    
    def evaluate_position(self, board, player):
        score = 0
        # Count stones and connectivity
        player_stones = sum(1 for i in range(self.size) for j in range(self.size) if board[i][j] == 1)
        
        # Check edge connectivity
        edge_connections = 0
        edge_names = ['top', 'bottom', 'left', 'right']
        connected_edges = set()
        for i in range(self.size):
            for j in range(self.size):
                if board[i][j] == 1:
                    for edge in edge_names:
                        if self.is_connected_to_edge((i, j), board, edge):
                            connected_edges.add(edge)
        edge_connections = len(connected_edges)
        
        # Check corner connectivity
        corner_stones = sum(1 for c in [(0,0), (0,self.size-1), (self.size-1,0), (self.size-1,self.size-1)] 
                          if board[c[0]][c[1]] == 1)
        
        score = player_stones * 10 + edge_connections * 50 + corner_stones * 30
        
        # Bonus for connected groups
        visited = set()
        for i in range(self.size):
            for j in range(self.size):
                if board[i][j] == 1 and (i, j) not in visited:
                    group = self.get_connected_group((i, j), board)
                    visited.update(group)
                    score += len(group) * len(group) * 2
        
        return score
    
    def find_threats(self, board):
        threats = []
        empty_cells = [(i, j) for i in range(self.size) for j in range(self.size) 
                      if board[i][j] == -1]
        
        for r, c in empty_cells:
            board[r][c] = 1
            if self.check_fork(board) or self.check_bridge(board):
                threats.append((r, c))
            board[r][c] = -1
        
        return threats
    
    def find_opponent_threats(self, board):
        threats = []
        empty_cells = [(i, j) for i in range(self.size) for j in range(self.size) 
                      if board[i][j] == -1]
        
        for r, c in empty_cells:
            board[r][c] = 0
            if self.check_fork(board) or self.check_bridge(board):
                threats.append((r, c))
            board[r][c] = -1
        
        return threats
    
    def get_moves_ordered(self, board):
        empty_cells = [(i, j) for i in range(self.size) for j in range(self.size) 
                      if board[i][j] == -1 and valid_mask_global[i][j]]
        
        if not empty_cells:
            return []
        
        # Score each move
        move_scores = []
        for r, c in empty_cells:
            score = 0
            # Prefer center
            center_dist = abs(r - self.size//2) + abs(c - self.size//2)
            score -= center_dist
            
            # Prefer moves near existing stones
            has_adjacent_own = False
            has_adjacent_opp = False
            for nr, nc in self.get_neighbors((r, c)):
                if board[nr][nc] == 1:
                    has_adjacent_own = True
                elif board[nr][nc] == 0:
                    has_adjacent_opp = True
            
            if has_adjacent_own:
                score += 20
            if has_adjacent_opp:
                score += 10
            
            # Check if move connects edges
            board[r][c] = 1
            edge_connections = 0
            edge_names = ['top', 'bottom', 'left', 'right']
            for edge in edge_names:
                if self.is_connected_to_edge((r, c), board, edge):
                    edge_connections += 1
            score += edge_connections * 30
            board[r][c] = -1
            
            move_scores.append((score, (r, c)))
        
        move_scores.sort(reverse=True)
        return [pos for _, pos in move_scores[:min(30, len(move_scores))]]
    
    def find_winning_move(self, board):
        my_threats = self.find_threats(board)
        if my_threats:
            return my_threats[0]
        return None
    
    def get_best_move(self, board, depth=3):
        self.start_time = time.time()
        
        # Check for immediate win
        win_move = self.find_winning_move(board)
        if win_move:
            return win_move
        
        # Block opponent threats
        opp_threats = self.find_opponent_threats(board)
        if opp_threats:
            return opp_threats[0]
        
        moves = self.get_moves_ordered(board)
        if not moves:
            return None
        
        best_move = moves[0]
        best_score = -float('inf')
        
        for move in moves[:20]:
            if time.time() - self.start_time > self.time_limit:
                break
            
            r, c = move
            board[r][c] = 1
            
            # Quick evaluation
            score = self.evaluate_position(board, 1)
            
            # Check if this creates a threat
            my_follow_threats = self.find_threats(board)
            if my_follow_threats:
                score += 500
            
            # Check if this blocks opponent
            board[r][c] = 0
            opp_blocked_threats = self.find_threats(board)
            if len(opp_blocked_threats) < len(opp_threats):
                score += 300
            
            board[r][c] = 1
            
            if score > best_score:
                best_score = score
                best_move = move
            
            board[r][c] = -1
        
        return best_move


# Global variable for valid mask
valid_mask_global = None
ai = None

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    global valid_mask_global, ai
    
    start = time.time()
    
    # Initialize AI if not done
    if ai is None:
        ai = HavannahAI(size=len(valid_mask))
    
    valid_mask_global = valid_mask
    
    # Build board representation
    board = [[-1 for _ in range(15)] for _ in range(15)]
    
    for r, c in me:
        board[r][c] = 1
    for r, c in opp:
        board[r][c] = 0
    for i in range(15):
        for j in range(15):
            if not valid_mask[i][j]:
                board[i][j] = -2
    
    # First move - play center area
    if len(me) == 0 and len(opp) == 0:
        center_moves = [(7, 7), (7, 6), (6, 7), (6, 6), (7, 8), (8, 7)]
        for move in center_moves:
            if move[0] < 15 and move[1] < 15 and valid_mask[move[0]][move[1]]:
                return move
    
    # Find best move
    best_move = ai.get_best_move(board)
    
    if best_move is None:
        # Fallback: find any valid move
        for i in range(15):
            for j in range(15):
                if valid_mask[i][j] and board[i][j] == -1:
                    return (i, j)
        return (7, 7)
    
    return best_move
