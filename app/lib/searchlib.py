"""
This library contains all the functions related to the search functionality.
"""
from typing import List, Generator, TypeVar, Any
import itertools

from rapidfuzz import fuzz, process
from unidecode import unidecode

from app import models
from app.db.store import Store
from app.utils.remove_duplicates import remove_duplicates

ratio = fuzz.ratio
wratio = fuzz.WRatio


class Cutoff:
    """
    Holds all the default cutoff values.
    """

    tracks: int = 90
    albums: int = 90
    artists: int = 90
    playlists: int = 90


class Limit:
    """
    Holds all the default limit values.
    """

    tracks: int = 150
    albums: int = 150
    artists: int = 150
    playlists: int = 150


class SearchTracks:
    def __init__(self, query: str) -> None:
        self.query = query
        self.tracks = Store.tracks

    def __call__(self) -> List[models.Track]:
        """
        Gets all songs with a given title.
        """

        track_titles = [unidecode(track.og_title).lower() for track in self.tracks]
        results = process.extract(
            self.query,
            track_titles,
            scorer=fuzz.WRatio,
            score_cutoff=Cutoff.tracks,
            limit=Limit.tracks,
        )

        tracks = [self.tracks[i[2]] for i in results]
        return remove_duplicates(tracks)


class SearchArtists:
    def __init__(self, query: str) -> None:
        self.query = query
        self.artists = Store.artists

    def __call__(self) -> list:
        """
        Gets all artists with a given name.
        """
        artists = [unidecode(a.name).lower() for a in self.artists]

        results = process.extract(
            self.query,
            artists,
            scorer=fuzz.WRatio,
            score_cutoff=Cutoff.artists,
            limit=Limit.artists,
        )

        return [self.artists[i[2]] for i in results]


class SearchAlbums:
    def __init__(self, query: str) -> None:
        self.query = query
        self.albums = Store.albums

    def __call__(self) -> List[models.Album]:
        """
        Gets all albums with a given title.
        """

        albums = [unidecode(a.title).lower() for a in self.albums]

        results = process.extract(
            self.query,
            albums,
            scorer=fuzz.WRatio,
            score_cutoff=Cutoff.albums,
            limit=Limit.albums,
        )

        return [self.albums[i[2]] for i in results]

        # get all artists that matched the query
        # for get all albums from the artists
        # get all albums that matched the query
        # return [**artist_albums **albums]

        # recheck next and previous artist on play next or add to playlist


class SearchPlaylists:
    def __init__(self, playlists: List[models.Playlist], query: str) -> None:
        self.playlists = playlists
        self.query = query

    def __call__(self) -> List[models.Playlist]:
        playlists = [p.name for p in self.playlists]
        results = process.extract(
            self.query,
            playlists,
            scorer=fuzz.WRatio,
            score_cutoff=Cutoff.playlists,
            limit=Limit.playlists,
        )

        return [self.playlists[i[2]] for i in results]


_type = List[models.Track | models.Album | models.Artist]
_S2 = TypeVar("_S2")
_ResultType = int | float


def get_titles(items: _type):
    for item in items:
        if isinstance(item, models.Track):
            text = item.og_title
        elif isinstance(item, models.Album):
            text = item.title
            # print(text)
        elif isinstance(item, models.Artist):
            text = item.name
        else:
            text = None

        yield text


class SearchAll:
    """
    Joins all tracks, albums and artists
    then fuzzy searches them as a single unit.
    """

    @staticmethod
    def collect_all():
        all_items: _type = []

        all_items.extend(Store.tracks)
        all_items.extend(Store.albums)
        all_items.extend(Store.artists)

        return all_items, get_titles(all_items)

    @staticmethod
    def get_results(items: Generator[str, Any, None], query: str):
        items = list(items)

        results = process.extract(
            query=query,
            choices=items,
            scorer=fuzz.WRatio,
            score_cutoff=Cutoff.tracks,
            limit=20
        )

        return results

    @staticmethod
    def sort_results(items: _type):
        """
        Separates results into differrent lists using itertools.groupby.
        """
        mapped_items = [
            {"type": "track", "item": item} if isinstance(item, models.Track) else
            {"type": "album", "item": item} if isinstance(item, models.Album) else
            {"type": "artist", "item": item} if isinstance(item, models.Artist) else
            {"type": "Unknown", "item": item} for item in items
        ]

        mapped_items.sort(key=lambda x: x["type"])

        groups = [
            list(group) for key, group in
            itertools.groupby(mapped_items, lambda x: x["type"])
        ]

        print(len(groups))

        # merge items of a group into a dict that looks like: {"albums": [album1, ...]}
        groups = [
            {f"{group[0]['type']}s": [i['item'] for i in group]} for group in groups
        ]

        return groups

    @staticmethod
    def search(query: str):
        items, titles = SearchAll.collect_all()
        results = SearchAll.get_results(titles, query)
        results = [items[i[2]] for i in results]

        return SearchAll.sort_results(results)
