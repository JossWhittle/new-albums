import argparse, yaml
parser = argparse.ArgumentParser(description='Update a Spotify Playlist.')

parser.add_argument('-y', '--config', required=False, default=None, type=str,
                    help='YAML config file.')
parser.add_argument('-Y', '--dump-config', required=False, default=None, type=str,
                    help='Dump YAML config to file.')
parser.add_argument('-p', '--playlist', required=False, default=None, type=str,
                    help='Playlist ID or URI.')
parser.add_argument('-c', '--country', default=[None], nargs='*',
                    help='List of country codes.')
parser.add_argument('-C', '--n-per-country', default=100, type=int,
                    help='Number of new released albums to sample from each country code.')
parser.add_argument('-g', '--limit-genres', default=[], nargs='*',
                    help='Filter albums to a specific list of genres.')
parser.add_argument('-G', '--exclude-genres', default=[], nargs='*',
                    help='Filter albums to exclude a specific list of genres.')
parser.add_argument('-a', '--limit-n-albums', default=0, type=int,
                    help='Limit the playlist to the N most recent albums matching the other criteria. Default no limit.')
parser.add_argument('-t', '--limit-n-tracks', default=0, type=int,
                    help='Limit the playlist to the tracks from the N most recent albums matching the other criteria, rounded up to the nearest full album. Default no limit.')
parser.add_argument('-v', '--verbose', action='count', default=0,
                    help='Set the logging level.')
parser.add_argument('-u', '--update', action='count', default=0,
                    help='Apply the changes to the playlist.')

args = vars(parser.parse_args())

if args['config'] is not None:
    with open(args['config'], 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        args = config | args

import sys, logging

# Create a unique logger for this SLURM job for this MPI rank
logging.getLogger().handlers.clear()
logger = logging.getLogger('update')
logger.setLevel(logging.DEBUG if (args['verbose'] > 0) else logging.INFO)
logger.handlers.clear()

# Format the logging to include the SLURM job and MPI ranks
formatter = logging.Formatter('%(asctime)s | %(levelname)10s | %(message)s')

# Mirror logging to stdout
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)

if args['playlist'] is None:
    logger.error('CLI aguments or YAML config file must contain a playlist ID or URI.')
    sys.exit(1)

import itertools, more_itertools
from datetime import datetime
from tqdm import tqdm

import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Debug the config
for line in yaml.dump(args, indent=4).splitlines():
    logger.info(f'CONFIG | {line}')

# Dump the config to YAML
if args['dump_config'] is not None:
    with open(args['dump_config'], 'w') as f:
        f.write(yaml.dump(args, indent=4))

# Authenticate against Spotify
scope = ['playlist-read-private', 'playlist-read-collaborative', 'playlist-modify-public', 'playlist-modify-private']
logger.info('Logging into Spotify using scope:')
for line in yaml.dump(scope, indent=4).splitlines():
    logger.info(f'SCOPES | {line}')
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, open_browser=False))
logger.info('Login succeeded.')

def new_releases_by_country(country, chunk=50):
    for offset in itertools.count(step=chunk):
        albums = sp.new_releases(country=country, limit=chunk, offset=offset)["albums"]["items"]
        yield from albums
        if len(albums) < chunk:
            return

def album_tracks(album_id, chunk=50):
    for offset in itertools.count(step=chunk):
        tracks = sp.album_tracks(album_id, limit=chunk, offset=offset)['items']
        yield from tracks
        if len(tracks) < chunk:
            return

def playlist_tracks(playlist_id, chunk=50):
    for offset in itertools.count(step=chunk):
        tracks = sp.playlist_items(playlist_id, limit=chunk, offset=offset)['items']
        yield from tracks
        if len(tracks) < chunk:
            return

def unique(it, key=(lambda x: x.id)):
    seen = set()
    for obj in it:
        k = key(obj)
        if k not in seen:
            seen.add(k)
            yield obj

def take(it, n):
    try:
        for _ in range(n):
            yield next(it)
    except StopIteration:
        pass

def take_tracks(it, n):
    try:
        count = 0
        for album in it:
            yield album
            count += len(album['tracks'])
            if count >= n:
                return
    except StopIteration:
        pass

def genres_from_artists(artists):
    return list(unique(itertools.chain.from_iterable(
                map(lambda artist: artist['genres'],
                    sp.artists(list(map(lambda artist: artist['uri'], artists)))['artists'])),
                key=lambda genre: genre))

def filter_limit_genres(it, genres):
    if len(genres) == 0:
        yield from it

    def fn(album):
        album_genres = list(genres_from_artists(album['artists']))
        return any(map(lambda genre: (genre in album_genres), genres))
    yield from filter(fn, it)

def filter_exclude_genres(it, genres):
    if len(genres) == 0:
        yield from it

    def fn(album):
        album_genres = list(genres_from_artists(album['artists']))
        return not any(map(lambda genre: (genre in album_genres), genres))
    yield from filter(fn, it)

# Drop duplicates from country codes
logger.info('From each country code, draw the {n_per_country} most recent albums that match the genre filters, '
            'and remove duplicates.'.format(**args))
new_releases = unique(itertools.chain.from_iterable(
    map(lambda country: take(
        filter_exclude_genres(
            filter_limit_genres(
                filter(lambda album: album['album_type'] == 'album',
                       new_releases_by_country(country)),
                args['limit_genres']),
            args['exclude_genres']),
        n=args['n_per_country']),
        args['country'])),
    key=lambda x: x['uri'])

# Filter unique albums by name and artist to avoid explicit duplicates
logger.info('Drop duplicated albums by album and artist name to avoid explicit vs radio edit duplicates.')
new_releases = unique(new_releases, key=lambda album: album['name']+'|'+','.join(map(lambda x: x['name'], album['artists'])))

# Sort by release date
logger.info('Sort albums by most recent release date.')
new_releases = sorted(new_releases, key=lambda album: datetime.strptime(album['release_date'], '%Y-%m-%d'), reverse=True)

# Fetch the tracks for each album
logger.info('Fetch the tracks for each album.')
new_releases = iter(album | { 'tracks': list(album_tracks(album['uri'])) } for album in new_releases)

# Filter the number of albums
if args['limit_n_albums'] > 0:
    logger.info('Filter the first {limit_n_albums} albums.'.format(**args))
    new_releases = take(new_releases, args['limit_n_albums'])

# Filter the number of tracks
if args['limit_n_tracks'] > 0:
    logger.info('Filter the first {limit_n_tracks} tracks.'.format(**args))
    new_releases = take_tracks(new_releases, args['limit_n_tracks'])

new_releases = list(new_releases)

# Log albums to be added to playlist
for line in ['-'*50] + yaml.dump([{
    'album': album['name'],
    'release_date': album['release_date'],
    'artists': list(map(lambda artist: artist['name'], album['artists'])),
    'tracks': [ track['name'] for track in album['tracks']] } |
    ({ 'genres': genres_from_artists(album['artists'])} if args['verbose'] > 0 else {})
    for album in new_releases], indent=4).splitlines():
    logger.info(f'ALBUM | {line}')

# Clear playlist
chunks = list(playlist_tracks(args['playlist']))
if args['verbose'] == 0:
    chunks = tqdm(list(chunks), desc='Removing from playlist')
if args['update'] > 0:
    for chunk in more_itertools.chunked(chunks, 100):
        if args['verbose'] > 0:
            for line in ['-' * 50] + yaml.dump([track['track']['name'] for track in chunk], indent=4).splitlines():
                logger.debug(f'REMOVING from playlist | {line}')
        sp.playlist_remove_all_occurrences_of_items(
            args['playlist'], items=list(map(lambda track: track['track']['uri'], chunk)))

else:
    logger.info('Not updating playlist. Run again with -u --update to alter the playlist.')

# Flatten all album tracks
tracks = list(itertools.chain.from_iterable(
    map(lambda track: track | { 'album': album }, album['tracks']) for album in new_releases))

# Add tracks to playlist
chunks = tracks if args['verbose'] > 0 else tqdm(tracks, desc='Adding to playlist')
if args['update'] > 0:
    for chunk in more_itertools.chunked(chunks, 100):
        if args['verbose'] > 0:
            for line in ['-' * 50] + yaml.dump([track['name'] for track in chunk], indent=4).splitlines():
                logger.debug(f'ADDING to playlist | {line}')
        sp.playlist_add_items(
            args['playlist'], items=list(map(lambda track: track['uri'], chunk)))

