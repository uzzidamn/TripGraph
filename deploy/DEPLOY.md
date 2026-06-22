# Deploying TripGraph to a DigitalOcean droplet (demo over IP)

This gets TripGraph running at `http://YOUR_DROPLET_IP` with one script.
No domain, no HTTPS — ideal for a class demo. Tear the droplet down afterward.

## Architecture
```
Browser ──http://DROPLET_IP──▶ nginx (:80)
                                 ├── /            → built React app (frontend/dist)
                                 └── /api, /health → uvicorn backend (127.0.0.1:8000)
```
Everything is one origin, so the backend's localhost-only CORS is never an issue.
Neo4j is NOT required — the backend uses the `local_kg_store.json` fallback.

## Prerequisites
- A droplet (Ubuntu 22.04 or 24.04) with your `id_ed25519_do` key added.
- Its public IP (DigitalOcean dashboard → your droplet).
- Your local `.env` (the one with all the API keys — it is gitignored, so it
  must be copied up manually).

## Steps (run from your laptop)

1. **Copy the deploy script up** (the repo is public, the droplet clones it itself,
   but the script lives in the repo — so just clone-and-run, or scp it):
   ```bash
   scp -i ~/.ssh/id_ed25519_do deploy/deploy.sh root@YOUR_IP:/root/
   ```

2. **Copy your secrets up** (API keys — never committed to git):
   ```bash
   scp -i ~/.ssh/id_ed25519_do .env root@YOUR_IP:/opt/tripgraph/.env
   ```
   > If `/opt/tripgraph` doesn't exist yet, run the script once first — it will
   > stop and tell you to copy `.env`, then re-run after this scp.

3. **SSH in and run the script:**
   ```bash
   ssh -i ~/.ssh/id_ed25519_do root@YOUR_IP
   chmod +x /root/deploy.sh
   /root/deploy.sh YOUR_IP
   ```

4. Open **`http://YOUR_IP`** in a browser. Done. 🎉

## Updating after a code change
```bash
ssh -i ~/.ssh/id_ed25519_do root@YOUR_IP
/opt/tripgraph/deploy/deploy.sh YOUR_IP   # pulls latest, rebuilds, restarts
```

## Troubleshooting
| Symptom | Check |
|---|---|
| 502 Bad Gateway | `journalctl -u tripgraph-backend -f` — backend crashed (often a missing key in `.env`) |
| Blank page | `ls /opt/tripgraph/frontend/dist` — did the build run? Re-run script. |
| Map tiles / photos blank | `VITE_GOOGLE_MAPS_API_KEY` missing in `.env`, or the key is referrer-restricted to localhost in Google Cloud Console |
| API calls fail | Confirm `http://YOUR_IP/health` returns `{"status":"healthy"}` |
| Can't SSH | You used the wrong key — must be `-i ~/.ssh/id_ed25519_do` |

## Notes / caveats for a real (non-demo) deploy
- **HTTP only** — fine for a demo, but browsers warn on forms. For HTTPS you need
  a domain + Let's Encrypt (`certbot`). Ask and I'll add that path.
- **Google Maps key** is embedded in the built JS (it's a client key). Restrict it
  in Google Cloud Console to your droplet IP / domain to prevent abuse.
- **Single uvicorn worker** — fine for a demo. For load, add `--workers N` or a
  gunicorn+uvicorn worker setup.
- **API rate limits** still apply (ORS 2000/day, etc.) — see the app's API usage.
