from typing import List, Optional, Callable, Dict, Tuple
from pathlib import Path
import asyncio
import threading
from pytubefix import YouTube
import whisper
from .storage import Storage

class MetadataFetcher:
    YOUTUBE_PREFIX = 'https://www.youtube.com/watch?v='

    def __init__(self, storage: Storage) -> None:
        self.storage = storage
        self.fetch_timeout = 20
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.fetch_thread: Optional[threading.Thread] = None
        self._start_async_loop()

    def _start_async_loop(self) -> None:
        """Sets up and starts the async event loop in a separate thread"""
        self.loop = asyncio.new_event_loop()
        self.fetch_thread = threading.Thread(
            target=self._run_async_loop,
            daemon=True
        )
        self.fetch_thread.start()

    def _run_async_loop(self) -> None:
        """Runs the async event loop"""
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.metadata_job())
        self.loop.run_forever()

    async def metadata_job(self) -> None:
        """Continuous job that handles fetching metadata"""
        while True:
            try:
                await self.fetch_next_metadata()
            except Exception as e:
                print(f"Error in metadata job: {e}")
            await asyncio.sleep(self.fetch_timeout)

    async def fetch_next_metadata(self) -> None:
        """Fetch metadata for the next available video"""
        youtube_ids = self.storage.retrieve_url_to_get_metadata()
        if not youtube_ids:
            return

        youtube_id = youtube_ids[0]
        url = f"{self.YOUTUBE_PREFIX}{youtube_id}"

        try:
            yt = await asyncio.to_thread(YouTube, url)
            
            metadata = {
                'title': yt.title,
                'keywords': yt.keywords
            }
            
            await asyncio.to_thread(
                self.storage.save_metadata,
                youtube_id,
                metadata['title'],
                metadata['keywords']
            )
            
            print(f"Fetched metadata for {metadata['title']}")

        except Exception as e:
            print(f"Error fetching metadata for video {youtube_id}: {e}")

    def __del__(self) -> None:
        """Cleanup method to stop the event loop"""
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.fetch_thread:
            self.fetch_thread.join(timeout=1.0)


class YouTubeDownloader:
    YOUTUBE_PREFIX = 'https://www.youtube.com/watch?v='
    FILTER_KEYWORDS = [
        'chill beats', 'chill beats records', 'chill', 'beats', 'study beats',
        'lofi', 'lo-fi beats', 'lo-fi', 'lofihiphop', 'chillhop', 'mellowbeats',
        'chillbeats', 'lofibeats', 'chill beats music', 'lofihophop',
        'instrumental', 'studybeats', 'crazzyjazz', 'Hippie', 'Sabotage', 'Hippie Sabotage', 'billie eilish',
        "Lofi Sleep Chill & Study", "Lofi Hip-Hop Beats", "LO-FI Beats", "LoFi Study Vibes", "Jazz Cafe LoFi",
        "tik tok", "tik tok song"
    ]

    def __init__(self, storage: Storage, downloads_dir: Path, do_download: bool = False) -> None:
        self.storage = storage
        self.downloads_dir = Path(downloads_dir)
        self.do_download = do_download
        self.download_timeout = 40
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.download_thread: Optional[threading.Thread] = None
        self._start_async_loop()

    def _start_async_loop(self) -> None:
        """Sets up and starts the async event loop in a separate thread"""
        self.loop = asyncio.new_event_loop()
        self.download_thread = threading.Thread(
            target=self._run_async_loop,
            daemon=True
        )
        self.download_thread.start()

    def _run_async_loop(self) -> None:
        """Runs the async event loop"""
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.downloads_job())
        self.loop.run_forever()

    async def downloads_job(self) -> None:
        """Continuous job that handles downloading videos"""
        while True:
            try:
                await self.download_next()
            except Exception as e:
                print(f"Error in downloads job: {e}")
            await asyncio.sleep(self.download_timeout)

    async def download_next(self) -> None:
        """Download the next available video"""
        youtube_ids = self.storage.retrieve_url_to_download()
        if not youtube_ids:
            return

        youtube_id = youtube_ids[0]
        url = f"{self.YOUTUBE_PREFIX}{youtube_id}"

        try:
            yt = await asyncio.to_thread(
                YouTube,
                url,
                on_complete_callback=self._completed_callback
            )

            if not self.do_download:
                return

            # Get keywords from storage instead of fetching again
            keywords = self.storage.get_video_keywords(youtube_id)
            if any(keyword in self.FILTER_KEYWORDS for keyword in keywords):
                return

            stream = await asyncio.to_thread(
                lambda: yt.streams.get_audio_only()
            )

            filename = f"{youtube_id}.mp4"
            await asyncio.to_thread(
                stream.download,
                output_path=str(self.downloads_dir),
                filename=filename
            )
            print(f"{yt.title} downloaded")

        except Exception as e:
            print(f"Error downloading video {youtube_id}: {e}")

    def _completed_callback(self, stream, file_path: str) -> None:
        """Handle successful download completion"""
        youtube_id = Path(file_path).stem
        self.storage.make_url_downloaded(youtube_id)

    def __del__(self) -> None:
        """Cleanup method to stop the event loop"""
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.download_thread:
            self.download_thread.join(timeout=1.0)


class Transcriber:
    def __init__(self, storage: Storage, downloads_dir: Path, transcribes_dir: Path) -> None:
        self.storage = storage
        self.downloads_dir = Path(downloads_dir)
        self.transcribes_dir = Path(transcribes_dir)
        self.transcriber_model = whisper.load_model("small")
        self.transcribe_thread: Optional[threading.Thread] = None
        self._start_async_loop()

    def _start_async_loop(self) -> None:
        """Sets up and starts the async event loop in a separate thread"""
        self.transcribe_thread = threading.Thread(
            target=self._run_transcribe_loop,
            daemon=True
        )
        self.transcribe_thread.start()

    def _run_transcribe_loop(self) -> None:
        """Runs the async event loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(self.transcribe_job())
        loop.run_forever()

    async def transcribe_job(self) -> None:
        """Continuous job that handles transcribing videos"""
        while True:
            try:
                await self.transcribe_next()
            except Exception as e:
                print(f"Error in transcribing job: {e}")

    async def transcribe_next(self) -> None:
        """Transcribe the next available video"""
        youtube_ids = self.storage.retrieve_url(downloaded=True, transcribed=False)
        if not youtube_ids:
            return

        youtube_id = youtube_ids[0]
        input_file = self.downloads_dir / f"{youtube_id}.mp4"
        output_file = self.transcribes_dir / f"{youtube_id}.txt"

        try:
            output = await asyncio.to_thread(
                self.transcriber_model.transcribe,
                str(input_file),
                fp16=False
            )

            await asyncio.to_thread(
                self._write_transcription,
                output_file,
                output["text"]
            )

            await asyncio.to_thread(
                self.storage.make_url_transcribed,
                youtube_id
            )

            print(f"Transcribed {youtube_id}")

        except Exception as e:
            print(f"Error transcribing video {youtube_id}: {e}")

    def _write_transcription(self, output_file: Path, text: str) -> None:
        """Helper method to write transcription to file"""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)

    def __del__(self) -> None:
        """Cleanup method to stop the thread"""
        if self.transcribe_thread:
            self.transcribe_thread.join(timeout=1.0)


class Engine:
    def __init__(self, db_name: str, downloads_dir: Path, transcribes_dir: Path, do_download: bool = False) -> None:
        self.storage = Storage(db_name)
        self.metadata_fetcher = MetadataFetcher(self.storage)
        self.downloader = YouTubeDownloader(self.storage, downloads_dir, do_download)
        self.transcriber = Transcriber(self.storage, downloads_dir, transcribes_dir)

    def load_urls(self, urls: List[str]) -> None:
        """Filter and save valid YouTube URLs"""
        valid_urls = [
            url for url in urls
            if url.startswith(YouTubeDownloader.YOUTUBE_PREFIX)
        ]
        self.storage.save_urls(valid_urls)