import re
import sqlite3

def remove_time_parameter(url):
    return re.sub(r"&t=\d+s", "", url)

class Storage():
    def __init__(self, db_name) -> None:
        try:
            self.db_name = db_name
            self.connection = sqlite3.connect(db_name, check_same_thread=False)
            self.create_urls_table()
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

    def create_urls_table(self):
        """Creates a table named 'urls' if it does not already exist."""
        try:
            with self.connection:
                self.connection.execute('''
                    CREATE TABLE IF NOT EXISTS urls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT NOT NULL UNIQUE
                    );
                ''')
        except Exception as e:
            print(f"Error creating table: {e}")
            raise

    def save_urls(self, url_list):
        """Inserts a list of URLs into the 'urls' table."""
        try:
            with self.connection:
                for u in url_list:
                    try:
                        trimmed_url = remove_time_parameter(u)
                        self.connection.execute('INSERT INTO urls (url) VALUES (?);', (trimmed_url,))
                    except sqlite3.IntegrityError:
                        print(f"URL '{trimmed_url}' is already in the database.")
                    except Exception as e:
                        print(f"Error inserting URL '{trimmed_url}': {e}")
        except Exception as e:
            print(f"Error in save_urls operation: {e}")
            raise

    def retrieve_urls(self):
        """Retrieves all URLs from the 'urls' table."""
        try:
            with self.connection:
                cursor = self.connection.execute('SELECT url FROM urls;')
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error retrieving URLs: {e}")
            raise

if __name__ == "__main__":
    # Example: testing functionality
    print("This module provides storage for search_tube.")