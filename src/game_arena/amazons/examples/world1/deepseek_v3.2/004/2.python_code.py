
import numpy as np
import random
import math
import time

class MCTSNode:
    def __init__(self, board, player, parent=None, move=None):
        self.board = board.copy()
        self.player = player  # 1 for us, 2 for opponent
        self.parent = parent
        self.move = move  # move that led here: (from, to, arrow)
        self.children = []
        self.visits = 0
        self.wins = 0.0
        self.untried_moves = self._get_legal_moves()

    def _get_legal_moves(self):
        moves = []
        for r in range(6):
            for c in range(6):
                if self.board[r, c] == self.player:
                    moves.extend(self._moves_for_amazon(r, c))
        return moves

    def _moves_for_amazon(self, r, c):
        moves = []
        dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        # Step move
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and self.board[nr, nc] == 0:
                # Shoot arrow from (nr, nc)
                for sdr, sdc in dirs:
                    sr, sc = nr + sdr, nc + sdc
                    while 0 <= sr < 6 and 0 <= sc < 6:
                        if self.board[sr, sc] == 0 or (sr == r and sc == c):
                            # allow arrow to pass through vacated start cell
                            moves.append(((r, c), (nr, nc), (sr, sc)))
                        else:
                            break
                        sr += sdr
                        sc += sdc
                nr += dr
                nc += dc
        return moves

    def is_terminal(self):
        return len(self._get_legal_moves()) == 0

    def best_child(self, c_param=1.414):
        best_score = -float('inf')
        best_child = None
        for child in self.children:
            if child.visits == 0:
                score = float('inf')
            else:
                score = child.wins / child.visits + c_param * math.sqrt(
                    math.log(self.visits) / child.visits
                )
            if score > best_score:
                best_score = score
                best_child = child
        return best_child

    def expand(self):
        if not self.untried_moves:
            return None
        move = self.untried_moves.pop()
        next_board = self._apply_move(self.board, move, self.player)
        next_player = 3 - self.player  # switch player
        child_node = MCTSNode(next_board, next_player, parent=self, move=move)
        self.children.append(child_node)
        return child_node

    def _apply_move(self, board, move, player):
        new_board = board.copy()
        (fr, fc), (tr, tc), (ar, ac) = move
        new_board[fr, fc] = 0
        new_board[tr, tc] = player
        new_board[ar, ac] = -1
        return new_board

    def update(self, result):
        self.visits += 1
        self.wins += result

    def rollout(self):
        # Fast evaluation using mobility difference
        board = self.board.copy()
        player = self.player
        for _ in range(10):  # limited random playout
            moves = self._get_all_moves(board, player)
            if not moves:
                # current player cannot move
                return 1.0 if player != self.player else 0.0  # opponent wins
            move = random.choice(moves)
            board = self._apply_move(board, move, player)
            player = 3 - player
        # evaluate final position
        my_mob = len(self._get_all_moves(board, self.player))
        opp_mob = len(self._get_all_moves(board, 3 - self.player))
        if my_mob == 0 and opp_mob == 0:
            return 0.5
        if my_mob == 0:
            return 0.0
        if opp_mob == 0:
            return 1.0
        # mobility heuristic
        score = 0.5 + 0.1 * (my_mob - opp_mob) / (my_mob + opp_mob + 1)
        # add territory bonus
        my_terr = self._territory(board, self.player)
        opp_terr = self._territory(board, 3 - self.player)
        terr_score = 0.1 * (my_terr - opp_terr) / 36.0
        return min(1.0, max(0.0, score + terr_score))

    def _get_all_moves(self, board, pl):
        moves = []
        for r in range(6):
            for c in range(6):
                if board[r, c] == pl:
                    # reuse move generation logic
                    dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
                    for dr, dc in dirs:
                        nr, nc = r + dr, c + dc
                        while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                            for sdr, sdc in dirs:
                                sr, sc = nr + sdr, nc + sdc
                                while 0 <= sr < 6 and 0 <= sc < 6:
                                    if board[sr, sc] == 0 or (sr == r and sc == c):
                                        moves.append(((r, c), (nr, nc), (sr, sc)))
                                    else:
                                        break
                                    sr += sdr
                                    sc += sdc
                            nr += dr
                            nc += dc
        return moves

    def _territory(self, board, player):
        # BFS from each amazon of player to count reachable empty cells
        visited = set()
        queue = []
        for r in range(6):
            for c in range(6):
                if board[r, c] == player:
                    queue.append((r, c))
                    visited.add((r, c))
        count = 0
        dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        while queue:
            r, c = queue.pop(0)
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 6 and 0 <= nc < 6:
                    if (nr, nc) in visited:
                        break
                    if board[nr, nc] == 0:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
                        count += 1
                    else:
                        break
                    nr += dr
                    nc += dc
        return count


def policy(board):
    start_time = time.time()
    root = MCTSNode(board, player=1)

    # Run MCTS within time limit
    while time.time() - start_time < 0.95:  # leave 50ms margin
        node = root
        # Selection
        while node.children and not node.untried_moves:
            node = node.best_child()

        # Expansion
        if node.untried_moves:
            node = node.expand()

        # Simulation
        result = node.rollout()

        # Backpropagation
        while node is not None:
            node.update(result)
            node = node.parent

    # Choose best move (most visited)
    best_child = max(root.children, key=lambda c: c.visits) if root.children else None
    if best_child is None:
        # fallback: pick first legal move
        legal_moves = root._get_legal_moves()
        if not legal_moves:
            return ""  # should not happen
        move = legal_moves[0]
    else:
        move = best_child.move

    (fr, fc), (tr, tc), (ar, ac) = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
