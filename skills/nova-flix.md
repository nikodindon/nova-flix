# Nova-Flix

**Unified media hub** — Movies, series, music via Radarr, Sonarr, Jellyfin, qBittorrent + Ollama.

## Setup

### 1. Clone and configure

```bash
cd /home/niko
git clone https://github.com/nikodindon/nova-flix.git
cd nova-flix
cp config/config.yaml.example config/config.yaml
```

### 2. API Keys

Find your API keys:

```bash
# Radarr
cat /mnt/c/ProgramData/Radarr/config.xml | grep -i api

# Prowlarr  
cat /mnt/c/ProgramData/Prowlarr/config.xml | grep -i api
```

### 3. Services

Make sure these Windows apps are running:
- Radarr (port 7878)
- qBittorrent (port 8080)
- Prowlarr (port 9696)
- Sonarr (port 8989) — optionnel
- Jellyfin via Docker (port 8096) — optionnel

### 4. Test

```bash
cd /home/niko/nova-flix
python3 nova_flix.py status
```

## Usage

### Status

```python
from nova_flix import NovaFlix

nf = NovaFlix()
nf.status()  # {radarr, sonarr, qbittorrent, jellyfin}
```

### Search & Add Movies

```python
# Search Radarr
results = nf.search_movie("Dune 2021")
# [{title, year, tmdbId}, ...]

# Add to Radarr library
nf.add_movie("Dune 2021")  # Triggers auto-search & download
```

### Search & Add Series

```python
results = nf.search_series("Arcane")
nf.add_series("Arcane")
```

### Direct Download via Prowlarr

```python
# Search all indexers
results = nf.search_prowlarr("Dune 2021 1080p", limit=10)
# [{title, size, downloadUrl}, ...]

# Download first result to qBittorrent
nf.add_torrent_from_prowlarr(results[0])
```

### Manage Downloads

```python
# List torrents
torrents = nf.get_torrents()
# [{name, progress, state, size, dlspeed}, ...]

# Control
nf.pause_torrent(hash)
nf.resume_torrent(hash)
nf.delete_torrent(hash, delete_files=False)
```

### Jellyfin (Streaming)

```python
# List libraries
libs = nf.jellyfin_libraries()

# Search
results = nf.jellyfin_search("Dune")
```

### AI Recommendations

```python
# Movie recommendations via Ollama
nf.ai_recommend("action movies like Die Hard")
```

## Commands

```bash
cd /home/niko/nova-flix
python3 nova_flix.py status                    # Check all services
python3 nova_flix.py search movie "Dune"       # Search movies
python3 nova_flix.py search series "Arcane"    # Search series
python3 nova_flix.py prowlarr "Dune 2021"      # Search all indexers
python3 nova_flix.py add movie "Dune"          # Add to Radarr
python3 nova_flix.py add series "Arcane"       # Add to Sonarr
python3 nova_flix.py downloads                 # Show qBittorrent
python3 nova_flix.py library radarr            # Show Radarr library
python3 nova_flix.py jellyfin search "Dune"   # Jellyfin search
python3 nova_flix.py ai recommend "action"    # AI recommendation
```

## Jellyfin Docker

```bash
cd /home/niko/nova-flix/docker
docker-compose up -d

# Access: http://localhost:8096
```

## Troubleshooting

### "401 Unauthorized" from Radarr
API key changed. Get new one:
```bash
cat /mnt/c/ProgramData/Radarr/config.xml | grep ApiKey
```

### qBittorrent 403 Forbidden
Password incorrect. Check in qBittorrent Web UI settings.

### Services unreachable from WSL
Check Windows firewall or use correct IP:
```bash
# Find Windows gateway IP from WSL
ip route | grep default
```

## Hermes Skill Integration

Load this skill in Hermes:

```
skill: nova-flix
```

Then use in conversations:

```
Search movies like "Dune"
Add "Arcane" to download queue
Show my downloads
```

## Notes

- Radarr auto-search sometimes fails with download client. Use `search_prowlarr()` + `add_torrent_from_prowlarr()` as workaround.
- Jellyfin needs to be configured with media paths to /mnt/c/Users/...
- For AI features, ensure Ollama is running at localhost:11434