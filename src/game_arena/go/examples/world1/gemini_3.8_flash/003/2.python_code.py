
import time
from typing import List, Tuple, Set, Dict

BOARD_SIZE = 19
PASS_MOVE = (0, 0)

STAR_POINTS = [
    (4, 4), (4, 16), (16, 4), (16, 16),
    (4, 10), (10, 4), (10, 16), (16, 10),
    (10, 10),
    (3, 4), (4, 3), (3, 16), (16, 3), (4, 17), (17, 4), (16, 17), (17, 16),
    (3, 3), (3, 17), (17, 3), (17, 17)
]

def in_bounds(r: int, c: int) -> bool:
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE

def get_neighbors(r: int, c: int) -> List[Tuple[int, int]]:
    neighbors = []
    if r > 1: neighbors.append((r - 1, c))
    if r < BOARD_SIZE: neighbors.append((r + 1, c))
    if c > 1: neighbors.append((r, c - 1))
    if c < BOARD_SIZE: neighbors.append((r, c + 1))
    return neighbors

def get_diagonals(r: int, c: int) -> List[Tuple[int, int]]:
    diag = []
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc):
            diag.append((nr, nc))
    return diag

class BoardState:
    def __init__(self, me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]):
        self.me_set: Set[Tuple[int, int]] = set(me)
        self.opp_set: Set[Tuple[int, int]] = set(opponent)
        self.occupied: Set[Tuple[int, int]] = self.me_set | self.opp_set

        # Chain maps: coord -> chain_id
        self.my_chains: Dict[int, Set[Tuple[int, int]]] = {}
        self.opp_chains: Dict[int, Set[Tuple[int, int]]] = {}
        self.my_chain_liberties: Dict[int, Set[Tuple[int, int]]] = {}
        self.opp_chain_liberties: Dict[int, Set[Tuple[int, int]]] = {}
        self.coord_to_my_chain: Dict[Tuple[int, int], int] = {}
        self.coord_to_opp_chain: Dict[Tuple[int, int], int] = {}

        self._build_chains()

    def _build_chains(self):
        visited = set()
        chain_id = 0
        for stone in self.me_set:
            if stone not in visited:
                chain = set()
                queue = [stone]
                visited.add(stone)
                while queue:
                    curr = queue.pop()
                    chain.add(curr)
                    for n in get_neighbors(*curr):
                        if n in self.me_set and n not in visited:
                            visited.add(n)
                            queue.append(n)
                libs = set()
                for s in chain:
                    for n in get_neighbors(*s):
                        if n not in self.occupied:
                            libs.add(n)
                self.my_chains[chain_id] = chain
                self.my_chain_liberties[chain_id] = libs
                for s in chain:
                    self.coord_to_my_chain[s] = chain_id
                chain_id += 1

        visited.clear()
        chain_id = 0
        for stone in self.opp_set:
            if stone not in visited:
                chain = set()
                queue = [stone]
                visited.add(stone)
                while queue:
                    curr = queue.pop()
                    chain.add(curr)
                    for n in get_neighbors(*curr):
                        if n in self.opp_set and n not in visited:
                            visited.add(n)
                            queue.append(n)
                libs = set()
                for s in chain:
                    for n in get_neighbors(*s):
                        if n not in self.occupied:
                            libs.add(n)
                self.opp_chains[chain_id] = chain
                self.opp_chain_liberties[chain_id] = libs
                for s in chain:
                    self.coord_to_opp_chain[s] = chain_id
                chain_id += 1

    def is_legal(self, move: Tuple[int, int]) -> bool:
        if move in self.occupied or not in_bounds(*move):
            return False

        # Check if move captures any adjacent opponent group
        for n in get_neighbors(*move):
            if n in self.opp_set:
                cid = self.coord_to_opp_chain[n]
                # If that group has exactly 1 liberty, move captures it
                if self.opp_chain_liberties[cid] == {move}:
                    return True

        # Check if move has any empty neighbor
        for n in get_neighbors(*move):
            if n not in self.occupied:
                return True

        # Check if move connects to a friendly chain with > 1 liberties
        for n in get_neighbors(*move):
            if n in self.me_set:
                cid = self.coord_to_my_chain[n]
                if len(self.my_chain_liberties[cid]) > 1:
                    return True

        return False

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    start_time = time.time()
    board = BoardState(me, opponent)
    num_stones = len(me) + len(opponent)

    # 1. Opening Moves
    if num_stones < 8:
        for pt in STAR_POINTS:
            if board.is_legal(pt):
                # Ensure it's not directly in contact with opponent unless necessary
                has_opp = any(n in board.opp_set for n in get_neighbors(*pt))
                if not has_opp:
                    return pt

    # 2. Critical Tactical Moves: Save our stones in atari
    urgent_saves = []
    for cid, libs in board.my_chain_liberties.items():
        if len(libs) == 1:
            save_move = next(iter(libs))
            chain_size = len(board.my_chains[cid])
            if board.is_legal(save_move):
                # Verify if playing at save_move gains > 1 liberty or captures
                gains_liberty = False
                for n in get_neighbors(*save_move):
                    if n not in board.occupied and n != save_move:
                        gains_liberty = True
                        break
                    if n in board.opp_set:
                        opp_cid = board.coord_to_opp_chain[n]
                        if board.opp_chain_liberties[opp_cid] == {save_move}:
                            gains_liberty = True
                            break
                if gains_liberty:
                    urgent_saves.append((chain_size, save_move))

    if urgent_saves:
        urgent_saves.sort(reverse=True, key=lambda x: x[0])
        return urgent_saves[0][1]

    # 3. Critical Tactical Moves: Capture opponent in atari
    captures = []
    for cid, libs in board.opp_chain_liberties.items():
        if len(libs) == 1:
            cap_move = next(iter(libs))
            if board.is_legal(cap_move):
                chain_size = len(board.opp_chains[cid])
                captures.append((chain_size, cap_move))

    if captures:
        captures.sort(reverse=True, key=lambda x: x[0])
        return captures[0][1]

    # 4. Generate Candidate Moves to Score
    candidates: Set[Tuple[int, int]] = set()

    # Stones near existing stones
    for s in board.occupied:
        for n in get_neighbors(*s):
            if n not in board.occupied:
                candidates.add(n)
        for d in get_diagonals(*s):
            if d not in board.occupied:
                candidates.add(d)

    # In early to mid game, also add star/third-line points
    if num_stones < 40:
        for pt in STAR_POINTS:
            if pt not in board.occupied:
                candidates.add(pt)

    if not candidates:
        # Check all empty cells
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                if (r, c) not in board.occupied:
                    candidates.add((r, c))

    best_move = PASS_MOVE
    best_score = -1e9

    for move in candidates:
        if time.time() - start_time > 0.85:
            break

        if not board.is_legal(move):
            continue

        r, c = move
        score = 0.0

        # Line preference (3rd and 4th lines are best for territory/influence)
        dist_edge_r = min(r, 20 - r)
        dist_edge_c = min(c, 20 - c)
        dist_edge = min(dist_edge_r, dist_edge_c)

        if dist_edge == 1:
            score -= 15.0  # 1st line usually endgame only
        elif dist_edge == 2:
            score -= 3.0   # 2nd line low priority in opening
        elif dist_edge in (3, 4):
            score += 8.0   # 3rd / 4th line ideal
        else:
            score += 3.0   # Center influence

        # Evaluate neighbor interactions
        my_neighbor_count = 0
        opp_neighbor_count = 0
        empty_neighbor_count = 0

        for n in get_neighbors(r, c):
            if n in board.me_set:
                my_neighbor_count += 1
                cid = board.coord_to_my_chain[n]
                cur_libs = len(board.my_chain_liberties[cid])
                if cur_libs == 2:
                    score += 12.0  # Helps group in low liberties
            elif n in board.opp_set:
                opp_neighbor_count += 1
                cid = board.coord_to_opp_chain[n]
                cur_libs = len(board.opp_chain_liberties[cid])
                if cur_libs == 2:
                    score += 15.0  # Puts opponent in atari
                elif cur_libs == 3:
                    score += 4.0   # Tightens liberties
            else:
                empty_neighbor_count += 1

        # Reward moves that preserve own liberties
        score += empty_neighbor_count * 3.5

        # Penalize self-atari (playing into a spot with only 1 liberty)
        if empty_neighbor_count == 0 and my_neighbor_count > 0:
            # Check combined liberties after connecting
            connected_libs = set()
            for n in get_neighbors(r, c):
                if n in board.me_set:
                    cid = board.coord_to_my_chain[n]
                    connected_libs |= board.my_chain_liberties[cid]
            connected_libs.discard(move)
            if len(connected_libs) <= 1:
                score -= 30.0  # Suicide / self-atari risk

        # Diagonal support & shapes
        for d in get_diagonals(r, c):
            if d in board.me_set:
                score += 2.0  # Kosumi / diagonal connection
            elif d in board.opp_set:
                score += 1.0  # Peep / clamp pressure

        if score > best_score:
            best_score = score
            best_move = move

    # Fallback to any legal move if best_move is still PASS_MOVE
    if best_move == PASS_MOVE:
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                if board.is_legal((r, c)):
                    return (r, c)

    return best_move
