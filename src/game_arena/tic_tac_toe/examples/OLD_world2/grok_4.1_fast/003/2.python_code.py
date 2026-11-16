```python
def has_winner(board: list[list[int]]) -> int:
    n = 4
    # rows
    for i in range(n):
        row = board[i]
        if row[0] != 0 and all(x == row[0]