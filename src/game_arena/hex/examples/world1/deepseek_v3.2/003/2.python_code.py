
import random
import math
import time
from collections import defaultdict, deque
from typing import List, Tuple, Set, Dict

# Precomputed neighbor lookup for 11x11 Hex board
NEIGHBORS = {}
for r in range(11):
    for c in range(11):
        neighbors = []
        # Same row
        if c > 0:
            neighbors.append((r, c-1))
        if c < 10:
            neighbors.append((r, c+1))
        # Top row
        if r > 0:
            neighbors.append((r-1, c))
            if c < 10:
                neighbors.append((r-1, c+1))
        # Bottom row
        if r < 10:
            neighbors.append((r+1, c))
            if c > 0:
                neighbors.append((r+1, c-1))
        NEIGHBORS[(r, c)] = neighbors

class HexBoard:
    def __init__(self, me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str):
        self.size = 11
        self.me = set(me)
        self.opp = set(opp)
        self.color = color
        self.empty = {(r, c) for r in range(11) for c in range(11)} - self.me - self.opp
        
        # Determine goal sides based on color
        if color == 'b':  # Black: connect top (row 0) to bottom (row 10)
            self.my_start = {(0, c) for c in range(11)}
            self.my_end = {(10, c) for c in range(11)}
            self.opp_start = {(r, 0) for r in range(11)}
            self.opp_end = {(r, 10) for r in range(11)}
        else:  # White: connect left (col 0) to right (col 10)
            self.my_start = {(r, 0) for r in range(11)}
            self.my_end = {(r, 10) for r in range(11)}
            self.opp_start = {(0, c) for c in range(11)}
            self.opp_end = {(10, c) for c in range(11)}
    
    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        return NEIGHBORS[pos]
    
    def is_valid_move(self, move: Tuple[int, int]) -> bool:
        return move in self.empty
    
    def make_move(self, move: Tuple[int, int], player: str) -> 'HexBoard':
        """Return new board with move made"""
        if player == 'me':
            new_me = self.me | {move}
            new_opp = self.opp
        else:
            new_me = self.me
            new_opp = self.opp | {move}
        return HexBoard(list(new_me), list(new_opp), self.color)
    
    def connected_to_goal(self, start_set: Set[Tuple[int, int]], 
                         end_set: Set[Tuple[int, int]], 
                         player_stones: Set[Tuple[int, int]]) -> bool:
        """Check if start_set connects to end_set via player_stones"""
        visited = set()
        queue = deque(start_set & player_stones)
        while queue:
            pos = queue.popleft()
            if pos in end_set:
                return True
            if pos in visited:
                continue
            visited.add(pos)
            for nr, nc in self.get_neighbors(pos):
                if (nr, nc) in player_stones and (nr, nc) not in visited:
                    queue.append((nr, nc))
        return False
    
    def game_over(self) -> Tuple[bool, str]:
        """Check if game is over and who won"""
        if self.connected_to_goal(self.my_start, self.my_end, self.me):
            return True, 'me'
        if self.connected_to_goal(self.opp_start, self.opp_end, self.opp):
            return True, 'opp'
        return False, None
    
    def evaluate(self) -> float:
        """Heuristic evaluation: positive is good for me"""
        # Quick win/lose check
        game_over, winner = self.game_over()
        if game_over:
            return 1000 if winner == 'me' else -1000
        
        # Distance to goal heuristic
        my_dist = self.shortest_path_length(self.me, self.my_start, self.my_end)
        opp_dist = self.shortest_path_length(self.opp, self.opp_start, self.opp_end)
        
        # Territory control
        my_influence = self.calculate_influence(self.me)
        opp_influence = self.calculate_influence(self.opp)
        
        score = (opp_dist - my_dist) * 10
        score += (sum(my_influence.values()) - sum(opp_influence.values())) * 0.1
        
        # Bonus for center control
        center = {(5, 5), (5, 6), (6, 5), (6, 6)}
        score += len(center & self.me) * 5
        score -= len(center & self.opp) * 5
        
        return score
    
    def shortest_path_length(self, stones: Set[Tuple[int, int]], 
                            start_set: Set[Tuple[int, int]], 
                            end_set: Set[Tuple[int, int]]) -> float:
        """Dijkstra shortest path through empty cells and own stones"""
        if stones & start_set and stones & end_set:
            # Already connected
            return 0
        
        INF = 1000
        dist = {}
        for r in range(11):
            for c in range(11):
                dist[(r, c)] = INF
        
        # Priority queue simulation
        heap = []
        for pos in start_set:
            if pos in stones:
                dist[pos] = 0
                heap.append((0, pos))
        
        while heap:
            heap.sort()
            d, pos = heap.pop(0)
            if d > dist[pos]:
                continue
            
            for nr, nc in self.get_neighbors(pos):
                nd = d
                if (nr, nc) not in stones:
                    nd += 1  # Empty cell costs 1
                if nd < dist[(nr, nc)]:
                    dist[(nr, nc)] = nd
                    heap.append((nd, (nr, nc)))
        
        min_dist = min(dist[pos] for pos in end_set)
        return min_dist
    
    def calculate_influence(self, stones: Set[Tuple[int, int]]) -> Dict[Tuple[int, int], float]:
        """Calculate influence over empty cells"""
        influence = defaultdict(float)
        for r, c in stones:
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 11 and 0 <= nc < 11:
                        dist = abs(dr) + abs(dc) + abs(dr + dc)
                        if dist <= 3:
                            influence[(nr, nc)] += 1.0 / (dist + 1)
        return influence

class MCTSNode:
    def __init__(self, board: HexBoard, parent=None, move=None):
        self.board = board
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.wins = 0.0
        self.untried_moves = list(board.empty)
        
    def uct_value(self, exploration=1.414) -> float:
        if self.visits == 0:
            return float('inf')
        return (self.wins / self.visits) + exploration * math.sqrt(math.log(self.parent.visits) / self.visits)
    
    def best_child(self) -> 'MCTSNode':
        return max(self.children, key=lambda c: c.uct_value())
    
    def expand(self) -> 'MCTSNode':
        move = self.untried_moves.pop()
        # Alternate players
        next_player = 'opp' if len(self.board.me) + len(self.board.opp) % 2 == 0 else 'me'
        if next_player == 'me':
            next_board = self.board.make_move(move, 'me')
        else:
            next_board = self.board.make_move(move, 'opp')
        child = MCTSNode(next_board, self, move)
        self.children.append(child)
        return child
    
    def simulate(self) -> float:
        """Run a simulation from this node"""
        board = self.board
        current_player = 'me'
        
        # Use heuristic for early termination
        max_plies = 20
        
        for _ in range(max_plies):
            # Check for win
            game_over, winner = board.game_over()
            if game_over:
                return 1.0 if winner == 'me' else 0.0
            
            # Heuristic move selection in simulation
            moves = list(board.empty)
            if not moves:
                break
            
            # Prefer moves that are near existing stones
            if current_player == 'me':
                stones = board.me
                target = board.my_end if any(s in board.my_start for s in board.me) else board.my_start
            else:
                stones = board.opp
                target = board.opp_end if any(s in board.opp_start for s in board.opp) else board.opp_start
            
            # Score moves by distance to target and existing stones
            scored_moves = []
            for move in moves:
                score = 0
                # Distance to target
                min_dist_to_target = min(abs(move[0]-t[0]) + abs(move[1]-t[1]) for t in target)
                score -= min_dist_to_target
                
                # Connection to existing stones
                for stone in stones:
                    dist = abs(move[0]-stone[0]) + abs(move[1]-stone[1])
                    if dist <= 2:
                        score += 3 - dist
                
                scored_moves.append((score, move))
            
            # Choose move with some randomness
            scored_moves.sort(reverse=True)
            top_moves = scored_moves[:max(3, len(scored_moves)//3)]
            _, chosen = random.choice(top_moves)
            
            # Make move
            if current_player == 'me':
                board = board.make_move(chosen, 'me')
                current_player = 'opp'
            else:
                board = board.make_move(chosen, 'opp')
                current_player = 'me'
        
        # If no win found, use evaluation
        return 0.5 + 0.5 * math.tanh(board.evaluate() / 100)

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    # Opening book for first few moves
    if len(me) + len(opp) < 4:
        # Strong opening moves for Hex
        empty_cells = {(r, c) for r in range(11) for c in range(11)} - set(me) - set(opp)
        
        # Prefer center and near-center moves
        center_cells = [(5, 5), (5, 6), (6, 5), (6, 6), 
                       (4, 5), (5, 4), (6, 7), (7, 6)]
        
        for cell in center_cells:
            if cell in empty_cells:
                return cell
        
        # Fallback to any empty cell
        return random.choice(list(empty_cells))
    
    # Main MCTS search
    board = HexBoard(me, opp, color)
    root = MCTSNode(board)
    
    # Time management
    end_time = time.time() + 0.95  # Use 0.95 seconds max
    
    iterations = 0
    while time.time() < end_time and iterations < 10000:
        # Selection
        node = root
        while node.children and not node.untried_moves:
            node = node.best_child()
        
        # Expansion
        if node.untried_moves:
            node = node.expand()
        
        # Simulation
        result = node.simulate()
        
        # Backpropagation
        while node is not None:
            node.visits += 1
            node.wins += result
            node = node.parent
            result = 1.0 - result  # Alternate perspective
        
        iterations += 1
    
    # Choose best move
    if root.children:
        # Select move with most visits
        best_child = max(root.children, key=lambda c: c.visits)
        return best_child.move
    
    # Fallback: choose move with best heuristic
    best_score = -float('inf')
    best_move = None
    for move in board.empty:
        # Quick evaluation
        if color == 'b':
            test_board = board.make_move(move, 'me')
        else:
            test_board = board.make_move(move, 'me')
        score = test_board.evaluate()
        if score > best_score:
            best_score = score
            best_move = move
    
    # If still no move (shouldn't happen), pick random
    if best_move is None:
        empty_cells = list(board.empty)
        return random.choice(empty_cells)
    
    return best_move
