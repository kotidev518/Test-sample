
import json
from pydantic import TypeAdapter
from typing import List

val1 = '["http://localhost:3000", "https://app.vercel.app"]'
val2 = 'http://localhost:3000, https://app.vercel.app'

def test_parse(val):
    try:
        # Pydantic 2.x TypeAdapter
        adapter = TypeAdapter(List[str])
        return adapter.validate_json(val)
    except Exception as e:
        try:
             # Try split by comma
             return [x.strip() for x in val.split(',')]
        except:
            return [val]

print(f"Val 1: {test_parse(val1)}")
print(f"Val 2: {test_parse(val2)}")
