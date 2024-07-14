import json
from typing import Iterable

from app.db.sqlite.artistcolors import SQLiteArtistMethods as ardb
from app.lib.tagger import create_artists
from app.models import Artist
from app.utils.bisection import use_bisection
from app.utils.customlist import CustomList
from app.utils.progressbar import tqdm
from .tracks import TrackStore

# from .albums import AlbumStore
from .tracks import TrackStore

ARTIST_LOAD_KEY = ""


class ArtistMapEntry:
    def __init__(self, artist: Artist) -> None:
        self.artist = artist
        self.albumhashes: set[str] = set()
        self.trackhashes: set[str] = set()


class ArtistStore:
    artists: list[Artist] = CustomList()
    artistmap: dict[str, ArtistMapEntry] = {}

    @classmethod
    def load_artists(cls, instance_key: str):
        """
        Loads all artists from the database into the store.
        """
        global ARTIST_LOAD_KEY
        ARTIST_LOAD_KEY = instance_key

        print("Loading artists... ", end="")
        cls.artistmap.clear()

        cls.artistmap = {
            artist.artisthash: ArtistMapEntry(artist=artist)
            for artist in create_artists()
        }

        for track in TrackStore.get_flat_list():
            if instance_key != ARTIST_LOAD_KEY:
                return

            for hash in track.artisthashes:
                cls.artistmap[hash].trackhashes.add(track.trackhash)
                cls.artistmap[hash].albumhashes.add(track.albumhash)

        print("Done!")
        # for artist in ardb.get_all_artists():
        #     if instance_key != ARTIST_LOAD_KEY:
        #         return

        #     cls.map_artist_color(artist)

    @classmethod
    def map_artist_color(cls, artist_tuple: tuple):
        """
        Maps a color to the corresponding artist.
        """

        artisthash = artist_tuple[1]
        color = json.loads(artist_tuple[2])

        for artist in cls.artists:
            if artist.artisthash == artisthash:
                artist.set_colors(color)
                break

    @classmethod
    def add_artist(cls, artist: Artist):
        """
        Adds an artist to the store.
        """
        cls.artists.append(artist)

    @classmethod
    def add_artists(cls, artists: list[Artist]):
        """
        Adds multiple artists to the store.
        """
        for artist in artists:
            if artist not in cls.artists:
                cls.artists.append(artist)

    @classmethod
    def get_artist_by_hash(cls, artisthash: str):
        """
        Returns an artist by its hash.P
        """
        entry = cls.artistmap.get(artisthash, None)
        if entry is not None:
            return entry.artist

    @classmethod
    def get_artists_by_hashes(cls, artisthashes: Iterable[str]):
        """
        Returns artists by their hashes.
        """
        artists = [cls.get_artist_by_hash(hash) for hash in artisthashes]
        return [a for a in artists if a is not None]

    @classmethod
    def artist_exists(cls, artisthash: str) -> bool:
        """
        Checks if an artist exists.
        """
        return artisthash in "-".join([a.artisthash for a in cls.artists])

    @classmethod
    def artist_has_tracks(cls, artisthash: str) -> bool:
        """
        Checks if an artist has tracks.
        """
        artists: set[str] = set()

        for track in TrackStore.tracks:
            artists.update(track.artist_hashes)
            album_artists: list[str] = [a.artisthash for a in track.albumartists]
            artists.update(album_artists)

        master_hash = "-".join(artists)
        return artisthash in master_hash

    @classmethod
    def remove_artist_by_hash(cls, artisthash: str):
        """
        Removes an artist from the store.
        """
        cls.artists = CustomList(a for a in cls.artists if a.artisthash != artisthash)

    @classmethod
    def get_artist_tracks(cls, artisthash: str):
        """
        Returns all tracks by the given artist hash.
        """
        entry = cls.artistmap.get(artisthash)
        if entry is not None:
            return TrackStore.get_tracks_by_trackhashes(entry.trackhashes)

        return []
