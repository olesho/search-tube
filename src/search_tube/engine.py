from .storage import Storage
from pytube import YouTube
from pytubefix import YouTube

YOUTUBE_PREFIX = 'https://www.youtube.com/watch?v='

class Engine:
    def __init__(self, db_name, downaloads_dir) -> None:
        self.storage = Storage(db_name)
        self.output_dir = downaloads_dir 

    def load_urls(self, urls: list[str]) -> None:
        self.storage.save_urls(urls)
        self.process()
    
    def process(self):
        youtube_ids = self.storage.retrieve_urls(downloaded=False)
        for youtube_id in youtube_ids[:1]:
            # TODO: running only for first URL! to be continued...
            try:
                url = YOUTUBE_PREFIX + youtube_id
                yt = YouTube(url)
                self.storage.save_title(youtube_id, yt.title)
                ys = yt.streams.get_audio_only()
                filename = youtube_id + '.mp4'
                ys.download(output_path=self.output_dir, filename=filename)
                self.storage.make_url_downloaded(youtube_id)
                print("title:", yt.title, "downloaded")
            except Exception as e:
                print(f"Error downloading video: {e}")
                continue
            