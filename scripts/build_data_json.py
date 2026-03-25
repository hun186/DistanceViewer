from pathlib import Path
import json
import pandas as pd
import re


def date_key(path: Path):
    m = re.search(r"_(\d{8})$", path.stem)
    return (int(m.group(1)) if m else 0, path.name)


def pick_latest_excel() -> Path:
    preferred = list(Path('.').glob('Ikariam島嶼_New_*.xlsx'))
    if preferred:
        return sorted(preferred, key=date_key, reverse=True)[0]
    all_xlsx = list(Path('.').glob('*.xlsx'))
    if all_xlsx:
        return sorted(all_xlsx, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    raise FileNotFoundError('No excel file found')


def main() -> None:
    excel = pick_latest_excel()
    df = pd.read_excel(excel)
    rows = [
        {
            'x': int(x),
            'y': int(y),
            'resource': str(resource or ''),
            'wonder': str(wonder or ''),
        }
        for x, y, resource, wonder in df[['X', 'Y', '資源', '神蹟']].itertuples(index=False, name=None)
    ]
    output = Path('data/islands_data.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'rows': rows}, ensure_ascii=False), encoding='utf-8')
    print(f'Wrote {len(rows)} rows to {output} from {excel}')


if __name__ == '__main__':
    main()
