#!/usr/bin/env python3
"""
Nova-Flix — Unified media hub for Hermes
Movies, series, music via Radarr, Sonarr, Jellyfin, qBittorrent + Ollama
"""

import argparse
import os
import sys
import yaml
import requests
import time
from pathlib import Path


class NovaFlix:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or Path(__file__).parent / "config.yaml"
        self.config = self._load_config()
        
        self.radarr_url = self.config["radarr"]["url"]
        self.radarr_api = self.config["radarr"]["api_key"]
        
        self.sonarr_url = self.config["sonarr"]["url"]
        self.sonarr_api = self.config["sonarr"]["api_key"]
        
        self.prowlarr_url = self.config["prowlarr"]["url"]
        self.prowlarr_api = self.config["prowlarr"]["api_key"]
        
        self.qbit_url = self.config["qbittorrent"]["url"]
        self.qbit_user = self.config["qbittorrent"]["username"]
        self.qbit_pass = self.config["qbittorrent"]["password"]
        
        self.jellyfin_url = self.config.get("jellyfin", {}).get("url")
        self.jellyfin_api = self.config.get("jellyfin", {}).get("api_key")
        
        self.ollama_url = self.config.get("ollama", {}).get("url", "http://localhost:11434")
        
        self.session = requests.Session()
    
    def _load_config(self) -> dict:
        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        with open(self.config_path) as f:
            return yaml.safe_load(f)
    
    # === RADARR ===
    
    def get_movies(self) -> list:
        self.session.headers["X-Api-Key"] = self.radarr_api
        resp = self.session.get(f"{self.radarr_url}/api/v3/movie")
        resp.raise_for_status()
        return resp.json()
    
    def search_movie(self, query: str) -> list:
        self.session.headers["X-Api-Key"] = self.radarr_api
        resp = self.session.get(
            f"{self.radarr_url}/api/v3/movie/lookup",
            params={"term": query}
        )
        resp.raise_for_status()
        return resp.json()
    
    def add_movie(self, query: str, quality_profile_id: int = 1) -> dict:
        results = self.search_movie(query)
        if not results:
            raise ValueError(f"No movie found: {query}")
        
        movie = results[0]
        folders = self.session.get(f"{self.radarr_url}/api/v3/rootfolder", 
                                   headers={"X-Api-Key": self.radarr_api})
        root_folder = folders.json()[0]["path"]
        
        payload = {
            "title": movie["title"],
            "titles": movie.get("titles", []),
            "qualityProfileId": quality_profile_id,
            "rootFolderPath": root_folder,
            "tmdbId": movie["tmdbId"],
            "year": movie.get("year"),
            "addOptions": {"searchForMovie": True}
        }
        
        self.session.headers["X-Api-Key"] = self.radarr_api
        resp = self.session.post(f"{self.radarr_url}/api/v3/movie", json=payload)
        resp.raise_for_status()
        return resp.json()
    
    # === SONARR ===
    
    def get_series(self) -> list:
        self.session.headers["X-Api-Key"] = self.sonarr_api
        resp = self.session.get(f"{self.sonarr_url}/api/v3/series")
        resp.raise_for_status()
        return resp.json()
    
    def search_series(self, query: str) -> list:
        self.session.headers["X-Api-Key"] = self.sonarr_api
        resp = self.session.get(
            f"{self.sonarr_url}/api/v3/series/lookup",
            params={"term": query}
        )
        resp.raise_for_status()
        return resp.json()
    
    def add_series(self, query: str) -> dict:
        results = self.search_series(query)
        if not results:
            raise ValueError(f"No series found: {query}")
        
        series = results[0]
        folders = self.session.get(f"{self.sonarr_url}/api/v3/rootfolder",
                                   headers={"X-Api-Key": self.sonarr_api})
        root_folder = folders.json()[0]["path"]
        
        payload = {
            "title": series["title"],
            "titles": series.get("titles", []),
            "qualityProfileId": 1,
            "rootFolderPath": root_folder,
            "tvdbId": series["tvdbId"],
            "seasonFolder": True,
            "addOptions": {"searchForSeason": True, "searchForEpisodes": True}
        }
        
        self.session.headers["X-Api-Key"] = self.sonarr_api
        resp = self.session.post(f"{self.sonarr_url}/api/v3/series", json=payload)
        resp.raise_for_status()
        return resp.json()
    
    # === PROWLARR ===
    
    def search_prowlarr(self, query: str, limit: int = 10) -> list:
        self.session.headers["X-Api-Key"] = self.prowlarr_api
        resp = self.session.get(
            f"{self.prowlarr_url}/api/v1/search",
            params={"query": query, "limit": limit}
        )
        if resp.status_code == 200:
            return resp.json()
        return []
    
    def add_torrent_from_prowlarr(self, release: dict, category: str = "movies") -> bool:
        if not release.get("downloadUrl"):
            return False
        
        url = release["downloadUrl"].replace("***", self.prowlarr_api)
        torrent_data = requests.get(url).content
        if not torrent_data or len(torrent_data) < 100:
            print("Failed to download torrent")
            return False
        
        temp_path = "/tmp/nova_flix.torrent"
        with open(temp_path, "wb") as f:
            f.write(torrent_data)
        
        login_resp = self.session.post(
            f"{self.qbit_url}/api/v2/auth/login",
            data={"username": self.qbit_user, "password": self.qbit_pass}
        )
        if login_resp.text != "Ok.":
            print(f"qBittorrent login failed: {login_resp.text}")
            return False
        
        with open(temp_path, "rb") as f:
            files = {"file": ("torrent.torrent", f)}
            add_resp = self.session.post(
                f"{self.qbit_url}/api/v2/torrents/add",
                files=files,
                data={"category": category}
            )
        
        os.remove(temp_path)
        
        if add_resp.text == "Ok.":
            print(f"✓ Added: {release.get('title', 'Unknown')}")
            return True
        print(f"Failed: {add_resp.text}")
        return False
    
    # === QBITTORRENT ===
    
    def get_torrents(self) -> list:
        login_resp = self.session.post(
            f"{self.qbit_url}/api/v2/auth/login",
            data={"username": self.qbit_user, "password": self.qbit_pass}
        )
        if login_resp.text != "Ok.":
            raise Exception(f"qBittorrent login failed: {login_resp.text}")
        
        resp = self.session.get(f"{self.qbit_url}/api/v2/torrents/info")
        resp.raise_for_status()
        return resp.json()
    
    def pause_torrent(self, hash: str) -> bool:
        self.session.post(
            f"{self.qbit_url}/api/v2/torrents/pause",
            data={"hashes": hash}
        )
        return True
    
    def resume_torrent(self, hash: str) -> bool:
        self.session.post(
            f"{self.qbit_url}/api/v2/torrents/resume",
            data={"hashes": hash}
        )
        return True
    
    def delete_torrent(self, hash: str, delete_files: bool = False) -> bool:
        self.session.post(
            f"{self.qbit_url}/api/v2/torrents/delete",
            data={"hashes": hash, "deleteFiles": delete_files}
        )
        return True
    
    # === JELLYFIN ===
    
    def jellyfin_libraries(self) -> list:
        if not self.jellyfin_url:
            return []
        self.session.headers["X-Emby-Token"] = self.jellyfin_api
        resp = self.session.get(f"{self.jellyfin_url}/emby/Views")
        if resp.status_code == 200:
            return resp.json().get("Items", [])
        return []
    
    def jellyfin_search(self, query: str) -> list:
        if not self.jellyfin_url:
            return []
        self.session.headers["X-Emby-Token"] = self.jellyfin_api
        resp = self.session.get(
            f"{self.jellyfin_url}/emby/Items",
            params={"SearchTerm": query, "Limit": 10}
        )
        if resp.status_code == 200:
            return resp.json().get("Items", [])
        return []
    
    # === OLLAMA AI ===
    
    def ai_chat(self, prompt: str, model: str = "llama3.2") -> str:
        resp = requests.post(
            f"{self.ollama_url}/api/chat",
            json={"model": model, "messages": [{"role": "user", "content": prompt}]}
        )
        if resp.status_code == 200:
            return resp.json().get("message", {}).get("content", "")
        return f"Error: {resp.status_code}"
    
    def ai_recommend(self, query: str) -> str:
        prompt = f"Recommend 5 movies similar to: {query}. Give title, year, and brief reason."
        return self.ai_chat(prompt)
    
    def ai_tts(self, text: str) -> bytes:
        # Uses Ollama's multimodal capability or external TTS
        # For now, returns text that could be sent to TTS service
        return text.encode()
    
    # === STATUS ===
    
    def status(self) -> dict:
        s = {}
        
        # Radarr
        try:
            self.session.headers["X-Api-Key"] = self.radarr_api
            r = self.session.get(f"{self.radarr_url}/api/v3/system/status")
            s["radarr"] = "OK" if r.status_code == 200 else f"Error {r.status_code}"
        except Exception as e:
            s["radarr"] = f"Failed: {e}"
        
        # Sonarr
        try:
            self.session.headers["X-Api-Key"] = self.sonarr_api
            r = self.session.get(f"{self.sonarr_url}/api/v3/system/status")
            s["sonarr"] = "OK" if r.status_code == 200 else f"Error {r.status_code}"
        except Exception as e:
            s["sonarr"] = f"Failed: {e}"
        
        # Prowlarr
        try:
            self.session.headers["X-Api-Key"] = self.prowlarr_api
            r = self.session.get(f"{self.prowlarr_url}/api/v1/config")
            s["prowlarr"] = "OK" if r.status_code == 200 else f"Error {r.status_code}"
        except Exception as e:
            s["prowlarr"] = f"Failed: {e}"
        
        # qBittorrent
        try:
            login_resp = self.session.post(
                f"{self.qbit_url}/api/v2/auth/login",
                data={"username": self.qbit_user, "password": self.qbit_pass}
            )
            s["qbittorrent"] = "OK" if login_resp.text == "Ok." else "Login failed"
        except Exception as e:
            s["qbittorrent"] = f"Failed: {e}"
        
        # Jellyfin
        try:
            if self.jellyfin_url:
                self.session.headers["X-Emby-Token"] = self.jellyfin_api
                r = self.session.get(f"{self.jellyfin_url}/emby/System/Info")
                s["jellyfin"] = "OK" if r.status_code == 200 else f"Error {r.status_code}"
            else:
                s["jellyfin"] = "Not configured"
        except Exception as e:
            s["jellyfin"] = f"Failed: {e}"
        
        return s


def main():
    parser = argparse.ArgumentParser(description="Nova-Flix — unified media hub")
    subparsers = parser.add_subparsers(dest="command")
    
    # Status
    subparsers.add_parser("status", help="Check service status")
    
    # Search
    search_parser = subparsers.add_parser("search", help="Search media")
    search_parser.add_argument("type", choices=["movie", "series"], help="Media type")
    search_parser.add_argument("query", help="Search query")
    
    # Prowlarr search
    prowlarr_parser = subparsers.add_parser("prowlarr", help="Search Prowlarr indexers")
    prowlarr_parser.add_argument("query", help="Search query")
    
    # Add
    add_parser = subparsers.add_parser("add", help="Add to library")
    add_parser.add_argument("type", choices=["movie", "series"], help="Media type")
    add_parser.add_argument("query", help="Media name")
    
    # Download from Prowlarr
    dl_parser = subparsers.add_parser("download", help="Download from Prowlarr result")
    dl_parser.add_argument("index", type=int, help="Result index to download")
    dl_parser.add_argument("--category", default="movies", help="qBittorrent category")
    
    # Library
    lib_parser = subparsers.add_parser("library", help="Show library")
    lib_parser.add_argument("type", choices=["radarr", "sonarr"], help="Which library")
    
    # Downloads
    subparsers.add_parser("downloads", help="Show torrents")
    
    # Control
    control_parser = subparsers.add_parser("pause", help="Pause torrent")
    control_parser.add_argument("hash", help="Torrent hash")
    
    control_parser = subparsers.add_parser("resume", help="Resume torrent")
    control_parser.add_argument("hash", help="Torrent hash")
    
    control_parser = subparsers.add_parser("delete", help="Delete torrent")
    control_parser.add_argument("hash", help="Torrent hash")
    control_parser.add_argument("--files", action="store_true", help="Also delete files")
    
    # Jellyfin
    jf_parser = subparsers.add_parser("jellyfin", help="Jellyfin commands")
    jf_parser.add_argument("action", choices=["libraries", "search"], default="libraries")
    jf_parser.add_argument("query", nargs="?", help="Search query")
    
    # AI
    ai_parser = subparsers.add_parser("ai", help="AI commands")
    ai_parser.add_argument("action", choices=["recommend", "chat", "tts"])
    ai_parser.add_argument("prompt", help="Prompt/query")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    nf = NovaFlix()
    
    if args.command == "status":
        s = nf.status()
        print("=== Nova-Flix Status ===")
        for svc, state in s.items():
            print(f"  {svc}: {state}")
    
    elif args.command == "search":
        if args.type == "movie":
            results = nf.search_movie(args.query)
            print(f"=== Movies: {args.query} ===")
            for i, m in enumerate(results[:10], 1):
                print(f"  {i}. {m.get('title')} ({m.get('year')})")
        else:
            results = nf.search_series(args.query)
            print(f"=== Series: {args.query} ===")
            for i, s in enumerate(results[:10], 1):
                print(f"  {i}. {s.get('title')} ({s.get('year')})")
    
    elif args.command == "prowlarr":
        results = nf.search_prowlarr(args.query)
        print(f"=== Prowlarr: {args.query} ===")
        print(f"Found {len(results)} results")
        for i, r in enumerate(results[:10], 1):
            size = int(r.get("size", 0) / 1024 / 1024)
            print(f"  {i}. {r.get('title')} ({size}MB)")
        # Store for download
        nf._last_results = results
    
    elif args.command == "add":
        if args.type == "movie":
            result = nf.add_movie(args.query)
            print(f"✓ Added: {result.get('title')}")
        else:
            result = nf.add_series(args.query)
            print(f"✓ Added: {result.get('title')}")
    
    elif args.command == "download":
        if hasattr(nf, '_last_results') and nf._last_results:
            release = nf._last_results[args.index]
            nf.add_torrent_from_prowlarr(release, args.category)
        else:
            print("Run 'prowlarr' command first to search")
    
    elif args.command == "library":
        if args.type == "radarr":
            movies = nf.get_movies()
            print("=== Radarr Library ===")
            for m in movies:
                print(f"  {m.get('title')} ({m.get('year')}) - {m.get('status')}")
        else:
            series = nf.get_series()
            print("=== Sonarr Library ===")
            for s in series:
                print(f"  {s.get('title')} - {s.get('status')}")
    
    elif args.command == "downloads":
        torrents = nf.get_torrents()
        print("=== Downloads ===")
        for t in torrents:
            progress = t.get("progress", 0) * 100
            print(f"  {t.get('name')} - {progress:.1f}% [{t.get('state')}]")
    
    elif args.command == "pause":
        nf.pause_torrent(args.hash)
        print(f"✓ Paused")
    
    elif args.command == "resume":
        nf.resume_torrent(args.hash)
        print(f"✓ Resumed")
    
    elif args.command == "delete":
        nf.delete_torrent(args.hash, args.files)
        print(f"✓ Deleted")
    
    elif args.command == "jellyfin":
        if args.action == "libraries":
            libs = nf.jellyfin_libraries()
            print("=== Jellyfin Libraries ===")
            for lib in libs:
                print(f"  {lib.get('Name')} ({lib.get('CollectionType')})")
        else:
            results = nf.jellyfin_search(args.query)
            print(f"=== Jellyfin: {args.query} ===")
            for i, r in enumerate(results[:10], 1):
                print(f"  {i}. {r.get('Name')} ({r.get('Type')})")
    
    elif args.command == "ai":
        if args.action == "recommend":
            resp = nf.ai_recommend(args.prompt)
            print(resp)
        elif args.action == "chat":
            resp = nf.ai_chat(args.prompt)
            print(resp)
        else:
            print("TTS not implemented yet")


if __name__ == "__main__":
    main()