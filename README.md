# Nova-Flix 🎬🎵

**Unified media hub**: movies, series, music — download & stream via Radarr, Sonarr, Jellyfin, qBittorrent + Ollama AI assistant.

```
┌────────────────────────────────────────────────────────┐
│                      NOVA-FLIX                         │
├────────────────────────────────────────────────────────┤
│  RADARR          SONARR          PROWLARR             │
│  (movies)        (series)        (indexers)           │
├────────────────────────────────────────────────────────┤
│               QBITTORRENT                             │
│               (downloads)                             │
├────────────────────────────────────────────────────────┤
│  JELLYFIN (WSL)          NOVA-TUNES                  │
│  (streaming)             (music)                      │
├────────────────────────────────────────────────────────┤
│            OLLAMA (AI assistant)                      │
│    (recommendations, summaries, TTS)                  │
└────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Clone & setup
cd /home/niko/nova-flix
cp config/config.yaml.example config/config.yaml

# Edit config with your API keys
# See below for how to find them

# Run
python3 nova_flix.py status
python3 nova_flix.py search movie "Dune 2021"
python3 nova_flix.py search series "Arcane"
```

## Features

- **Movies**: Search & download via Radarr → qBittorrent
- **Series**: Search & download via Sonarr → qBittorrent
- **Direct Download**: Download from Prowlarr directly to qBittorrent
- **Streaming**: Stream via Jellyfin (WSL) or native Windows
- **Music**: Download & organize music (merged from nova-tunes)
- **AI Assistant**: Ollama-powered recommendations, summaries, TTS

## API Keys Setup

### Radarr
1. Settings → General → API Key
2. Or: `cat /mnt/c/ProgramData/Radarr/config.xml | grep ApiKey`

### Sonarr
1. Settings → General → API Key
2. Or: `cat /mnt/c/ProgramData/NzbDrone/config.xml | grep ApiKey`

### Prowlarr
1. Settings → General → API Key
2. Or: `cat /mnt/c/ProgramData/Prowlarr/config.xml | grep ApiKey`

### qBittorrent
- Username: admin (default)
- Password: your_web_ui_password (check qBittorrent settings)

## Configuration

```yaml
# config/config.yaml
radarr:
  url: "http://192.168.1.X:7878"
  api_key: "your_radarr_api_key"

sonarr:
  url: "http://192.168.1.X:8989"
  api_key: "your_sonarr_api_key"

prowlarr:
  url: "http://192.168.1.X:9696"
  api_key: "your_prowlarr_api_key"

qbittorrent:
  url: "http://192.168.1.X:8080"
  username: "admin"
  password: "your_password"

jellyfin:
  url: "http://localhost:8096"
  api_key: "your_jellyfin_api_key"

ollama:
  url: "http://localhost:11434"
```

## Commands

```bash
# Status
python3 nova_flix.py status

# Search
python3 nova_flix.py search movie "Dune"
python3 nova_flix.py search series "Arcane"
python3 nova_flix.py prowlarr "Dune 2021"

# Add to library
python3 nova_flix.py add movie "Dune"
python3 nova_flix.py add series "Arcane"

# Download directly
python3 nova_flix.py download 0  # download first result

# Library
python3 nova_flix.py library radarr
python3 nova_flix.py library sonarr

# Downloads
python3 nova_flix.py downloads

# Control
python3 nova_flix.py pause <hash>
python3 nova_flix.py resume <hash>
python3 nova_flix.py delete <hash>

# Jellyfin
python3 nova_flix.py jellyfin libraries
python3 nova_flix.py jellyfin search "Dune"

# AI
python3 nova_flix.py ai recommend "action movies like Die Hard"
python3 nova_flix.py ai summarize "Dune"
python3 nova_flix.py ai tts "Watch this great movie"
```

## Docker: Jellyfin (WSL)

```bash
cd /home/niko/nova-flix/docker
docker-compose up -d
```

Access Jellyfin: http://localhost:8096

## Hermes Skill

See `skills/nova-flix.md` for Hermes integration.

## Architecture

```
Prowlarr (indexers)
       ↓
  Radarr/Sonarr (management)
       ↓
  qBittorrent (download)
       ↓
   Jellyfin (streaming)
       ↓
    Ollama (AI)
```

## License

MIT — Nikodindon 2025