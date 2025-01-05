import re
import sqlite3

# remove_time_parameter removes time from Youtube URL
def remove_time_parameter(url):
    return re.sub(r"&t=\d+s", "", url)

CREATE_URLS_SCHEMA = """
    CREATE TABLE IF NOT EXISTS urls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        youtube_id TEXT NOT NULL UNIQUE,
        title TEXT,
        downloaded BOOL NOT NULL,
        transcribed BOOL NOT NULL
    );"""

class Storage():
    def __init__(self, db_name) -> None:
        try:
            self.db_name = db_name
            self.connection = sqlite3.connect(db_name, check_same_thread=False)
            self.create_urls_table()
            self.log_level = 0
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

    def create_urls_table(self):
        """Creates a table named 'urls' if it does not already exist."""
        try:
            with self.connection:
                self.connection.execute(CREATE_URLS_SCHEMA)
        except Exception as e:
            print(f"Error creating table: {e}")
            raise

    def save_urls(self, url_list):
        """Inserts a list of URLs into the 'urls' table."""
        try:
            with self.connection:
                for u in url_list:
                    try:
                        trimmed_url = remove_time_parameter(u).removeprefix('https://www.youtube.com/watch?v=') 
                        self.connection.execute('INSERT INTO urls (youtube_id, title, downloaded, transcribed) VALUES (?, NULL, false, false);', (trimmed_url,))
                    except sqlite3.IntegrityError:
                        if self.log_level > 0:
                            print(f"URL '{trimmed_url}' is already in the database.")
                    except Exception as e:
                        print(f"Error inserting URL '{trimmed_url}': {e}")
        except Exception as e:
            print(f"Error in save_urls operation: {e}")
            raise

    def retrieve_url(self, downloaded=False):
        """Retrieves all URLs from the 'urls' table."""
        try:
            with self.connection:
                cursor = self.connection.execute('SELECT youtube_id FROM urls WHERE downloaded = ? LIMIT 1;', (downloaded,))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error retrieving URLs: {e}")
            raise

    def save_title(self, youtube_id, title):
        """Updates the title for a given YouTube ID.
        
        Args:
            youtube_id (str): The YouTube video ID to update
            title (str): The title to save for the video
            
        Raises:
            Exception: If there's an error updating the database
        """
        try:
            with self.connection:
                self.connection.execute(
                    'UPDATE urls SET title = ? WHERE youtube_id = ?;',
                    (title, youtube_id)
                )
        except Exception as e:
            print(f"Error updating title for {youtube_id}: {e}")
            raise

    def make_url_downloaded(self, youtube_id):
        """Updates the downloaded status to True for a given YouTube ID.
        
        Args:
            youtube_id (str): The YouTube video ID to update
            
        Raises:
            Exception: If there's an error updating the database
        """
        try:
            with self.connection:
                self.connection.execute(
                    'UPDATE urls SET downloaded = true WHERE youtube_id = ?;',
                    (youtube_id,)
                )
        except Exception as e:
            print(f"Error updating downloaded status for {youtube_id}: {e}")
            raise

if __name__ == "__main__":
    # Example: testing functionality
    print("This module provides storage for search_tube.")