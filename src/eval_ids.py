from pathlib import Path
import random


ids=[d.name.removesuffix('.json') for d in Path('data/evaluation').iterdir()]
print(random.Random(42).sample(ids,k=20))