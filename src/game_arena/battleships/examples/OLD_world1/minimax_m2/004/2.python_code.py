
def policy(board: list[list[int]]) -> tuple[int, int]:
    known_hits = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                known_hits.append((r, c))
    
    if not known_hits:
        for r in range(10):
            for c in range(10):
                if ((r % 2 == 0 and c % 2 == 0) or (r % 2 == 1 and c % 2 == 1)) and board[r][c] == 0:
                    return (r, c)
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)
    
    visited = set()
    clusters = []
    for hit in known_hits:
        if hit in visited:
            continue
        cluster = [hit]
        visited.add(hit)
        queue = [hit]
        while queue:
            node = queue.pop()
            for next_hit in known_hits:
                if next_hit in visited:
                    continue
                if (node[0] == next_hit[0] and abs(node[1] - next_hit[1]) == 1) or (node[1] == next_hit[1] and abs(node[0] - next_hit[0]) == 1):
                    cluster.append(next_hit)
                    visited.add(next_hit)
                    queue.append(next_hit)
        clusters.append(cluster)
    
    clusters.sort(key=len, reverse=True)
    
    for cluster in clusters:
        if len(cluster) == 1:
            r, c = cluster[0]
            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    return (nr, nc)
        else:
            rows = set(r0 for r0, c0 in cluster)
            cols = set(c0 for r0, c0 in cluster)
            if len(rows) == 1:
                r = list(rows)[0]
                cols_list = sorted([c0 for r0, c0 in cluster if r0 == r])
                min_c = cols_list[0]
                max_c = cols_list[-1]
                if min_c - 1 >= 0 and board[r][min_c-1] == 0:
                    return (r, min_c-1)
                if max_c + 1 < 10 and board[r][max_c+1] == 0:
                    return (r, max_c+1)
            elif len(cols) == 1:
                c = list(cols)[0]
                rows_list = sorted([r0 for r0, c0 in cluster if c0 == c])
                min_r = rows_list[0]
                max_r = rows_list[-1]
                if min_r - 1 >= 0 and board[min_r-1][c] == 0:
                    return (min_r-1, c)
                if max_r + 1 < 10 and board[max_r+1][c] == 0:
                    return (max_r+1, c)
            else:
                for (r, c) in cluster:
                    for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                            return (nr, nc)
    
    for r in range(10):
        for c in range(10):
            if ((r % 2 == 0 and c % 2 == 0) or (r % 2 == 1 and c % 2 == 1)) and board[r][c] == 0:
                return (r, c)
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)
