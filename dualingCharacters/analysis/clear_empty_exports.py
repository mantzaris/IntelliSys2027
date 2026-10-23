"""Remove stale CSV data when the corresponding regenerated JSON table is empty."""
from pathlib import Path
import json

root=Path(__file__).resolve().parents[1]
cleared=[]
for path in sorted((root/'reports/tables').glob('*.csv')):
    source=path.with_suffix('.json')
    if source.exists() and json.loads(source.read_text())==[] and path.read_bytes():
        path.write_text('');cleared.append(str(path.relative_to(root)))
print(json.dumps({'empty_json_tables_with_stale_csv_cleared':cleared}))
