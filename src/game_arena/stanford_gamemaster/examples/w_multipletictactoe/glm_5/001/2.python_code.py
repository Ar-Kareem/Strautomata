
def policy(state: list[list[object]], role: str) -> str:
    cells = {}
    for prop in state:
        if prop[0] == "cell":
            cells[(prop[1], prop[2], prop[3], prop[4])] = prop[5]
    
    my_mark = role
    opp_mark = "o" if my_mark == "x" else "x"
    
    lines = [
        [("1","1"), ("1","2"), ("1","3")], [("2","1"), ("2","2"), ("2","3")], [("3","1"), ("3","2"), ("3","3")],
        [("1","1"), ("2","1"), ("3","1")], [("1","2"), ("2","2"), ("3","2")], [("1","3"), ("2","3"), ("3","3")],
        [("1","1"), ("2","2"), ("3","3")], [("1","3"), ("2","2"), ("3","1")]
    ]
    
    def get_cell(bm, bn, ci, cj):
        return cells.get((bm, bn, ci, cj), "b")
    
    def is_blank(bm, bn, ci, cj):
        return get_cell(bm, bn, ci, cj) == "b"
    
    def find_winning_moves(bm, bn, mark):
        moves = []
        for line in lines:
            count, blank = 0, None
            for ci, cj in line:
                cell = get_cell(bm, bn, ci, cj)
                if cell == mark: count += 1
                elif cell == "b": blank = (ci, cj)
            if count == 2 and blank: moves.append(blank)
        return moves
    
    def find_forks(bm, bn, mark):
        forks = []
        for ci in ["1","2","3"]:
            for cj in ["1","2","3"]:
                if is_blank(bm, bn, ci, cj):
                    cells[(bm, bn, ci, cj)] = mark
                    wins = find_winning_moves(bm, bn, mark)
                    cells[(bm, bn, ci, cj)] = "b"
                    if len(wins) >= 2: forks.append((ci, cj))
        return forks
    
    bm, bn = "2", "2"
    
    # 1. Win immediately
    wins = find_winning_moves(bm, bn, my_mark)
    if wins: return f"mark({bm},{bn},{wins[0][0]},{wins[0][1]})"
    
    # 2. Block opponent win
    blocks = find_winning_moves(bm, bn, opp_mark)
    if blocks: return f"mark({bm},{bn},{blocks[0][0]},{blocks[0][1]})"
    
    # 3. Create fork
    forks = find_forks(bm, bn, my_mark)
    if forks: return f"mark({bm},{bn},{forks[0][0]},{forks[0][1]})"
    
    # 4. Block opponent fork
    opp_forks = find_forks(bm, bn, opp_mark)
    if opp_forks: return f"mark({bm},{bn},{opp_forks[0][0]},{opp_forks[0][1]})"
    
    # 5. Take center
    if is_blank(bm, bn, "2", "2"): return f"mark({bm},{bn},2,2)"
    
    # 6. Opposite corner if opponent in corner
    opposite = {("1","1"):("3","3"), ("1","3"):("3","1"), ("3","1"):("1","3"), ("3","3"):("1","1")}
    for c, oc in opposite.items():
        if get_cell(bm, bn, c[0], c[1]) == opp_mark and is_blank(bm, bn, oc[0], oc[1]):
            return f"mark({bm},{bn},{oc[0]},{oc[1]})"
    
    # 7. Any corner
    for ci, cj in [("1","1"), ("1","3"), ("3","1"), ("3","3")]:
        if is_blank(bm, bn, ci, cj): return f"mark({bm},{bn},{ci},{cj})"
    
    # 8. Any edge
    for ci, cj in [("1","2"), ("2","1"), ("2","3"), ("3","2")]:
        if is_blank(bm, bn, ci, cj): return f"mark({bm},{bn},{ci},{cj})"
    
    # 9. Anywhere
    for b1 in ["1","2","3"]:
        for b2 in ["1","2","3"]:
            for c1 in ["1","2","3"]:
                for c2 in ["1","2","3"]:
                    if is_blank(b1, b2, c1, c2): return f"mark({b1},{b2},{c1},{c2})"
    return "mark(1,1,1,1)"
