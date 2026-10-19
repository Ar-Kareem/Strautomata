```python
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    def pos_to_idx(x: int, y: int, z: int) -> int:
        return x * 9 + y * 3 + z

