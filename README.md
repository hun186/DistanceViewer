# DistanceViewer

A tool for displaying specific resource–god combinations in Ikariam and calculating distances between islands.

## Existing Desktop App

Desktop mode still works:

```bash
python DisViewer.py
```

## New Web Mode (Flask + Plotly)

This repo now also supports a web UI so users can interact in browser.

### Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app api.index run --debug
```

Open <http://127.0.0.1:5000>.

### Web features

- Query islands by 資源 / 神蹟
- Add/remove points interactively on chart
- Toggle Delaunay edges and labels
- Save/load point list in browser `localStorage`

### Data source behavior (cold-start optimized)

- Web API now prefers repo-local `data/islands_data.json` as primary source to avoid Excel parsing during cold start.
- Excel (`Ikariam島嶼_New_*.xlsx`) is treated as offline update source.
- To refresh JSON from latest Excel:

```bash
python scripts/build_data_json.py
```

## Deploy to Vercel

1. Install Vercel CLI and login:

```bash
npm i -g vercel
vercel login
```

2. Deploy:

```bash
vercel
```

3. Production deploy:

```bash
vercel --prod
```

Configuration is included in `vercel.json` and Python dependencies are in `requirements.txt`.


## 新人文件

- 新手快速上手請看：`docs/新人操作手冊.md`
- 純網頁使用者請看：`docs/網頁版操作手冊.md`
