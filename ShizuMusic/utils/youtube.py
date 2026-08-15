 # --------------------------------------------------------------------------------
#  ShizuMusic © 2026
#  Developed by Bad Munda ❤️
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

DOWNLOAD_DIR = "downloads"
_file_cache: dict[str, str] = {}


def _extract_video_id(url: str) -> str:
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return url


def time_to_seconds(time) -> int:
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


async def _native_ytdlp_download(video_id: str, is_video: bool = False) -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ext = "mp4" if is_video else "mp3"
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    cookie_file = None
    possible_paths = [
        "/home/ubuntu/ShizuMusic/cookies.txt",
        "cookies.txt",
        "/home/ubuntu/cookies.txt",
    ]
    for cp in possible_paths:
        if os.path.exists(cp) and os.path.getsize(cp) > 0:
            cookie_file = cp
            break

    ydl_opts = {
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]" if is_video else "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "mweb"],
                "player_skip": ["webpage", "configs"],
            }
        },
    }

    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file

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
            if f.startswith(video_id) and os.path.getsize(os.path.join(DOWNLOAD_DIR, f)) > 0:
                return os.path.join(DOWNLOAD_DIR, f)
    except Exception as e:
        logger.error(f"[Download Error] {e}")

    return None


async def download_song(link: str) -> str:
    video_id = _extract_video_id(link)
    if not video_id or len(video_id) < 3:
        return None
    return await _native_ytdlp_download(video_id, is_video=False)


async def download_video(link: str) -> str:
    video_id = _extract_video_id(link)
    if not video_id or len(video_id) < 3:
        return None
    return await _native_ytdlp_download(video_id, is_video=True)


async def resolve_stream(url: str, video: bool = False) -> str:
    if os.path.exists(url) and os.path.isfile(url):
        return url

    cache_key = f"{url}_video" if video else url
    if cache_key in _file_cache and os.path.exists(_file_cache[cache_key]):
        return _file_cache[cache_key]

    video_id = _extract_video_id(url)
    ext = "mp4" if video else "mp3"
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        _file_cache[cache_key] = file_path
        return file_path

    downloaded = await download_video(url) if video else await download_song(url)
    if downloaded:
        _file_cache[cache_key] = downloaded
        return downloaded

    raise Exception("ᴅᴏᴡɴʟᴏᴀᴅ ғᴀɪʟᴇᴅ. ᴩʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.")


async def search_yt(query: str):
    if "playlist?list=" in query or "&list=" in query:
        pl = await Playlist.get(query)
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
            thumb = thumbs[0].get("url", "").split("?")[0] if thumbs else ""
            items.append({
                "link": f"https://www.youtube.com/watch?v={v['id']}",
                "title": v.get("title", "Unknown"),
                "duration": sec_to_iso(secs),
                "thumbnail": thumb,
            })
        return {"playlist": items}

    search = VideosSearch(query, limit=1)
    results = await search.next()
    lst = results.get("result", [])
    if not lst:
        raise Exception("ɴᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ")

    r = lst[0]
    url = r.get("link") or f"https://www.youtube.com/watch?v={r['id']}"
    title = r.get("title", "Unknown")
    thumb = (r.get("thumbnails") or [{}])[0].get("url", "").split("?")[0]
    dur = r.get("duration") or "0:00"

    parts = [int(x) for x in dur.split(":")]
    secs = (
        parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 3
        else parts[0] * 60 + parts[1]
    )
    return (url, title, sec_to_iso(secs), thumb)


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

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
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
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
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
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
                                "format": fmt["format"],
                                "filesize": fmt.get("filesize"),
                                "format_id": fmt["format_id"],
                                "ext": fmt["ext"],
                                "format_note": fmt["format_note"],
                                "yturl": link,
                            }
                        )
                except Exception:
                    continue
        return formats_available, link

    async def slider(
        self, link: str, query_type: int, videoid: Union[bool, str] = None
    ):
        link = self._strip_extra(self._build_link(link, videoid))
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
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
