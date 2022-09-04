# Spotify New Albums Bot

Update a Spotify Playlist to contain new released albums from a given set of countries new-releases feeds with filters for genre, artists, and playlist length.

---

### Setup

Export the following three environment variables and configure your Spotify app (on the management dashboard) to use that redirect URL. 
It does not actually need to be a publicly reachable URL but it does need to match what you use in the environment variable.
```
export SPOTIPY_CLIENT_ID=
export SPOTIPY_CLIENT_SECRET=
export SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
```

---

### Examples

```
python -m newalbums.update --help

usage: update.py [-h] [-y CONFIG] [-Y DUMP_CONFIG] [-p PLAYLIST] [-c [COUNTRY ...]] [-C N_PER_COUNTRY] [-g [LIMIT_GENRES ...]] [-G [EXCLUDE_GENRES ...]] [-a LIMIT_N_ALBUMS] [-t LIMIT_N_TRACKS] [-v] [-u]

Update a Spotify Playlist.

options:
  -h, --help            show this help message and exit
  -y CONFIG, --config CONFIG
                        YAML config file.
  -Y DUMP_CONFIG, --dump-config DUMP_CONFIG
                        Dump YAML config to file.
  -p PLAYLIST, --playlist PLAYLIST
                        Playlist ID or URI.
  -c [COUNTRY ...], --country [COUNTRY ...]
                        List of country codes.
  -C N_PER_COUNTRY, --n-per-country N_PER_COUNTRY
                        Number of new released albums to sample from each country code.
  -g [LIMIT_GENRES ...], --limit-genres [LIMIT_GENRES ...]
                        Filter albums to a specific list of genres.
  -G [EXCLUDE_GENRES ...], --exclude-genres [EXCLUDE_GENRES ...]
                        Filter albums to exclude a specific list of genres.
  -a LIMIT_N_ALBUMS, --limit-n-albums LIMIT_N_ALBUMS
                        Limit the playlist to the N most recent albums matching the other criteria. Default no limit.
  -t LIMIT_N_TRACKS, --limit-n-tracks LIMIT_N_TRACKS
                        Limit the playlist to the tracks from the N most recent albums matching the other criteria, rounded up to the nearest full album. Default no limit.
  -v, --verbose         Set the logging level.
  -u, --update          Apply the changes to the playlist.
```

```
python -m newalbums.update -p $NEW_ALBUMS_PLAYLIST_ID -c GB FR -a 10 -t 200 -v --update

2022-09-04 14:50:41,171 |       INFO | CONFIG | config: null
2022-09-04 14:50:41,172 |       INFO | CONFIG | country:
2022-09-04 14:50:41,172 |       INFO | CONFIG | - GB
2022-09-04 14:50:41,172 |       INFO | CONFIG | - FR
2022-09-04 14:50:41,172 |       INFO | CONFIG | dump_config: null
2022-09-04 14:50:41,172 |       INFO | CONFIG | exclude_genres: []
2022-09-04 14:50:41,172 |       INFO | CONFIG | limit_genres: []
2022-09-04 14:50:41,172 |       INFO | CONFIG | limit_n_albums: 10
2022-09-04 14:50:41,172 |       INFO | CONFIG | limit_n_tracks: 200
2022-09-04 14:50:41,172 |       INFO | CONFIG | n_per_country: 100
2022-09-04 14:50:41,172 |       INFO | CONFIG | playlist: scnalidvaefwq3
2022-09-04 14:50:41,172 |       INFO | CONFIG | update: 1
2022-09-04 14:50:41,172 |       INFO | CONFIG | verbose: 1
2022-09-04 14:50:41,172 |       INFO | Logging into Spotify using scope:
2022-09-04 14:50:41,172 |       INFO | SCOPES | - playlist-read-private
2022-09-04 14:50:41,172 |       INFO | SCOPES | - playlist-read-collaborative
2022-09-04 14:50:41,172 |       INFO | SCOPES | - playlist-modify-public
2022-09-04 14:50:41,172 |       INFO | SCOPES | - playlist-modify-private
2022-09-04 14:50:41,172 |       INFO | Login succeeded.
2022-09-04 14:50:41,172 |       INFO | From each country code, draw the 100 most recent albums that match the genre filters, and remove duplicates.
2022-09-04 14:50:41,172 |       INFO | Drop duplicated albums by album and artist name to avoid explicit vs radio edit duplicates.
2022-09-04 14:50:41,172 |       INFO | Sort albums by most recent release date.
2022-09-04 14:50:42,483 |       INFO | Fetch the tracks for each album.
2022-09-04 14:50:42,483 |       INFO | Filter the first 10 albums.
2022-09-04 14:50:42,483 |       INFO | Filter the first 200 tracks.
...
```