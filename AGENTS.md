## Cursor Cloud specific instructions

### Architecture

Two services — a Python/Flask backend (port 5050) and a Next.js frontend (port 3000). No databases, Docker, or external services required. Everything runs in-memory.

### Running services

**Backend:** `cd AI-video-reccomendation && python3 server.py` (port 5050). On first request to `/next_video`, ResNet-18 processes video embeddings on CPU which takes ~50s. Subsequent requests are fast.

**Frontend:** `cd AI-video-reccomendation/ui && npm run dev` (port 3000). Fetches from `http://127.0.0.1:5050`.

### Lint / Build

- `cd AI-video-reccomendation/ui && npx next lint` — ESLint
- `cd AI-video-reccomendation/ui && npx next build` — production build

### Gotchas

- There is no `requirements.txt` in the repo. Python deps must be installed manually: `flask flask-cors torch torchvision opencv-python-headless numpy scikit-learn Pillow`. Use `--index-url https://download.pytorch.org/whl/cpu` for torch/torchvision separately from the rest (PyPI CPU-only index doesn't carry non-PyTorch packages).
- The `VIDEOS_DIR` in `server.py` resolves relative to `os.getcwd()`, so the Flask server must be started from `AI-video-reccomendation/`.
- `~/.local/bin` may not be on PATH — add it if `flask` command is not found.
- The frontend hardcodes `http://127.0.0.1:5050` as the API URL in `tiktok-feed.tsx`.
