import re
from pathlib import Path

count = 0
count_success = 0
for md in Path("important-run-logs/20241027-165323").rglob('*.md'):
    print(md)
    with open(md, 'r') as f:
        count += 1
        if re.match("state machine finished, result is None", f.readlines()[-1]) is None:
            count_success +=1

print (count_success, count)