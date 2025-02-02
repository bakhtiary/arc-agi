from pathlib import Path
import tempfile
import unittest

from code_utils import generate_tools_docs_by_ast, keep_only_defs_and_imports


class TestCodeUtils(unittest.TestCase):
    def test_generate_tools_docs_by_ast_actual(self):
        print(generate_tools_docs_by_ast(Path(__file__).parent.parent / 'src' / 'tools_src_mini.py', tool_type='all'))
    
    def test_generate_tools_docs_by_ast_hardcoded(self):
        with tempfile.NamedTemporaryFile(delete=False) as fp:            
            fp.close()
            file = Path(fp.name)
            file.write_text('''## flood fill, connect lines, describe shapes (with discribe inside, but about unconnected shapes with an "invisible" tie, or
# black squares on a large yellow rectangle)
from code_utils import ignore_for_llm_tools_docs
Grid = list[list[int]]
Object = list[tuple[tuple[int,int], int]]
BLUE=1

@llm_tool
def direct_neighbors(loc: tuple[int,int]) -> list[tuple[int,int]]:
    """ directly adjacent indices (including invalid (negative) indiced) """
    return list(set({(loc[0] - 1, loc[1]), (loc[0] + 1, loc[1]), (loc[0], loc[1] - 1), (loc[0], loc[1] + 1)}))

RED=2

@ignore_for_llm_tools_docs
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

''')
            docs = generate_tools_docs_by_ast(file, tool_type='all')
            self.assertIn('BLUE', docs)
            self.assertIn('''def direct_neighbors(loc: tuple[int,int]) -> list[tuple[int,int]]:
    """directly adjacent indices (including invalid (negative) indiced) """''', docs)
            self.assertNotIn('diagonal_neighbors', docs)
            self.assertNotIn('most_colors', docs)

    def test_keep_only_defs_and_imports(self):
        code = '''import sys
        
def f():
    return 0

x = f()
assert x==1

def g():
    ...'''
        new_code = keep_only_defs_and_imports(code)
        self.assertEqual(new_code, '''import sys

def f():
    return 0

def g():
    ...

''')

if __name__ == '__main__':
    TestCodeUtils().test_generate_tools_docs_by_ast_actual()
            