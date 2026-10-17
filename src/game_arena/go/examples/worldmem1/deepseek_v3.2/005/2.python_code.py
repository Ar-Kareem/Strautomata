
import math
import random
from collections import defaultdict
import time

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    MCTS-based Go policy with pattern knowledge and tactical awareness.
    """
    # Initialize memory if first call
    if not memory:
        memory = {
            'move_count': 0,
            'ko_position': None,
            'last_opponent_move': None,
            'opening_moves': [],
            'transposition_table': {}
        }
    
    memory['move_count'] += 1
    move_num = memory['move_count']
    
    # Create board representation
    board_size = 19
    board = [[0] * (board_size + 2) for _ in range(board_size + 2)]  # 1-indexed with border
    my_stones = set(me)
    opp_stones = set(opponent)
    
    for r, c in my_stones:
        board[r][c] = 1
    for r, c in opp_stones:
        board[r][c] = -1
    
    # Add border
    for i in range(board_size + 2):
        board[i][0] = board[i][board_size + 1] = 2
        board[0][i] = board[board_size + 1][i] = 2
    
    # Check for urgent moves (save endangered groups)
    urgent_move = find_urgent_move(board, my_stones, opp_stones, memory.get('ko_position'))
    if urgent_move and urgent_move != (0, 0):
        memory['last_move'] = urgent_move
        return urgent_move, memory
    
    # Opening book for first ~40 moves
    if move_num <= 40:
        opening_move = get_opening_move(board, move_num, memory)
        if opening_move:
            memory['last_move'] = opening_move
            memory['opening_moves'].append(opening_move)
            return opening_move, memory
    
    # Run MCTS
    best_move = mcts_search(board, my_stones, opp_stones, memory)
    
    if best_move == (0, 0) or not is_legal_move(best_move[0], best_move[1], board, my_stones, opp_stones, memory.get('ko_position')):
        # Fallback to first legal move
        for r in range(1, 20):
            for c in range(1, 20):
                if is_legal_move(r, c, board, my_stones, opp_stones, memory.get('ko_position')):
                    best_move = (r, c)
                    break
            if best_move != (0, 0):
                break
    
    # Update ko memory
    if best_move != (0, 0):
        new_board = [row[:] for row in board]
        new_board[best_move[0]][best_move[1]] = 1
        captures = get_captures(new_board, best_move[0], best_move[1], -1)
        if len(captures) == 1 and len(get_liberties(new_board, captures[0][0], captures[0][1])) == 1:
            memory['ko_position'] = captures[0]
        else:
            memory['ko_position'] = None
    
    memory['last_move'] = best_move
    memory['last_opponent_move'] = opponent[-1] if opponent else None
    
    return best_move, memory


def mcts_search(board, my_stones, opp_stones, memory, time_limit=0.95):
    """Monte Carlo Tree Search with pattern-based rollouts."""
    start_time = time.time()
    root_node = MCTSNode(board, my_stones, opp_stones, player=1, 
                         ko_pos=memory.get('ko_position'), parent=None)
    
    # Progressive widening - expand more promising moves first
    move_candidates = get_move_candidates(board, my_stones, opp_stones, 
                                         memory.get('ko_position'), width=15)
    
    # Early return if only one candidate
    if len(move_candidates) == 1:
        return move_candidates[0]
    
    # Run simulations until time limit
    sim_count = 0
    while time.time() - start_time < time_limit:
        node = root_node
        
        # Selection
        while node.children and not node.terminal:
            node = node.select_child()
        
        # Expansion
        if not node.terminal:
            node.expand(move_candidates)
            if node.children:
                node = random.choice(node.children)
        
        # Simulation
        result = node.simulate()
        
        # Backpropagation
        while node:
            node.update(result)
            node = node.parent
        
        sim_count += 1
    
    # Choose best move
    if not root_node.children:
        return (0, 0)  # Pass if no moves
    
    # Find child with most visits
    best_child = max(root_node.children, key=lambda c: c.visits)
    return best_child.move


class MCTSNode:
    """MCTS node for Go game state."""
    def __init__(self, board, my_stones, opp_stones, player, ko_pos, parent, move=None):
        self.board = board
        self.my_stones = set(my_stones)
        self.opp_stones = set(opp_stones)
        self.player = player  # 1 for me, -1 for opponent
        self.ko_pos = ko_pos
        self.parent = parent
        self.move = move
        
        self.children = []
        self.visits = 0
        self.wins = 0
        self.terminal = self.check_terminal()
        
        # Legal moves cache
        self._legal_moves = None
    
    def check_terminal(self):
        """Check if game should end (simplified)."""
        # In MCTS simulations, end after reasonable length
        total_stones = len(self.my_stones) + len(self.opp_stones)
        return total_stones > 250  # Cap simulation length
    
    def get_legal_moves(self):
        """Get all legal moves for current player."""
        if self._legal_moves is not None:
            return self._legal_moves
        
        moves = []
        stones = self.my_stones if self.player == 1 else self.opp_stones
        opponent_stones = self.opp_stones if self.player == 1 else self.my_stones
        
        # Check all intersections
        for r in range(1, 20):
            for c in range(1, 20):
                if self.board[r][c] == 0:  # Empty
                    # Check basic legality
                    if (r, c) == self.ko_pos:
                        continue
                    
                    # Make move temporarily
                    new_board = [row[:] for row in self.board]
                    new_board[r][c] = self.player
                    
                    # Check for captures
                    captures = []
                    for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        nr, nc = r + dr, c + dc
                        if 1 <= nr <= 19 and 1 <= nc <= 19:
                            if new_board[nr][nc] == -self.player:
                                libs = get_liberties(new_board, nr, nc)
                                if len(libs) == 0:
                                    captures.extend(libs)
                    
                    # Suicide rule
                    if not captures:
                        libs = get_liberties(new_board, r, c)
                        if len(libs) == 0:
                            continue
                    
                    moves.append((r, c))
        
        # Add pass move
        moves.append((0, 0))
        self._legal_moves = moves
        return moves
    
    def select_child(self):
        """UCT selection."""
        exploration = 1.414  # sqrt(2)
        
        def uct_score(child):
            if child.visits == 0:
                return float('inf')
            exploitation = child.wins / child.visits
            exploration_term = exploration * math.sqrt(math.log(self.visits) / child.visits)
            return exploitation + exploration_term
        
        return max(self.children, key=uct_score)
    
    def expand(self, move_candidates):
        """Expand node with promising moves."""
        legal_moves = self.get_legal_moves()
        
        # Prioritize move candidates
        for move in move_candidates:
            if move in legal_moves:
                child = self.make_child(move)
                if child:
                    self.children.append(child)
        
        # Add a few random moves
        random_moves = [m for m in legal_moves if m not in move_candidates and m != (0, 0)]
        if random_moves:
            move = random.choice(random_moves[:5])  # Limit random expansion
            child = self.make_child(move)
            if child:
                self.children.append(child)
    
    def make_child(self, move):
        """Create child node after making a move."""
        if move == (0, 0):  # Pass
            return MCTSNode(
                self.board,
                self.my_stones,
                self.opp_stones,
                -self.player,
                None,  # Ko resets on pass
                self,
                move
            )
        
        r, c = move
        new_board = [row[:] for row in self.board]
        new_board[r][c] = self.player
        
        # Update stone sets
        if self.player == 1:
            new_my_stones = self.my_stones | {(r, c)}
            new_opp_stones = self.opp_stones.copy()
        else:
            new_my_stones = self.my_stones.copy()
            new_opp_stones = self.opp_stones | {(r, c)}
        
        # Remove captured stones
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if new_board[nr][nc] == -self.player:
                    if len(get_liberties(new_board, nr, nc)) == 0:
                        # Capture group
                        captured = get_group(new_board, nr, nc)
                        for cr, cc in captured:
                            new_board[cr][cc] = 0
                            if self.player == 1:
                                new_opp_stones.discard((cr, cc))
                            else:
                                new_my_stones.discard((cr, cc))
        
        # Check for ko
        ko_pos = None
        captures = get_captures(new_board, r, c, -self.player)
        if len(captures) == 1 and len(get_liberties(new_board, captures[0][0], captures[0][1])) == 1:
            ko_pos = captures[0]
        
        return MCTSNode(
            new_board,
            new_my_stones if self.player == 1 else new_opp_stones,
            new_opp_stones if self.player == 1 else new_my_stones,
            -self.player,
            ko_pos,
            self,
            move
        )
    
    def simulate(self):
        """Pattern-based rollout simulation."""
        board = [row[:] for row in self.board]
        my_stones = self.my_stones.copy()
        opp_stones = self.opp_stones.copy()
        player = self.player
        ko_pos = self.ko_pos
        
        # Pattern-based simulation
        for _ in range(60):  # Limited simulation depth
            # Get moves with pattern heuristics
            moves = get_pattern_moves(board, my_stones if player == 1 else opp_stones,
                                     opp_stones if player == 1 else my_stones, player, ko_pos)
            
            if not moves:
                player = -player
                ko_pos = None
                continue
            
            move = random.choice(moves[:3])  # Choose from top patterns
            
            if move == (0, 0):  # Pass
                player = -player
                ko_pos = None
                continue
            
            r, c = move
            board[r][c] = player
            
            if player == 1:
                my_stones.add((r, c))
            else:
                opp_stones.add((r, c))
            
            # Capture stones
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19:
                    if board[nr][nc] == -player:
                        if len(get_liberties(board, nr, nc)) == 0:
                            captured = get_group(board, nr, nc)
                            for cr, cc in captured:
                                board[cr][cc] = 0
                                if player == 1:
                                    opp_stones.discard((cr, cc))
                                else:
                                    my_stones.discard((cr, cc))
            
            # Update ko
            ko_pos = None
            captures = get_captures(board, r, c, -player)
            if len(captures) == 1 and len(get_liberties(board, captures[0][0], captures[0][1])) == 1:
                ko_pos = captures[0]
            
            player = -player
        
        # Evaluate final position
        return evaluate_position(board, self.my_stones, self.opp_stones)
    
    def update(self, result):
        """Update node statistics."""
        self.visits += 1
        if result > 0:  # Win for original player (me)
            self.wins += 1


def get_liberties(board, r, c):
    """Get liberties of a stone group starting at (r, c)."""
    color = board[r][c]
    if color == 0:
        return []
    
    visited = set()
    liberties = set()
    stack = [(r, c)]
    
    while stack:
        cr, cc = stack.pop()
        if (cr, cc) in visited:
            continue
        visited.add((cr, cc))
        
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = cr + dr, cc + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if board[nr][nc] == 0:
                    liberties.add((nr, nc))
                elif board[nr][nc] == color and (nr, nc) not in visited:
                    stack.append((nr, nc))
    
    return list(liberties)


def get_group(board, r, c):
    """Get all stones in the group containing (r, c)."""
    color = board[r][c]
    if color == 0:
        return []
    
    group = []
    visited = set()
    stack = [(r, c)]
    
    while stack:
        cr, cc = stack.pop()
        if (cr, cc) in visited:
            continue
        visited.add((cr, cc))
        group.append((cr, cc))
        
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = cr + dr, cc + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if board[nr][nc] == color and (nr, nc) not in visited:
                    stack.append((nr, nc))
    
    return group


def get_captures(board, r, c, color):
    """Get stones that would be captured by playing at (r, c) against color."""
    captures = []
    for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        nr, nc = r + dr, c + dc
        if 1 <= nr <= 19 and 1 <= nc <= 19:
            if board[nr][nc] == color:
                if len(get_liberties(board, nr, nc)) == 0:
                    captures.append((nr, nc))
    return captures


def is_legal_move(r, c, board, my_stones, opp_stones, ko_pos):
    """Check if move is legal."""
    if r == 0 and c == 0:  # Pass is always legal
        return True
    
    if not (1 <= r <= 19 and 1 <= c <= 19):
        return False
    
    if board[r][c] != 0:
        return False
    
    if (r, c) == ko_pos:
        return False
    
    # Check suicide rule
    new_board = [row[:] for row in board]
    new_board[r][c] = 1
    
    # Check for captures
    captures = get_captures(new_board, r, c, -1)
    if captures:
        return True
    
    # Check if move has liberties
    libs = get_liberties(new_board, r, c)
    return len(libs) > 0


def find_urgent_move(board, my_stones, opp_stones, ko_pos):
    """Find urgent moves to save groups or attack opponent."""
    # Check if any of my groups are in atari
    for r, c in my_stones:
        libs = get_liberties(board, r, c)
        if len(libs) == 1:
            # Save the group by extending or capturing
            lib = libs[0]
            if is_legal_move(lib[0], lib[1], board, my_stones, opp_stones, ko_pos):
                return lib
    
    # Check if any opponent groups are in atari
    for r, c in opp_stones:
        libs = get_liberties(board, r, c)
        if len(libs) == 1:
            # Try to capture
            lib = libs[0]
            if is_legal_move(lib[0], lib[1], board, my_stones, opp_stones, ko_pos):
                return lib
    
    # Look for cutting points
    for r in range(1, 20):
        for c in range(1, 20):
            if board[r][c] == 0:
                # Check if this is a cutting point between opponent groups
                opponent_neighbors = 0
                for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= 19 and 1 <= nc <= 19:
                        if board[nr][nc] == -1:
                            opponent_neighbors += 1
                
                if opponent_neighbors >= 2:
                    if is_legal_move(r, c, board, my_stones, opp_stones, ko_pos):
                        return (r, c)
    
    return None


def get_opening_move(board, move_num, memory):
    """Opening book for standard fuseki."""
    opening_moves = memory.get('opening_moves', [])
    
    # Common opening moves on 19x19
    standard_moves = [
        (4, 4), (4, 16), (16, 4), (16, 16),  # Star points
        (4, 10), (10, 4), (10, 16), (16, 10),  # 3-4 points
        (10, 10),  # Tengen
        (4, 7), (4, 13), (7, 4), (7, 16), (13, 4), (13, 16), (16, 7), (16, 13),
        (7, 7), (7, 13), (13, 7), (13, 13)
    ]
    
    # Filter out occupied positions
    available = []
    for move in standard_moves:
        r, c = move
        if board[r][c] == 0:
            available.append(move)
    
    if not available:
        return None
    
    # Choose based on move number and existing stones
    if move_num == 1:
        return random.choice([(4, 4), (4, 16), (16, 4), (16, 16)])
    elif move_num == 2:
        # Respond to opponent's first move
        if memory.get('last_opponent_move'):
            or_, oc = memory['last_opponent_move']
            # Play opposite side
            if or_ <= 10:
                return random.choice([m for m in available if m[0] >= 10])
            else:
                return random.choice([m for m in available if m[0] <= 10])
    
    # For later opening moves, choose unoccupied standard point
    return available[0] if available else None


def get_move_candidates(board, my_stones, opp_stones, ko_pos, width=20):
    """Get promising move candidates for MCTS expansion."""
    candidates = []
    
    # 1. Extend from existing stones
    for r, c in my_stones:
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if board[nr][nc] == 0 and (nr, nc) != ko_pos:
                    candidates.append((nr, nc))
    
    # 2. Urgent moves (saving/attacking)
    urgent = find_urgent_move(board, my_stones, opp_stones, ko_pos)
    if urgent and urgent not in candidates:
        candidates.append(urgent)
    
    # 3. Empty intersections near opponent stones
    for r, c in opp_stones:
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if board[nr][nc] == 0 and (nr, nc) != ko_pos:
                    candidates.append((nr, nc))
    
    # 4. Center and key points if board is empty
    if len(my_stones) + len(opp_stones) < 10:
        center_points = [(10, 10), (10, 9), (9, 10), (11, 10), (10, 11)]
        candidates.extend([p for p in center_points if board[p[0]][p[1]] == 0])
    
    # Remove duplicates and check legality
    unique_candidates = []
    for move in candidates:
        if move not in unique_candidates and is_legal_move(move[0], move[1], board, my_stones, opp_stones, ko_pos):
            unique_candidates.append(move)
    
    # Add pass as last resort
    unique_candidates.append((0, 0))
    
    return unique_candidates[:width]


def get_pattern_moves(board, my_stones, opp_stones, player, ko_pos):
    """Get moves based on tactical patterns for rollouts."""
    moves = []
    
    # Pattern: save group in atari
    stones = my_stones if player == 1 else opp_stones
    for r, c in stones:
        libs = get_liberties(board, r, c)
        if len(libs) == 1:
            move = libs[0]
            if is_legal_move(move[0], move[1], board, 
                           my_stones if player == 1 else opp_stones,
                           opp_stones if player == 1 else my_stones,
                           ko_pos):
                moves.append(move)
    
    # Pattern: capture opponent group
    opponent_stones = opp_stones if player == 1 else my_stones
    for r, c in opponent_stones:
        libs = get_liberties(board, r, c)
        if len(libs) == 1:
            move = libs[0]
            if is_legal_move(move[0], move[1], board,
                           my_stones if player == 1 else opp_stones,
                           opp_stones if player == 1 else my_stones,
                           ko_pos):
                moves.append(move)
    
    # Pattern: extend from existing stones
    for r, c in stones:
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if board[nr][nc] == 0 and (nr, nc) != ko_pos:
                    if is_legal_move(nr, nc, board,
                                   my_stones if player == 1 else opp_stones,
                                   opp_stones if player == 1 else my_stones,
                                   ko_pos):
                        moves.append((nr, nc))
    
    # Add some random moves
    for _ in range(3):
        r, c = random.randint(1, 19), random.randint(1, 19)
        if board[r][c] == 0 and (r, c) != ko_pos:
            if is_legal_move(r, c, board,
                           my_stones if player == 1 else opp_stones,
                           opp_stones if player == 1 else my_stones,
                           ko_pos):
                moves.append((r, c))
    
    # Add pass
    moves.append((0, 0))
    
    # Remove duplicates
    return list(dict.fromkeys(moves))


def evaluate_position(board, my_stones, opp_stones):
    """Simple evaluation based on territory and influence."""
    # Count stones (simplified)
    my_count = len(my_stones)
    opp_count = len(opp_stones)
    
    # Add influence for center stones
    center_bonus = 0
    for r, c in my_stones:
        distance_from_center = abs(r - 10) + abs(c - 10)
        if distance_from_center < 5:
            center_bonus += 0.5
    
    score = (my_count - opp_count) + center_bonus
    
    # Normalize to [-1, 1] range
    return math.tanh(score / 100)


# Start of execution
if __name__ == "__main__":
    # Test with empty board
    test_me = []
    test_opponent = []
    test_memory = {}
    
    move, new_memory = policy(test_me, test_opponent, test_memory)
    print(f"First move: {move}")
