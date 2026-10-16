
import random
import sys
from typing import List, Tuple, Dict, Set

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    # Ensure memory is properly initialized
    if not memory:
        memory = {
            'phase': 'opening',  # opening, middle, endgame
            'turn_count': 0,
            'last_move': None,
            'strategic_points': [],
            'aggression': 0.5
        }
    
    # Update turn count
    memory['turn_count'] += 1
    
    # Board size (19x19)
    BOARD_SIZE = 19
    
    # Convert to sets for faster operations
    me_set = set(me)
    opp_set = set(opponent)
    all_stones = me_set.union(opp_set)
    
    # Directions for adjacent positions
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # Helper function: Check if position is on board
    def on_board(pos):
        r, c = pos
        return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE
    
    # Helper function: Get adjacent positions
    def get_adjacent(pos):
        r, c = pos
        return [(r + dr, c + dc) for dr, dc in directions if on_board((r + dr, c + dc))]
    
    # Helper function: Count liberties of a group
    def count_liberties(start, stones_set):
        """BFS to find group and count liberties"""
        if start not in stones_set:
            return 0, set()
        
        visited = {start}
        group = {start}
        queue = [start]
        
        while queue:
            pos = queue.pop(0)
            for adj in get_adjacent(pos):
                if adj in stones_set and adj not in visited:
                    visited.add(adj)
                    group.add(adj)
                    queue.append(adj)
        
        liberties = set()
        for pos in group:
            for adj in get_adjacent(pos):
                if adj not in all_stones:
                    liberties.add(adj)
        
        return len(liberties), group
    
    # Helper function: Check if move is legal (not suicide, not on stone)
    def is_legal_move(pos, player_set, opponent_set):
        r, c = pos
        if not on_board(pos):
            return False
        if pos in player_set or pos in opponent_set:
            return False
        
        # Check suicide
        # Temporarily place stone
        test_player = player_set | {pos}
        test_opponent = opponent_set
        test_all = test_player.union(test_opponent)
        
        # Check if our group has liberties after placement
        our_liberties, our_group = count_liberties(pos, test_player)
        
        if our_liberties > 0:
            return True
        
        # If our group has no liberties, check if we capture opponent stones
        for adj in get_adjacent(pos):
            if adj in test_opponent:
                opp_liberties, opp_group = count_liberties(adj, test_opponent)
                if opp_liberties == 0:
                    return True  # Capturing opponent stones makes this legal
        
        return False
    
    # Helper function: Get all legal moves for a player
    def get_all_legal_moves(player_set, opponent_set, exclude=None):
        if exclude is None:
            exclude = set()
        
        candidates = set()
        # Consider positions near existing stones
        for stone in player_set.union(opponent_set):
            for adj in get_adjacent(stone):
                if on_board(adj) and adj not in player_set and adj not in opponent_set and adj not in exclude:
                    candidates.add(adj)
        
        # Also consider some random positions for opening/middle game
        if len(all_stones) < 50:  # Opening phase
            # Try some opening patterns (star points)
            star_points = [(4, 4), (4, 10), (4, 16),
                          (10, 4), (10, 10), (10, 16),
                          (16, 4), (16, 10), (16, 16)]
            for pt in star_points:
                if pt not in candidates and pt not in player_set and pt not in opponent_set:
                    candidates.add(pt)
        
        # Filter legal moves
        legal_moves = []
        for move in candidates:
            if is_legal_move(move, player_set, opponent_set):
                legal_moves.append(move)
        
        return legal_moves
    
    # Helper function: Find captures
    def find_captures(player_set, opponent_set):
        captures = []
        for stone in player_set:
            for adj in get_adjacent(stone):
                if adj in opponent_set:
                    opp_liberties, opp_group = count_liberties(adj, opponent_set)
                    if opp_liberties == 1:
                        # Can capture this group by playing at its last liberty
                        # Find the liberty
                        for adj2 in get_adjacent(adj):
                            if adj2 not in all_stones and is_legal_move(adj2, player_set, opponent_set):
                                captures.append((adj2, opp_group))
        return captures
    
    # Helper function: Find atari
    def find_atari(player_set, opponent_set):
        atari_moves = []
        for stone in player_set:
            for adj in get_adjacent(stone):
                if adj not in all_stones and is_legal_move(adj, player_set, opponent_set):
                    # Temporarily place stone
                    test_player = player_set | {adj}
                    # Check opponent groups adjacent
                    for opp_adj in get_adjacent(adj):
                        if opp_adj in opponent_set:
                            opp_liberties, opp_group = count_liberties(opp_adj, opponent_set)
                            if opp_liberties == 1:
                                atari_moves.append((adj, opp_group))
        return atari_moves
    
    # Helper function: Score a move
    def score_move(move, player_set, opponent_set, memory):
        score = 0
        
        # 1. Capture opportunity (highest priority)
        captures = find_captures(player_set | {move}, opponent_set)
        if captures:
            score += 50 + sum(len(group) for _, group in captures) * 10
        
        # 2. Save own stones (if in atari)
        liberties, group = count_liberties(move, player_set | {move})
        if liberties == 1:
            score += 40
        
        # 3. Reduce opponent's liberties (atari)
        ataris = find_atari(player_set | {move}, opponent_set)
        if ataris:
            score += 30 + sum(len(group) for _, group in ataris) * 5
        
        # 4. Territory value based on position
        r, c = move
        # Center is more valuable
        center_dist = abs(r - 10) + abs(c - 10)
        score += max(0, 10 - center_dist // 2)
        
        # 5. Connection value (don't play isolated)
        connection_score = 0
        for adj in get_adjacent(move):
            if adj in player_set:
                connection_score += 2
            elif adj in opponent_set:
                connection_score -= 1
        score += connection_score
        
        # 6. Safety check: avoid moves that make groups too weak
        test_player = player_set | {move}
        for adj in get_adjacent(move):
            if adj in test_player:
                test_liberties, test_group = count_liberties(adj, test_player)
                if test_liberties == 1:
                    score -= 15  # Punish creating atari on own group
        
        return score
    
    # Update game phase based on stone count
    total_stones = len(all_stones)
    if total_stones < 40:
        memory['phase'] = 'opening'
    elif total_stones < 120:
        memory['phase'] = 'middle'
        memory['aggression'] = 0.7
    else:
        memory['phase'] = 'endgame'
        memory['aggression'] = 0.4
    
    # Special case: empty board (first move)
    if total_stones == 0:
        # Play at a star point (e.g., 4,4)
        memory['last_move'] = (4, 4)
        return (4, 4), memory
    
    # Generate legal moves
    legal_moves = get_all_legal_moves(me_set, opp_set)
    
    if not legal_moves:
        # Pass if no legal moves
        return (0, 0), memory
    
    # If we have captures, prioritize them
    captures = find_captures(me_set, opp_set)
    if captures:
        # Choose capture that captures most stones
        best_capture = max(captures, key=lambda x: len(x[1]))
        return best_capture[0], memory
    
    # Score all moves
    scored_moves = []
    for move in legal_moves:
        score = score_move(move, me_set, opp_set, memory)
        # Add some randomness for variety
        score += random.uniform(-2, 2)
        scored_moves.append((move, score))
    
    # Sort by score
    scored_moves.sort(key=lambda x: x[1], reverse=True)
    
    # Choose top move
    best_move = scored_moves[0][0]
    
    # For middle/endgame, sometimes play pass if no good moves
    if memory['phase'] in ['middle', 'endgame'] and scored_moves[0][1] < 10:
        if random.random() < 0.1:  # 10% chance to pass in endgame if weak moves
            return (0, 0), memory
    
    memory['last_move'] = best_move
    return best_move, memory
