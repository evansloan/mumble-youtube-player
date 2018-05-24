# mumble-youtube-player
A simple Mumble bot that takes song requests in the form of YouTube video names/URLs and plays them back through Mumble.

Use `!request <song name/video URL>` to request a song.

**Requirements**:
 - Python >= 3.6.0
 - FFMPEG

**Clone the repo**:
```git clone https://github.com/evansloan082/mumble-youtube-player.git ```

**Install requirements**:
```pip install -r requirements.txt```

This project makes use of Google's YouTube data API and requires service account credentials in order to authenticate. More information on creating your own service account can be found [here](https://developers.google.com/identity/protocols/OAuth2ServiceAccount#creatinganaccount).

Replace `config/service_client.json` with your own service account credentials. (Make sure the file is still named `service_client.json`)

Modify `config/config.ini` to connect to the Mumble server of your choosing.

[*Optional*] Replace `config/certfile.pem` with your own Mumble certificate if you would like to authenticate the bot.

**Run the bot**:
```python main.py```