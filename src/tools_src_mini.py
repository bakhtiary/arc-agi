Grid = list[list[int]]
Object = list[tuple[tuple[int,int], int]]

def direct_neighbors(loc: tuple[int,int]) -> list[tuple[int,int]]:
    """ directly adjacent indices (including invalid (negative) indiced) """
    return list(set({(loc[0] - 1, loc[1]), (loc[0] + 1, loc[1]), (loc[0], loc[1] - 1), (loc[0], loc[1] + 1)}))


def diagonal_neighbors(loc: tuple[int,int]) -> list[tuple[int,int]]:
    """ diagonally adjacent indices (including invalid (negative) indiced) """
    return list(set({(loc[0] - 1, loc[1] - 1), (loc[0] - 1, loc[1] + 1), (loc[0] + 1, loc[1] - 1), (loc[0] + 1, loc[1] + 1)}))


def neighbors(loc: tuple[int,int]) -> list[tuple[int,int]]:
    """ adjacent indices (including invalid (negative) indiced) """
    return list(set(direct_neighbors(loc)) | set(diagonal_neighbors(loc)))

def most_color(element: Object|Grid) -> int:
    """ most common color """
    if isinstance(element[0], tuple): # an object
        values = [x[1] for x in element]
    else:
        values = [cell for row in element for cell in row]
    return max(set(values), key=values.count)


def as_indices(grid: Grid) -> list[tuple[int,int]]:
    """ indices of all grid cells """
    return list((i, j) for i in range(len(grid)) for j in range(len(grid[0])))

def get_grid_objects(grid: Grid, univalued: bool, diagonal: bool, without_bg: bool) -> list[Object]:
    """ Extract connected objects from a grid.

    Args:
        grid (List[List[int]]): A 2D grid represented as a list of lists of integers.
        univalued (bool): If True, only consider connected cells with the same value as part of an object.
                          If False, any non-background value is included in the object.
        diagonal (bool): If True, include diagonal neighbors when determining connectivity.
                         If False, only consider orthogonal neighbors (up, down, left, right).
        without_bg (bool): If True, ignore the background value, when finding objects.

    Returns:
        List[Object]: A list of objects, where each object is a list of tuples like ((row index, column index), value).
    """

    bg = most_color(grid) if without_bg else None
    objs = []
    occupied = set()
    h, w = len(grid), len(grid[0])
    unvisited = as_indices(grid)
    diag_fun = neighbors if diagonal else direct_neighbors
    for loc in unvisited:
        if loc in occupied:
            continue
        val = grid[loc[0]][loc[1]]
        if val == bg:
            continue
        obj = {(loc, val)}
        cands = {loc}
        while len(cands) > 0:
            neighborhood = set()
            for cand in cands:
                v = grid[cand[0]][cand[1]]
                if (val == v) if univalued else (v != bg):
                    obj.add((cand, v))
                    occupied.add(cand)
                    neighborhood |= {
                        (i, j) for i, j in diag_fun(cand) if 0 <= i < h and 0 <= j < w
                    }
            cands = neighborhood - occupied
        objs.append(list(obj))
    return objs


def has_hole(obj: Object) -> bool:
    from collections import deque

    # Extract the set of positions from the object
    positions = set(pos for pos, val in obj)
    
    # Determine the bounding box of the object
    min_i = min(pos[0] for pos in positions)
    max_i = max(pos[0] for pos in positions)
    min_j = min(pos[1] for pos in positions)
    max_j = max(pos[1] for pos in positions)

    height = max_i - min_i + 1
    width = max_j - min_j + 1

    # Initialize the grid representing the bounding box
    grid = [[0 for _ in range(width)] for _ in range(height)]

    # Mark the object positions on the grid
    for (i, j) in positions:
        grid[i - min_i][j - min_j] = 1  # Mark object cells with 1

    # Initialize the visited matrix for background cells
    visited = [[False for _ in range(width)] for _ in range(height)]
    queue = deque()

    # Start flood fill from the boundary cells
    for i in range(height):
        for j in range(width):
            if (i == 0 or i == height - 1 or j == 0 or j == width - 1) and grid[i][j] == 0:
                queue.append((i, j))
                visited[i][j] = True

    # Perform BFS to mark all reachable background cells
    while queue:
        i, j = queue.popleft()
        for ni, nj in [(i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)]:
            if 0 <= ni < height and 0 <= nj < width and grid[ni][nj] == 0 and not visited[ni][nj]:
                queue.append((ni, nj))
                visited[ni][nj] = True

    # Check for any unvisited background cells (holes)
    for i in range(height):
        for j in range(width):
            if grid[i][j] == 0 and not visited[i][j]:
                return True  # Hole detected

    return False  # No holes found
