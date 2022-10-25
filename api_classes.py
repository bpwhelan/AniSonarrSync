from dataclasses import dataclass
import json
import collections
from dataclasses_json import dataclass_json
from marshmallow import fields


def to_object(o):
    keys, values = zip(*o.items())
    # print(keys, values)
    return collections.namedtuple("X", keys)(*values)


@dataclass_json
@dataclass
class CustomLists:
    Scouting: bool = False
    Downloaded: bool = False
    Shame: bool = False
    BANGER_OPs: bool = False
    BANGER_EDs: bool = False
    Keijo: bool = False
    Sonarr: bool = False
    Radarr: bool = False
    Smut: bool = False


@dataclass_json
@dataclass
class DateObj:
    year: int
    month: int
    day: int


@dataclass_json
@dataclass
class TitleObj:
    romaji: str
    english: str
    native: str


@dataclass_json
@dataclass
class AnilistMedia:
    id: int
    type: str
    format: str
    status: str
    source: str
    season: str
    episodes: int
    startDate: 'DateObj'
    endDate: 'DateObj'
    title: 'TitleObj'


@dataclass_json
@dataclass
class AnilistSeries:
    id: int
    progress: int
    status: str
    repeat: int
    notes: str
    customLists: 'CustomLists'
    media: 'AnilistMedia'


@dataclass_json
@dataclass
class AniListListData:
    name: str
    status: str
    isCustomList: bool
    entries: list['AnilistSeries']

@dataclass_json
@dataclass
class MediaListCollection:
    lists: list['AniListListData']


@dataclass_json
@dataclass
class AnilistQueryData:
    MediaListCollection: 'MediaListCollection'

@dataclass_json
@dataclass
class AnilistQuery:
    data: 'AnilistQueryData'


@dataclass_json
@dataclass
class SonarrItem:
    def __init__(
            self,
            show_id,
            tvdb_id,
            sort_title,
            title,
            json_object,
            episode_count,
            episode_file_count,
            seasons,
            genres,
    ):
        self.id = show_id
        self.tvdbId = tvdb_id
        self.sortTitle = sort_title
        self.title = title
        self.jsonObject = json_object
        self.episodeCount = episode_count
        self.episodeFileCount = episode_file_count
        self.seasons = seasons
        self.genres = genres

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                sort_keys=True, indent=4)

