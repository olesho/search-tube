# search-tube
A research project fot transcribing YouTube videos history.


## Running the server

### Using Anaconda
```bash
conda create -n search-tube python=3.10
conda activate search-tube
```

### Using Docker
```bash
docker build -t search-tube .
docker run -p 5000:5000 search-tube
```

## Fetching Youtube History URLs
To retrieve URL history open browser console at https://www.youtube.com/feed/history and copy/pasete following code:

```javascript
(async () => {
    // Step 1: Retrieve the list of URLs
    const elements = document.querySelectorAll('div[id=title-wrapper]>h3>a[id=video-title]');
    const urls = Array.from(elements).map(el => el.href);

    // Step 2: Encode data as URL-encoded string
    const urlEncodedData = `urls=${encodeURIComponent(JSON.stringify(urls))}`;

    // Step 3: Send POST request without triggering preflight
    const sendData = async (url, data) => {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded', // Avoid preflight
                },
                body: data
            });
            if (response.ok) {
                console.log('Data sent successfully');
            } else {
                console.error('Failed to send data:', response.statusText);
            }
        } catch (error) {
            console.error('Error during POST request:', error);
        }
    };

    // Step 4: Call the API
    const apiUrl = 'http://localhost:5555';
    await sendData(apiUrl, urlEncodedData);
})();
```