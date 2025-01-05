import re
import sqlite3
import json
import threading

# remove_time_parameter removes time from Youtube URL
def remove_time_parameter(url):
    return re.sub(r"&t=\d+s", "", url)

CREATE_URLS_SCHEMA = """
    CREATE TABLE IF NOT EXISTS urls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        youtube_id TEXT NOT NULL UNIQUE,
        title TEXT DEFAULT NULL,
        keywords JSON DEFAULT NULL,
        downloaded BOOL NOT NULL DEFAULT False,
        transcribed BOOL NOT NULL DEFAULT False,
        rejected BOOL DEFAULT False,
        reject_reason TEXT DEFAULT NULL
    );"""

class Storage():
    def __init__(self, db_name) -> None:
        try:
            self.db_name = db_name
            self.lock = threading.Lock()
            self.connection = sqlite3.connect(db_name, check_same_thread=False)
            self.create_urls_table()
            self.log_level = 0
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

    def create_urls_table(self):
        """Creates a table named 'urls' if it does not already exist."""
        with self.lock:
            try:
                with self.connection:
                    cursor = self.connection.cursor()
                    cursor.execute(CREATE_URLS_SCHEMA)
            except Exception as e:
                print(f"Error creating table: {e}")
                raise

    def save_urls(self, url_list):
        """Inserts a list of URLs into the 'urls' table."""
        with self.lock:
            try:
                with self.connection:
                    cursor = self.connection.cursor()
                    for u in url_list:
                        try:
                            trimmed_url = remove_time_parameter(u).removeprefix('https://www.youtube.com/watch?v=') 
                            cursor.execute('INSERT INTO urls (youtube_id, title, downloaded, transcribed) VALUES (?, NULL, false, false);', (trimmed_url,))
                        except sqlite3.IntegrityError:
                            if self.log_level > 0:
                                print(f"URL '{trimmed_url}' is already in the database.")
                        except Exception as e:
                            print(f"Error inserting URL '{trimmed_url}': {e}")
            except Exception as e:
                print(f"Error in save_urls operation: {e}")
                raise


    def retrieve_url_to_get_metadata(self):
        """Retrieves URL which needs metadata."""
        with self.lock:
            try:
                with self.connection:
                    cursor = self.connection.cursor()
                    cursor.execute('SELECT youtube_id FROM urls WHERE title IS NULL AND keywords IS NULL LIMIT 1;')
                    return [row[0] for row in cursor.fetchall()]
            except Exception as e:
                print(f"Error retrieving URLs: {e}")
                raise

    def retrieve_url_to_download(self):
        """Retrieves URL from the 'urls' table to download."""
        with self.lock:
            try:
                with self.connection:
                    cursor = self.connection.cursor()
                    cursor.execute("""
                        SELECT * FROM urls 
                        WHERE title IS NOT NULL 
                            AND keywords IS NOT NULL 
                            AND rejected IS False 
                            AND downloaded IS False
                        LIMIT 1;""")
                    row = cursor.fetchone()
                    return {
                        'id': row[0],
                        'youtube_id': row[1],
                        'title': row[2], 
                        'keywords': row[3],
                        'downloaded': row[4],
                        'transcribed': row[5]
                    }
            except Exception as e:
                print(f"Error retrieving URLs: {e}")
                raise

    def retrieve_url(self, downloaded=False, transcribed=False):
        """Retrieves all URLs from the 'urls' table."""
        with self.lock:
            try:
                with self.connection:
                    cursor = self.connection.cursor()
                    cursor.execute('SELECT youtube_id FROM urls WHERE downloaded = ? AND transcribed = ? LIMIT 1;', (downloaded, transcribed,))
                    return [row[0] for row in cursor.fetchall()]
            except Exception as e:
                print(f"Error retrieving URLs: {e}")
                raise

    def save_metadata(self, youtube_id, title, keywords):
        """Updates the title for a given YouTube ID.
        
        Args:
            youtube_id (str): The YouTube video ID to update
            title (str): The title to save for the video
            
        Raises:
            Exception: If there's an error updating the database
        """
        with self.lock:
            try:
                with self.connection:
                    cursor = self.connection.cursor()
                    cursor.execute(
                        'UPDATE urls SET title = ?, keywords = ? WHERE youtube_id = ?;',
                        (title, json.dumps(keywords), youtube_id)
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
        with self.lock:
            try:
                with self.connection:
                    cursor = self.connection.cursor()
                    cursor.execute(
                        'UPDATE urls SET downloaded = true WHERE youtube_id = ?;',
                        (youtube_id,)
                    )
            except Exception as e:
                print(f"Error updating downloaded status for {youtube_id}: {e}")
                raise

    def make_url_transcribed(self, youtube_id):
        """Updates the transcribed status to True for a given YouTube ID.
        
        Args:
            youtube_id (str): The YouTube video ID to update
            
        Raises:
            Exception: If there's an error updating the database
        """
        with self.lock:
            try:
                with self.connection:
                    cursor = self.connection.cursor()
                    cursor.execute(
                        'UPDATE urls SET transcribed = true WHERE youtube_id = ?;',
                        (youtube_id,)
                    )
            except Exception as e:
                print(f"Error updating downloaded status for {youtube_id}: {e}")
                raise    

    def make_url_rejected(self, youtube_id, reason: str):
        """Updates the rejected status to True for a given YouTube ID.
        
        Args:
            youtube_id (str): The YouTube video ID to update
            reason (str): Reason for rejection
            
        Raises:
            Exception: If there's an error updating the database
        """
        with self.lock:
            try:
                with self.connection:
                    cursor = self.connection.cursor()
                    cursor.execute(
                        'UPDATE urls SET rejected = true, reject_reason = ? WHERE youtube_id = ?;',
                        (reason, youtube_id, )
                    )
            except Exception as e:
                print(f"Error updating downloaded status for {youtube_id}: {e}")
                raise    

if __name__ == "__main__":
    # Example: testing functionality
    print("This module provides storage for search_tube.")