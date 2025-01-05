from .storage import Storage
from pytube import YouTube
from pytubefix import YouTube
import asyncio
import threading
from pytubefix.cli import on_progress

YOUTUBE_PREFIX = 'https://www.youtube.com/watch?v='

class Engine:
    def __init__(self, db_name, downloads_dir) -> None:
        self.download_timeout = 20  # sleep timeout between downloads
        self.storage = Storage(db_name)
        self.output_dir = downloads_dir
        
        # Create event loop in a separate thread
        self.loop = asyncio.new_event_loop()
        self.download_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.download_thread.start()

    def _run_async_loop(self):
        """Sets up and runs the async event loop in a separate thread"""
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.downloads_job())
        self.loop.run_forever()

    def load_urls(self, urls: list[str]) -> None:
        urls = [u for u in urls if u.startswith(YOUTUBE_PREFIX)]  # this filters out shorts
        self.storage.save_urls(urls)

    async def downloads_job(self):
        """Asynchronous job that handles downloading videos"""
        while True:
            await self.download_next()
            await asyncio.sleep(self.download_timeout)

    async def download_next(self):
        """Asynchronous method to download the next video"""
        youtube_ids = self.storage.retrieve_url(downloaded=False)
        if len(youtube_ids) < 1:
            return

        youtube_id = youtube_ids[0]
        try:
            url = YOUTUBE_PREFIX + youtube_id
            # Run YouTube operations in a thread pool since they're blocking
            yt = await asyncio.to_thread(YouTube, url, on_complete_callback=self.completed_callback)
            await asyncio.to_thread(self.storage.save_title, youtube_id, yt.title)
            
            ys = await asyncio.to_thread(lambda: yt.streams.get_audio_only())
            filename = youtube_id + '.mp4'

            await asyncio.to_thread(
                ys.download,
                output_path=self.output_dir,
                filename=filename
            )
            print(yt.title, "downloaded")

        except Exception as e:
            print(f"Error downloading video: {e}")

    def completed_callback(self, stream, file_path):
        youtube_id = file_path.split('/')[-1].replace('.mp4', '')
        self.storage.make_url_downloaded(youtube_id)

    def __del__(self):
        """Cleanup method to stop the event loop when the Engine is destroyed"""
        if hasattr(self, 'loop') and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.download_thread.join(timeout=1.0)