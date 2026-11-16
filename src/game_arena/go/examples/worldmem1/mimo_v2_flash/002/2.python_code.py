
import numpy as np
import random
import time
from typing import List, Tuple, Dict

# Constants
BOARD_SIZE = 19
EMPTY = 0
ME = 1
OPPONENT = 2
KOMI = 0.5  # Standard Komi if needed, though score isn't calculated here

class GoState:
    def __init__(self, board=None, me_stones=None, opp_stones=None, last_move=None, prev_board=None):
        if board is None:
            self.board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int8)
            self.me = set()
            self.opp = set()
        else:
            self.board = board.copy()
            self.me = set(me_stones)
            self.opp = set(opp_stones)
        self.last_move = last_move
        self.prev_board = prev_board

    def copy(self):
        return GoState(self.board, list(self.me), list(self.opp), self.last_move, self.prev_board)

    def get_neighbors(self, r, c):
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                neighbors.append((nr, nc))
        return neighbors

    def get_group_liberties(self, r, c, player):
        color = ME if player == 'me' else OPPONENT
        if self.board[r, c] != color:
            return set(), set()

        group = set()
        liberties = set()
        queue = [(r, c)]
        group.add((r, c))

        while queue:
            curr_r, curr_c = queue.pop(0)
            for nr, nc in self.get_neighbors(curr_r, curr_c):
                val = self.board[nr, nc]
                if val == EMPTY:
                    liberties.add((nr, nc))
                elif val == color and (nr, nc) not in group:
                    group.add((nr, nc))
                    queue.append((nr, nc))
        
        return group, liberties

    def place_stone(self, r, c, player):
        color = ME if player == 'me' else OPPONENT
        if self.board[r, c] != EMPTY:
            return False
        
        # Save state for Ko check
        old_board = self.board.copy()

        # Temporarily place stone
        self.board[r, c] = color
        if player == 'me':
            self.me.add((r, c))
        else:
            self.opp.add((r, c))

        # Check captures
        opponent = OPPONENT if player == 'me' else ME
        opponent_stones = self.opp if player == 'me' else self.me
        captured = []
        
        # Check neighbors of placed stone for capture
        for nr, nc in self.get_neighbors(r, c):
            if self.board[nr, nc] == opponent:
                group, liberties = self.get_group_liberties(nr, nc, 'opp' if player == 'me' else 'me')
                if len(liberties) == 0:
                    captured.extend(list(group))
        
        # Remove captured stones
        for cr, cc in captured:
            self.board[cr, cc] = EMPTY
            opponent_stones.remove((cr, cc))

        # Suicide check
        _, liberties = self.get_group_liberties(r, c, 'me' if player == 'me' else 'opp')
        if len(liberties) == 0:
            # Revert
            self.board = old_board
            if player == 'me': self.me.discard((r, c))
            else: self.opp.discard((r, c))
            return False

        # Ko check
        if self.prev_board is not None:
            if np.array_equal(self.board, self.prev_board):
                # Revert
                self.board = old_board
                if player == 'me': self.me.discard((r, c))
                else: self.opp.discard((r, c))
                return False

        return True

    def get_legal_moves(self, player):
        moves = []
        # Heuristic: Prioritize captures and liberties
        # To save time on 19x19, we scan neighbors of existing stones + random exploration
        candidate_set = set()
        
        stones = self.me if player == 'me' else self.opp
        opponent_stones = self.opp if player == 'me' else self.me
        
        # 1. Moves adjacent to existing stones
        for r, c in stones:
            for nr, nc in self.get_neighbors(r, c):
                if self.board[nr, nc] == EMPTY:
                    candidate_set.add((nr, nc))
        
        # 2. Capturing moves (Check if placing a stone here captures opponent)
        # This is covered by candidate_set mostly, but we want to prioritize them
        
        # 3. Expansion: Add random empty spots if candidates are few
        if len(candidate_set) < 20:
            empties = np.argwhere(self.board == EMPTY)
            for er, ec in empties:
                candidate_set.add((tuple((er, ec))))
                if len(candidate_set) > 50: break
        
        valid_moves = []
        for r, c in candidate_set:
            if self.is_move_safe(r, c, player):
                valid_moves.append((r, c))
        
        return valid_moves

    def is_move_safe(self, r, c, player):
        # Quick check without full state modification
        color = ME if player == 'me' else OPPONENT
        if self.board[r, c] != EMPTY:
            return False
        
        # Simulate
        temp_board = self.board.copy()
        temp_board[r, c] = color
        
        # Check if any opponent groups died
        opponent = OPPONENT if player == 'me' else ME
        captured = False
        for nr, nc in self.get_neighbors(r, c):
            if temp_board[nr, nc] == opponent:
                if self.count_liberties_quick(nr, nc, opponent, temp_board) == 0:
                    captured = True
        
        # If not captured, check if own group lives
        if not captured:
            if self.count_liberties_quick(r, c, color, temp_board) == 0:
                return False # Suicide
        
        # Ko check
        if self.prev_board is not None:
            if np.array_equal(temp_board, self.prev_board):
                return False
        
        return True

    def count_liberties_quick(self, r, c, color, board_arr):
        group = set()
        queue = [(r, c)]
        group.add((r, c))
        liberties = 0
        
        while queue:
            curr_r, curr_c = queue.pop(0)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = curr_r + dr, curr_c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if board_arr[nr, nc] == EMPTY:
                        liberties += 1
                    elif board_arr[nr, nc] == color and (nr, nc) not in group:
                        group.add((nr, nc))
                        queue.append((nr, nc))
        return liberties

    def is_game_over(self):
        # Simple heuristic: Pass if both players pass or board full
        # Here we just check if board is mostly full or no legal moves
        if len(np.nonzero(self.board)[0]) > 300:
            return True
        return False

# MCTS Node
class Node:
    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_moves = state.get_legal_moves('me')

    def uct_select_child(self, exploration=1.41):
        # UCB1
        best_score = -float('inf')
        best_child = None
        
        for child in self.children:
            if child.visits == 0:
                uct_score = float('inf')
            else:
                exploit = child.wins / child.visits
                explore = exploration * np.sqrt(np.log(self.visits) / child.visits)
                uct_score = exploit + explore
            
            if uct_score > best_score:
                best_score = uct_score
                best_child = child
        
        return best_child

    def add_child(self, move, state):
        node = Node(state, self, move)
        self.untried_moves.remove(move)
        self.children.append(node)
        return node

    def update(self, result):
        self.visits += 1
        self.wins += result

# Main Policy
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    start_time = time.time()
    
    # Reconstruct state
    board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int8)
    me_set = set()
    opp_set = set()
    
    for r, c in me:
        board[r-1, c-1] = ME
        me_set.add((r-1, c-1))
        
    for r, c in opponent:
        board[r-1, c-1] = OPPONENT
        opp_set.add((r-1, c-1))
        
    prev_board = memory.get('prev_board')
    current_state = GoState(board, list(me_set), list(opp_set), prev_board=prev_board)
    
    # 1. Check for immediate captures or defense
    # Fast heuristic check before MCTS
    legal_moves = current_state.get_legal_moves('me')
    
    if not legal_moves:
        # Pass
        memory['prev_board'] = board
        return (0, 0), memory
    
    # Sort moves by immediate gain (captures)
    # This helps MCTS focus on good branches early
    moves_with_value = []
    for move in legal_moves:
        score = 0
        # Check capture potential
        temp_state = current_state.copy()
        temp_state.place_stone(move[0], move[1], 'me')
        # Simple metric: difference in stone count
        diff = len(temp_state.me) - len(temp_state.opp) - (len(current_state.me) - len(current_state.opp))
        moves_with_value.append((diff, move))
    
    moves_with_value.sort(reverse=True)
    
    # 2. Run MCTS for the remaining time (approx 0.8s)
    root = Node(current_state)
    
    # Pre-populate root children with sorted moves to prioritize
    for _, move in moves_with_value:
        if move in root.untried_moves:
            child_state = root.state.copy()
            success = child_state.place_stone(move[0], move[1], 'me')
            if success:
                root.add_child(move, child_state)
    
    simulations = 0
    while time.time() - start_time < 0.8:
        simulations += 1
        node = root
        
        # Selection
        while node.children and not node.untried_moves:
            node = node.uct_select_child()
        
        # Expansion
        if node.untried_moves:
            move = random.choice(node.untried_moves)
            child_state = node.state.copy()
            if child_state.place_stone(move[0], move[1], 'me'):
                node = node.add_child(move, child_state)
        
        # Simulation (Rollout)
        # Play random moves for both players
        temp_state = node.state.copy()
        current_player = 'opp' # Next to move in the child node is opponent
        
        # Limited depth simulation
        for _ in range(30): # Reduced depth for speed
            moves = temp_state.get_legal_moves(current_player)
            if not moves:
                break
            move = random.choice(moves)
            if current_player == 'me':
                temp_state.place_stone(move[0], move[1], 'me')
            else:
                temp_state.place_stone(move[0], move[1], 'opp')
            current_player = 'opp' if current_player == 'me' else 'me'
        
        # Result (Win/Loss estimation)
        # Heuristic: More stones is better
        my_stones = len(temp_state.me)
        opp_stones = len(temp_state.opp)
        
        # Add Komi for stability
        result = 1 if (my_stones + 0.5) > opp_stones else 0
        
        # Backpropagation
        while node:
            node.update(result)
            node = node.parent
            result = 1 - result # Switch perspective
            
    # Selection of best move
    best_move = (0, 0)
    max_visits = -1
    
    # If root has children
    if root.children:
        for child in root.children:
            if child.visits > max_visits:
                max_visits = child.visits
                best_move = child.move
    
    # Fallback: if no simulations ran or best move is weird, pick top heuristic
    if max_visits == -1 and moves_with_value:
        best_move = moves_with_value[0][1]
    
    # Pass condition: If best move win rate is low (< 30%)
    # Find the corresponding child for the best move
    best_child = None
    for child in root.children:
        if child.move == best_move:
            best_child = child
            break
            
    if best_child and best_child.wins / best_child.visits < 0.3:
        best_move = (0, 0)

    # Update Memory for Ko check
    # We need to store the board state AFTER our move to prevent immediate ko recapture
    if best_move != (0, 0):
        new_board = board.copy()
        new_board[best_move[0], best_move[1]] = ME
        memory['prev_board'] = new_board
    else:
        memory['prev_board'] = board

    # Convert back to 1-based indexing
    if best_move == (0, 0):
        final_action = (0, 0)
    else:
        final_action = (best_move[0] + 1, best_move[1] + 1)
        
    return final_action, memory
