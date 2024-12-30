from .storage import Storage
from pytube import YouTube

SEARCH_TUBE_DB_NAME = "search_tube.db"

class Engine:
    def __init__(self) -> None:
        self.storage = Storage(SEARCH_TUBE_DB_NAME)

    def load_urls(self, urls: list[str]) -> None:
        self.storage.save_urls(urls)
        self.process()
    
    def process(self):
        urls = self.storage.retrieve_urls()
        for u in urls[:1]:
            # TODO: running only for first URL! to be continued...

            print("processing ", u)

            try:
                yt = YouTube(u)
                print("title:", yt.title)
            except Exception as e:
                print(f"Error downloading video: {e}")
                continue
            