
import random
import math
import time
import numpy as np
from collections import defaultdict

# Offsets for hexagonal neighbors on a 2D array representation
NEIGHBOR_OFFSETS = [
    (0, 1), (0, -1),   # same column: up, down
    (1, 0), (-1, 0),   # left column: down-left, up-left
    (1, 1), (-1, -1)   # right column: down-right, up-right
]

def policy(me, opp, valid_mask):
    start_time = time.time()
    board_size = len(valid_mask)
    
    # Convert to set for O(1) lookup
    my_stones = set(me)
    opp_stones = set(opp)
    all_stones = my_stones | opp_stones
    
    # Immediate win/block detection
    best_move = None
    for r in range(board_size):
        for c in range(board_size):
            if not valid_mask[r][c]:
                continue
            # Check if this move wins for me
            my_stones.add((r, c))
            if check_win(my_stones, board_size):
                my_stones.remove((r, c))
                return (r, c)
            my_stones.remove((r, c))
            
            # Check if this move wins for opponent (need to block)
            opp_stones.add((r, c))
            if check_win(opp_stones, board_size):
                opp_stones.remove((r, c))
                best_move = (r, c)  # Remember to block
            opp_stones.remove((r, c))
    
    if best_move:
        return best_move
    
    # Generate all legal moves with heuristic ordering
    legal_moves = []
    for r in range(board_size):
        for c in range(board_size):
            if valid_mask[r][c]:
                legal_moves.append((r, c))
    
    if not legal_moves:
        # Should not happen in Havannah
        return (0, 0)
    
    # If few moves left or time is very short, use heuristic
    if len(legal_moves) <= 5:
        return greedy_heuristic(my_stones, opp_stones, legal_moves, board_size)
    
    # Order moves by proximity to existing stones and corners/edges
    legal_moves = order_moves(legal_moves, my_stones, opp_stones, board_size)
    
    # Initialize MCTS tree
    root = MCTSNode(parent=None, move=None, player=0, 
                    my_stones=my_stones, opp_stones=opp_stones, 
                    legal_moves=legal_moves)
    
    # Iterative deepening within time limit
    iterations = 0
    while time.time() - start_time < 0.95:  # Leave 50ms buffer
        # Selection
        node = root
        while node.children and not node.terminal:
            node = node.select_child()
        
        # Expansion
        if not node.terminal and node.visits > 0 and node.untried_moves:
            node = node.expand()
        
        # Simulation
        winner = node.rollout(board_size)
        
        # Backpropagation
        while node:
            node.update(winner)
            node = node.parent
        iterations += 1
    
    # Choose best move
    if root.children:
        best_child = max(root.children, key=lambda c: c.visits)
        return best_child.move
    else:
        # Fallback to heuristic
        return greedy_heuristic(my_stones, opp_stones, legal_moves, board_size)

def order_moves(moves, my_stones, opp_stones, board_size):
    """Order moves by heuristic priority"""
    if not moves:
        return moves
    
    scores = []
    for (r, c) in moves:
        score = 0
        
        # Proximity to my stones
        for (mr, mc) in my_stones:
            dist = max(abs(r - mr), abs(c - mc))
            if dist == 1:
                score += 10
            elif dist == 2:
                score += 3
            elif dist <= 4:
                score += 1
        
        # Proximity to opponent stones (for blocking)
        for (or_, oc) in opp_stones:
            dist = max(abs(r - or_), abs(c - oc))
            if dist == 1:
                score += 5
            elif dist == 2:
                score += 2
        
        # Corner/edge preference
        if r == 0 or r == board_size-1 or c == 0 or c == board_size-1:
            score += 2
        if (r == 0 and c == 0) or (r == 0 and c == board_size-1) or \
           (r == board_size-1 and c == 0) or (r == board_size-1 and c == board_size-1):
            score += 5
        
        scores.append((score, (r, c)))
    
    # Sort by score descending
    scores.sort(reverse=True)
    return [move for _, move in scores]

def greedy_heuristic(my_stones, opp_stones, legal_moves, board_size):
    """Fallback greedy heuristic"""
    if not legal_moves:
        return (0, 0)
    
    best_score = -1
    best_move = legal_moves[0]
    
    for (r, c) in legal_moves:
        score = 0
        
        # Count friendly neighbors
        for dr, dc in NEIGHBOR_OFFSETS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < board_size and 0 <= nc < board_size:
                if (nr, nc) in my_stones:
                    score += 3
                elif (nr, nc) in opp_stones:
                    score += 1
        
        # Edge/corner bonus
        if r == 0 or r == board_size-1 or c == 0 or c == board_size-1:
            score += 1
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move

class MCTSNode:
    def __init__(self, parent, move, player, my_stones, opp_stones, legal_moves):
        self.parent = parent
        self.move = move
        self.player = player  # 0 = me, 1 = opponent
        self.my_stones = set(my_stones)
        self.opp_stones = set(opp_stones)
        self.legal_moves = legal_moves.copy()
        
        self.children = []
        self.untried_moves = legal_moves.copy()
        
        self.visits = 0
        self.wins = 0  # wins from perspective of original player (player 0)
        
        # Terminal if someone has won or no moves left
        self.terminal = False
        if check_win(self.my_stones, len(valid_mask) if 'valid_mask' in globals() else 15):
            self.terminal = True
            self.winner = 0
        elif check_win(self.opp_stones, len(valid_mask) if 'valid_mask' in globals() else 15):
            self.terminal = True
            self.winner = 1
        elif not self.legal_moves:
            self.terminal = True
            self.winner = -1  # draw
    
    def select_child(self):
        """UCT selection"""
        C = 1.414  # exploration constant
        
        best_score = -float('inf')
        best_child = None
        
        for child in self.children:
            if child.visits == 0:
                ucb = float('inf')
            else:
                exploitation = child.wins / child.visits
                exploration = C * math.sqrt(math.log(self.visits) / child.visits)
                ucb = exploitation + exploration
            
            if ucb > best_score:
                best_score = ucb
                best_child = child
        
        return best_child
    
    def expand(self):
        """Expand an untried move"""
        if not self.untried_moves:
            return self
        
        move = self.untried_moves.pop()
        
        # Create new state
        if self.player == 0:
            new_my_stones = self.my_stones | {move}
            new_opp_stones = self.opp_stones
        else:
            new_my_stones = self.my_stones
            new_opp_stones = self.opp_stones | {move}
        
        # Remove move from legal moves
        new_legal_moves = [m for m in self.legal_moves if m != move]
        
        # Create child node
        child = MCTSNode(
            parent=self,
            move=move,
            player=1 - self.player,  # switch player
            my_stones=new_my_stones,
            opp_stones=new_opp_stones,
            legal_moves=new_legal_moves
        )
        
        self.children.append(child)
        return child
    
    def rollout(self, board_size):
        """Random simulation until terminal state"""
        current_my = set(self.my_stones)
        current_opp = set(self.opp_stones)
        current_player = self.player
        current_moves = self.legal_moves.copy()
        random.shuffle(current_moves)
        
        while current_moves:
            # Check for immediate wins
            if check_win(current_my, board_size):
                return 0 if self.player == 0 else 1
            if check_win(current_opp, board_size):
                return 1 if self.player == 0 else 0
            
            # Play random move
            move = current_moves.pop()
            if current_player == 0:
                current_my.add(move)
            else:
                current_opp.add(move)
            
            current_player = 1 - current_player
        
        # No moves left, check final state
        if check_win(current_my, board_size):
            return 0 if self.player == 0 else 1
        elif check_win(current_opp, board_size):
            return 1 if self.player == 0 else 0
        else:
            return 0.5  # draw
    
    def update(self, result):
        """Backpropagate result"""
        self.visits += 1
        if result == 0.5:  # draw
            self.wins += 0.5
        elif result == (0 if self.player == 0 else 1):
            self.wins += 1

def check_win(stones, board_size):
    """Check if a set of stones contains a winning structure"""
    stones = set(stones)
    if len(stones) < 6:  # Minimum stones needed for any win
        return False
    
    # Check for bridge (connects two corners)
    corners = [(0, 0), (0, board_size-1), 
               (board_size-1, 0), (board_size-1, board_size-1)]
    stone_corners = [c for c in corners if c in stones]
    
    if len(stone_corners) >= 2:
        # Check connectivity between all pairs of occupied corners
        for i in range(len(stone_corners)):
            for j in range(i+1, len(stone_corners)):
                if connected(stone_corners[i], stone_corners[j], stones):
                    return True
    
    # Check for fork (connects three edges)
    edge_groups = {
        'top': [(0, c) for c in range(1, board_size-1)],
        'bottom': [(board_size-1, c) for c in range(1, board_size-1)],
        'left': [(r, 0) for r in range(1, board_size-1)],
        'right': [(r, board_size-1) for r in range(1, board_size-1)],
        'diag_left': [(r, c) for r in range(1, board_size-1) 
                     for c in range(1, board_size-1) if r == c],
        'diag_right': [(r, c) for r in range(1, board_size-1)
                      for c in range(1, board_size-1) if r + c == board_size-1]
    }
    
    connected_edges = 0
    for edge_name, edge_cells in edge_groups.items():
        edge_stones = [cell for cell in edge_cells if cell in stones]
        if edge_stones:
            # Check if any stone on this edge is connected to others
            for stone in edge_stones:
                if any(connected(stone, other, stones) for other in stones if other != stone):
                    connected_edges += 1
                    break
    
    if connected_edges >= 3:
        return True
    
    # Check for ring (loop)
    return has_ring(stones, board_size)

def connected(a, b, stones):
    """BFS to check if two stones are connected through stone paths"""
    if a not in stones or b not in stones:
        return False
    
    visited = set()
    queue = [a]
    
    while queue:
        current = queue.pop(0)
        if current == b:
            return True
        
        if current in visited:
            continue
        
        visited.add(current)
        r, c = current
        
        for dr, dc in NEIGHBOR_OFFSETS:
            nr, nc = r + dr, c + dc
            neighbor = (nr, nc)
            if neighbor in stones and neighbor not in visited:
                queue.append(neighbor)
    
    return False

def has_ring(stones, board_size):
    """Check for a ring using BFS from empty cells"""
    if len(stones) < 6:
        return False
    
    # Flood fill from each empty cell
    all_cells = {(r, c) for r in range(board_size) for c in range(board_size)}
    empty_cells = all_cells - stones
    visited = set()
    
    for start in empty_cells:
        if start in visited:
            continue
        
        # BFS from this empty cell
        queue = [start]
        component = set()
        touches_boundary = False
        
        while queue:
            cell = queue.pop(0)
            if cell in visited:
                continue
            
            visited.add(cell)
            component.add(cell)
            r, c = cell
            
            # Check if touches board boundary
            if r == 0 or r == board_size-1 or c == 0 or c == board_size-1:
                touches_boundary = True
            
            # Add neighboring empty cells
            for dr, dc in NEIGHBOR_OFFSETS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < board_size and 0 <= nc < board_size:
                    neighbor = (nr, nc)
                    if neighbor in empty_cells and neighbor not in visited:
                        queue.append(neighbor)
        
        # If component doesn't touch boundary, it's surrounded -> ring exists
        if not touches_boundary and len(component) > 0:
            return True
    
    return False
