# --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
#
#  Unauthorized copying, editing, re-uploading or removing credits
#  from this source code is strictly prohibited.
# --------------------------------------------------------------------------------

import asyncio
import logging
import os
import re
from typing import Union

import aiofiles
import aiohttp
import yt_dlp
from py_yt import Playlist, VideosSearch
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from ShizuMusic.utils.formatters import sec_to_iso

logger = logging.getLogger(__name__)

# ── API config ────────────────────────────────────────────────────────────────
SHRUTI_API_URL        = os.environ.get("SHRUTI_API_URL", "https://api.shrutibots.site")
SHRUTI_API_KEY        = os.environ.get("SHRUTI_API_KEY", "ShrutiBotsZWU3vIU63uUHoUPgOw2m")
DOWNLOAD_DIR          = "downloads"
SHRUTI_TOKEN_TIMEOUT  = 10
SHRUTI_STREAM_TIMEOUT = 900

_file_cache: dict[str, str] = {}


# ═════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _extract_video_id(url: str) -> str:
    """Extract raw video ID from any YouTube URL format."""
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return url


def _cleanup(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def time_to_seconds(time) -> int:
    """Convert M:SS or H:MM:SS string to total seconds."""
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


async def _native_ytdlp_download(video_id: str, is_video: bool = False) -> str:
    """High-speed native fallback extractor with Android/iOS client rotation."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ext = "mp4" if is_video else "mp3"
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    # First attempt: Piped / Invidious CDN Direct Stream
    piped_instances = [
        "https://pipedapi.kavin.rocks",
        "https://api.piped.privacydev.net",
        "https://pipedapi.leptons.xyz",
    ]
    for api in piped_instances:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{api}/streams/{video_id}", timeout=aiohttp.ClientTimeout(total=6)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        streams = data.get("videoStreams" if is_video else "audioStreams", [])
                        if streams:
                            target_url = streams[0].get("url")
                            async with session.get(target_url, timeout=aiohttp.ClientTimeout(total=300)) as dl:
                                if dl.status == 200:
                                    async with aiofiles.open(file_path, "wb") as f:
                                        async for chunk in dl.content.iter_chunked(131072):
                                            await f.write(chunk)
                                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                                        return file_path
        except Exception:
            continue

    # Second attempt: Direct yt-dlp Android client
    ydl_opts = {
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]" if is_video else "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "extractor_args": {"youtube": {"player_client": ["android", "ios"]}},
    }
    if not is_video:
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    def _ytdlp():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

    try:
        await asyncio.to_thread(_ytdlp)
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(video_id):
                return os.path.join(DOWNLOAD_DIR, f)
    except Exception as e:
        logger.error(f"[Fallback DL Error] {e}")

    return None


# ═════════════════════════════════════════════════════════════════════════════
# DOWNLOAD HELPERS (API + Multi-Node Fallback)
# ═════════════════════════════════════════════════════════════════════════════

async def download_song(link: str) -> str:
    """Download audio via API with automatic fallback. Returns file path or None."""
    video_id = _extract_video_id(link)
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    # Try Primary Shruti API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{SHRUTI_API_URL}/download",
                params={"url": video_id, "type": "audio", "api_key": SHRUTI_API_KEY},
                timeout=aiohttp.ClientTimeout(total=SHRUTI_STREAM_TIMEOUT),
            ) as resp:
                if resp.status == 200:
                    async with aiofiles.open(file_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(131072):
                            await f.write(chunk)
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        return file_path
                else:
                    logger.warning(f"[shruti] Audio API returned {resp.status}, triggering fallback...")
    except Exception as e:
        logger.warning(f"[shruti] Audio API error: {e}")

    # Fallback to direct streamer
    return await _native_ytdlp_download(video_id, is_video=False)


async def download_video(link: str) -> str:
    """Download video via API with automatic fallback. Returns file path or None."""
    video_id = _extract_video_id(link)
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    # Try Primary Shruti API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{SHRUTI_API_URL}/download",
                params={"url": video_id, "type": "video", "api_key": SHRUTI_API_KEY},
                timeout=aiohttp.ClientTimeout(total=SHRUTI_STREAM_TIMEOUT),
            ) as resp:
                if resp.status == 200:
                    async with aiofiles.open(file_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(131072):
                            await f.write(chunk)
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        return file_path
                else:
                    logger.warning(f"[shruti] Video API returned {resp.status}, triggering fallback...")
    except Exception as e:
        logger.warning(f"[shruti] Video API error: {e}")

    # Fallback to direct streamer
    return await _native_ytdlp_download(video_id, is_video=True)


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC — STREAM RESOLVER (Supports Audio & Video)
# ═════════════════════════════════════════════════════════════════════════════

async def resolve_stream(url: str, video: bool = False) -> str:
    """Resolve a YouTube URL or video ID to a local audio/video file path."""
    if os.path.exists(url) and os.path.isfile(url):
        return url

    cache_key = f"{url}_video" if video else url
    if cache_key in _file_cache and os.path.exists(_file_cache[cache_key]):
        logger.info("[Stream] Cache hit")
        return _file_cache[cache_key]

    video_id = _extract_video_id(url)
    ext = "mp4" if video else "mp3"
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        _file_cache[cache_key] = file_path
        return file_path

    logger.info(f"[Stream] Fetching {'video' if video else 'audio'}: {video_id}")
    downloaded = await download_video(url) if video else await download_song(url)
    if downloaded:
        _file_cache[cache_key] = downloaded
        logger.info(f"[Stream] Done — {os.path.getsize(downloaded) // 1024} KB")
        return downloaded

    raise Exception("ᴅᴏᴡɴʟᴏᴀᴅ ғᴀɪʟᴇᴅ. ᴩʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.")


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC — YOUTUBE SEARCH / METADATA
# ═════════════════════════════════════════════════════════════════════════════

async def search_yt(query: str):
    """Search YouTube for a video or playlist. Returns metadata tuple or playlist dict."""

    # ── Playlist ──────────────────────────────────────────────────────────────
    if "playlist?list=" in query or "&list=" in query:
        pl   = await Playlist.get(query)
        vids = pl.get("videos") or []
        if not vids:
            raise Exception("ᴩʟᴀʏʟɪsᴛ ɪs ᴇᴍᴩᴛʏ")

        items = []
        for v in vids:
            raw = v.get("duration", {})
            secs = 0
            if isinstance(raw, dict):
                try:
                    secs = int(raw.get("secondsText", 0))
                except Exception:
                    secs = 0
            else:
                try:
                    secs = int(raw)
                except Exception:
                    secs = 0

            thumbs = v.get("thumbnails") or []
            thumb  = thumbs[0].get("url", "").split("?")[0] if thumbs else ""
            items.append({
                "link":      f"https://www.youtube.com/watch?v={v['id']}",
                "title":     v.get("title", "Unknown"),
                "duration":  sec_to_iso(secs),
                "thumbnail": thumb,
            })
        return {"playlist": items}

    # ── Single video search ───────────────────────────────────────────────────
    search  = VideosSearch(query, limit=1)
    results = await search.next()
    lst     = results.get("result", [])
    if not lst:
        raise Exception("ɴᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ")

    r     = lst[0]
    url   = r.get("link") or f"https://www.youtube.com/watch?v={r['id']}"
    title = r.get("title", "Unknown")
    thumb = (r.get("thumbnails") or [{}])[0].get("url", "").split("?")[0]
    dur   = r.get("duration") or "0:00"

    parts = [int(x) for x in dur.split(":")]
    secs  = (
        parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 3
        else parts[0] * 60 + parts[1]
    )
    return (url, title, sec_to_iso(secs), thumb)


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC — YouTubeAPI CLASS
# ═════════════════════════════════════════════════════════════════════════════

class YouTubeAPI:
    def __init__(self):
        self.base     = "https://www.youtube.com/watch?v="
        self.regex    = r"(?:youtube\.com|youtu\.be)"
        self.status   = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg      = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    def _build_link(self, link: str, videoid) -> str:
        return (self.base + link) if videoid else link

    def _strip_extra(self, link: str) -> str:
        return link.split("&")[0] if "&" in link else link

    async def exists(self, link: str, videoid: Union[bool, str] = None) -> bool:
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        link = self._strip_extra(self._build_link(link, videoid))
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title        = result["title"]
            duration_min = result["duration"]
            thumbnail    = result["thumbnails"][0]["url"].split("?")[0]
            vidid        = result["id"]
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None) -> str:
        link = self._strip_extra(self._build_link(link, videoid))
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None) -> str:
        link = self._strip_extra(self._build_link(link, videoid))
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None) -> str:
        link = self._strip_extra(self._build_link(link, videoid))
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        link = self._strip_extra(self._build_link(link, videoid))
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(
        self, link: str, limit: int, user_id, videoid: Union[bool, str] = None
    ) -> list:
        if videoid:
            link = self.listbase + link
        link = self._strip_extra(link)
        try:
            plist = await Playlist.get(link)
        except Exception:
            return []
        videos = plist.get("videos") or []
        ids = []
        for data in videos[:limit]:
            if not data:
                continue
            vid = data.get("id")
            if not vid:
                continue
            ids.append(vid)
        return ids

    async def track(self, link: str, videoid: Union[bool, str] = None):
        link = self._strip_extra(self._build_link(link, videoid))
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title        = result["title"]
            duration_min = result["duration"]
            vidid        = result["id"]
            yturl        = result["link"]
            thumbnail    = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title":        title,
            "link":         yturl,
            "vidid":        vidid,
            "duration_min": duration_min,
            "thumb":        thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        link = self._strip_extra(self._build_link(link, videoid))
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for fmt in r["formats"]:
                try:
                    if "dash" not in str(fmt["format"]).lower():
                        formats_available.append(
                            {
                                "format":      fmt["format"],
                                "filesize":    fmt.get("filesize"),
                                "format_id":   fmt["format_id"],
                                "ext":         fmt["ext"],
                                "format_note": fmt["format_note"],
                                "yturl":       link,
                            }
                        )
                except Exception:
                    continue
        return formats_available, link

    async def slider(
        self, link: str, query_type: int, videoid: Union[bool, str] = None
    ):
        link = self._strip_extra(self._build_link(link, videoid))
        a      = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title        = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid        = result[query_type]["id"]
        thumbnail    = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video:     Union[bool, str] = None,
        videoid:   Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title:     Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + link
        try:
            if video:
                downloaded_file = await download_video(link)
            else:
                downloaded_file = await download_song(link)
            if downloaded_file:
                return downloaded_file, True
            return None, False
        except Exception:
            return None, False
