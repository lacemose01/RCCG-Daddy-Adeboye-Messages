# Grace Radio playlist

Edit `Playlist.xlsx` and upload the updated file to this repository to change the station. The first worksheet must have `Title` and `Cloudinary Url` headers, with one recording per row in playback order. An optional `Speaker` column can name the speaker or artist. Only use recordings you have permission to broadcast. The repository and links are public; do not include passwords or API secrets.

The publishing workflow measures the duration of new audio URLs and generates `playlist.json` for GitHub Pages. It keeps existing schedules intact and schedules each changed workbook at the end of the latest playlist cycle, at least five minutes after generation. If an update is already waiting, another update is queued after that scheduled playlist has played once. Long playlists therefore mean a longer wait. Publishing or network delays, offline listeners, and inaccurate device clocks can cause listeners to switch late.

Use a new Cloudinary URL when replacing a recording; the workflow reuses the measured duration for URLs already in `station-playlist.json`. Duplicate URLs are allowed and will be played more than once.

`station-playlist.json` is generated schedule state. Do not edit or delete it: it preserves timing for listeners and pending updates. If publishing fails, check the **Actions** tab and rerun the failed workflow after fixing the reported problem. The workflow needs permission to write repository contents as well as deploy GitHub Pages.

The app must be built with `VITE_PLAYLIST_URL` set to the published GitHub Pages `playlist.json` URL. Uploading the workbook does not itself deploy or configure the app.
