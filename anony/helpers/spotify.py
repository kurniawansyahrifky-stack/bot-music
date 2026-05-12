import asyncio
import requests


async def get_spotify_track(url: str):
    api_url = f"https://open.spotify.com/oembed?url={url}"

    def fetch():
        try:
            r = requests.get(api_url, timeout=10)
            if r.status_code != 200:
                return None, None

            data = r.json()
            title = data.get("title")
            if not title:
                return None, None

            if " - " in title:
                song, artist = title.split(" - ", 1)
            else:
                song = title
                artist = ""

            return song.strip(), artist.strip()
        except Exception:
            return None, None

    return await asyncio.to_thread(fetch)


async def get_spotify_playlist(url: str, limit: int, mention: str, video: bool = False):
    return []
