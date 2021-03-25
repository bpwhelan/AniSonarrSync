import collections
import io
import json
import logging
from datetime import date

import requests

# variables/keys
from auth import *

logger = logging.getLogger("SonarrAniSync")
newAnilistShows = []
tags = []
user_list_response = ''


# noinspection PyArgumentList
def to_object(o):
    keys, values = zip(*o.items())
    # print(keys, values)
    return collections.namedtuple("X", keys)(*values)


# need to fill out for this to work
class AnilistSeries:
    def __init__(
            self,
            media_id,
            s_type,
            s_format,
            source,
            status,
            media_status,
            progress,
            notes,
            season,
            episodes,
            title_english,
            title_romaji,
            started_year,
            ended_year,
            scouting,
            downloaded,
            shame,
            banger_op,
            banger_ed,
            keijo,
            sonarr,
            json_object,
    ):
        self.id = media_id
        self.sType = s_type
        self.sFormat = s_format
        self.source = source
        self.status = status
        self.media_status = media_status
        self.progress = progress
        self.notes = notes
        self.season = season
        self.episodes = episodes
        self.title_english = title_english
        self.title_romaji = title_romaji
        self.started_year = started_year
        self.ended_year = ended_year
        self.scouting = scouting
        self.downloaded = downloaded
        self.shame = shame
        self.bangerOPs = banger_op
        self.bangerEDs = banger_ed
        self.keijo = keijo
        self.sonarr = sonarr
        self.jsonObject = json_object

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)


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
    ):
        self.id = show_id
        self.tvdbId = tvdb_id
        self.sortTitle = sort_title
        self.title = title
        self.jsonObject = json_object
        self.episodeCount = episode_count
        self.episodeFileCount = episode_file_count
        self.seasons = seasons


# def check_and_get_old_token():
#     try:
#         # open the file if it exists
#         print('Checking for token file')
#         token_file = open('anilist.token', 'r+')
#         token_json = json.load(token_file)
#         time_now = time.time()
#
#         if time_now < token_json['expires']:
#             global access_token
#             access_token = token_json['access_token']
#             token_file.close()
#             print('Token file checked and valid')
#             return True
#         else:
#             token_file.close()
#             print('Token file checked and invalid')
#             return False
#
#     except Exception as e:
#         # Token file doesnt exist or there was some other error
#         # create a new empty token file
#         print('No existing token file found')
#         open('anilist.token', 'w').close()
#         return False
#
#
# def get_auth():
#     try:
#         print('Trying to get new anilist token')
#         request = requests.post('https://anilist.co/api/v2/oauth/authorize',
#                                 params={'grant_type': 'authorization_code', 'client_id': ANICLIENT,
#                                         'client_secret': ANISECRET, 'redirect_uri': REDIRECT})
#         print('Gained anilist token')
#
#         print('Writing new anilist token file')
#         request_json = request.json()
#         print(request_json)
#         f = open('anilist.token', 'w')
#         json.dump(request_json, f)
#         f.close()
#
#         global accessToken
#         accessToken = request_json['access_token']
#     except Exception as e:
#         traceback.print_exc()
#         print('Error getting anilist API token')


# noinspection PyGlobalUndefined
def fetch_user_list(username):
    query = """
            query ($username: String) {
            MediaListCollection(userName: $username, type: ANIME) {
                lists {
                name
                status
                isCustomList
                entries {
                    id
                    progress
                    status
                    repeat
                    notes
                    customLists
                    media{
                    id
                    type
                    format
                    status
                    source
                    season
                    episodes
                    startDate {
                        year
                        month
                        day
                    }
                    endDate {
                        year
                        month
                        day
                    }
                    title {
                        romaji
                        english
                        native
                    }
                    }
                }
                }
            }
            }
            """

    variables = {"username": username}

    url = "https://graphql.anilist.co"

    headers = {
        "Authorization": "Bearer " + accessToken,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = requests.post(
        url, headers=headers, json={"query": query, "variables": variables}
    )

    global user_list_response
    user_list_response = response.content.decode('utf-8')
    # print(response.content.decode('utf-8'))

    # f = open("list.json", "w")
    # f.write(response.content.decode('utf-8'))
    # f.close()

    f = open("list2.json", "w")
    f.write(user_list_response)
    f.close()

    for item in json.loads(response.content, object_hook=to_object):
        logger.info(item)
        for mediaCollection in item.MediaListCollection.lists:
            for list_entry in mediaCollection.entries:
                aniListShows.append(mediaitem_to_object(list_entry))


def get_list(username):
    logger.info("[ANILIST] Retrieving AniList list for user: %s" % username)
    anilist_series = []
    fetch_user_list(username)
    fetch_sonarr_list()
    try:
        if not aniListShows:
            logger.critical(
                "[ANILIST] Failed to return list for user: %s" % username)
            return None
        else:
            for series_obj in aniListShows:
                # if list_entry.status != "DROPPED" and list_entry.status != "COMPLETED"
                # and list_entry.status != "PAUSED":
                if series_obj.sonarr:
                    # and "#radarr" not in list_entry.notes:
                    anilist_series.append(series_obj)
                    # checkSonarrForDownloadedFiles(series_obj)
                    # fixBlankTag(series_obj.id, series_obj)
                    # break
                else:
                    if series_obj.notes is None:
                        anilist_series.append(series_obj)
                # if list_entry.status == "CURRENT":
                #     if list_entry.media is not None:
                #         series_obj = mediaitem_to_object(
                #             list_entry)
                #         anilist_series.append(series_obj)
                # if list_entry.status == "PLANNING":
                #     if list_entry.media is not None:
                #         series_obj = mediaitem_to_object(
                #             list_entry)
                #         anilist_series.append(series_obj)
                # if list_entry.status == "COMPLETED":
                #     if list_entry.media is not None:
                #         series_obj = mediaitem_to_object(
                #             list_entry)
                #         anilist_series.append(series_obj)
                # if list_entry.status == "DROPPED":
                #     if list_entry.media is not None:
                #         series_obj = mediaitem_to_object(
                #             list_entry)
                #         anilist_series.append(series_obj)
                # if list_entry.status == "PAUSED":
                #     if list_entry.media is not None:
                #         series_obj = mediaitem_to_object(
                #             list_entry)
                #         anilist_series.append(series_obj)
                # if list_entry.status == "REPEATING":
                #     if list_entry.media is not None:
                #         series_obj = mediaitem_to_object(
                #             list_entry)
                #         anilist_series.append(series_obj)
    except BaseException as e:
        print(e)
        logger.critical(
            "[ANILIST] Failed to return list for user: %s" % username)
        return None

    logger.info("[ANILIST] Found %s anime series on list" %
                (len(anilist_series)))
    return anilist_series


def fetch_sonarr_list():
    response = requests.get(
        SONARRURL + "series?apikey=" + SONARRAPIKEY)

    list_items = json.loads(response.content, object_hook=to_object)

    for item in list_items:
        series_obj = sonarr_item_to_object(item)
        sonarrShows.append(series_obj)


def sonarr_item_to_object(list_entry):
    episode_count = ''
    episode_file_count = ''
    seasons = []
    json_object = list_entry
    tvdb_id = list_entry.tvdbId
    sort_title = list_entry.sortTitle
    title = list_entry.title
    sonarr_id = ''
    if hasattr(list_entry, "id"):
        sonarr_id = list_entry.id
    if hasattr(list_entry, "episodeCount"):
        episode_count = list_entry.episodeCount
    if hasattr(list_entry, "episodeFileCount"):
        episode_file_count = list_entry.episodeFileCount
    if hasattr(list_entry, "seasons"):
        seasons = list_entry.seasons

    sonarr_item = SonarrItem(
        sonarr_id,
        tvdb_id,
        sort_title,
        title,
        json_object,
        episode_count,
        episode_file_count,
        seasons,
    )

    return sonarr_item


def mediaitem_to_object(media_item):
    media_id = media_item.media.id
    s_type = ""
    s_format = ""
    source = ""
    status = ""
    media_status = ""
    progress = ""
    season = ""
    episodes = ""
    title_english = ""
    title_romaji = ""
    started_year = ""
    ended_year = ""
    notes = ""
    # custom Lists
    scouting = ""
    downloaded = ""
    shame = ""
    banger_op = ""
    banger_ed = ""
    keijo = ""
    sonarr = ""
    json_object = media_item

    if hasattr(media_item.customLists, "Scouting"):
        scouting = media_item.customLists.Scouting
    if hasattr(media_item.customLists, "Downloaded"):
        downloaded = media_item.customLists.Downloaded
    if hasattr(media_item.customLists, "shame"):
        shame = media_item.customLists.Shame
    if hasattr(media_item.customLists, "BANGER_OPs"):
        banger_op = media_item.customLists.BANGER_OPs
    if hasattr(media_item.customLists, "BANGER_EDs"):
        banger_ed = media_item.customLists.BANGER_EDs
    if hasattr(media_item.customLists, "Keijo"):
        keijo = media_item.customLists.Keijo
    if hasattr(media_item.customLists, "Sonarr"):
        sonarr = media_item.customLists.Sonarr
    if hasattr(media_item, "status"):
        status = media_item.status
    if hasattr(media_item, "progress"):
        progress = media_item.progress
    if hasattr(media_item, "notes"):
        notes = media_item.notes
    if hasattr(media_item.media, "status"):
        media_status = media_item.media.status
    if hasattr(media_item.media, "type"):
        s_type = media_item.media.type
    if hasattr(media_item.media, "format"):
        s_format = media_item.media.format
    if hasattr(media_item.media, "source"):
        source = media_item.media.source
    if hasattr(media_item.media, "season"):
        season = media_item.media.season
    if hasattr(media_item.media, "episodes"):
        episodes = media_item.media.episodes
    if hasattr(media_item.media.title, "english"):
        title_english = media_item.media.title.english
    if hasattr(media_item.media.title, "romaji"):
        title_romaji = media_item.media.title.romaji
    if hasattr(media_item.media.startDate, "year"):
        started_year = media_item.media.startDate.year
    if hasattr(media_item.media.endDate, "year"):
        ended_year = media_item.media.endDate.year

    series = AnilistSeries(
        media_id,
        s_type,
        s_format,
        source,
        status,
        media_status,
        progress,
        notes,
        season,
        episodes,
        title_english,
        title_romaji,
        started_year,
        ended_year,
        scouting,
        downloaded,
        shame,
        banger_op,
        banger_ed,
        keijo,
        sonarr,
        json_object,
    )

    return series


def add_to_sonarr_list(media_id, series_obj):
    query = """
        mutation ($mediaId: Int, $customLists: [String]) {
            SaveMediaListEntry (mediaId: $mediaId, customLists: $customLists) {
                id
                customLists
            }
        }
        """
    custom_lists = ["Sonarr"]
    if series_obj.downloaded:
        custom_lists.append("Downloaded")
    if series_obj.scouting:
        custom_lists.append("Scouting")
    if series_obj.shame:
        custom_lists.append("Shame")
    if series_obj.bangerOPs:
        custom_lists.append("BANGER_OPs")
    if series_obj.bangerEDs:
        custom_lists.append("BANGER_EDs")
    if series_obj.keijo:
        custom_lists.append("Keijo")
    print(custom_lists)
    print(series_obj.title_english)

    variables = {"mediaId": media_id, "customLists": ["Sonarr"]}

    url = "https://graphql.anilist.co"

    headers = {
        "Authorization": "Bearer " + accessToken,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # print({"query": query, "variables": variables})

    response = requests.post(
        url, headers=headers, json={"query": query, "variables": variables}
    )

    print(response.content)


def add_to_downloaded_list(media_id, series_obj, remove_downloaded):
    query = """
        mutation ($mediaId: Int, $customLists: [String]) {
            SaveMediaListEntry (mediaId: $mediaId, customLists: $customLists) {
                id
                customLists
            }
        }
        """

    custom_lists = []
    if not remove_downloaded:
        custom_lists.append("Downloaded")
    if series_obj.scouting:
        custom_lists.append("Scouting")
    if series_obj.shame:
        custom_lists.append("Shame")
    if series_obj.bangerOPs:
        custom_lists.append("BANGER_OPs")
    if series_obj.bangerEDs:
        custom_lists.append("BANGER_EDs")
    if series_obj.keijo:
        custom_lists.append("Keijo")
    custom_lists.append("Sonarr")
    print(custom_lists)
    print(series_obj.title_english)

    variables = {"mediaId": media_id, "customLists": custom_lists}

    url = "https://graphql.anilist.co"

    headers = {
        "Authorization": "Bearer " + accessToken,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # print({"query": query, "variables": variables})

    response = requests.post(
        url, headers=headers, json={"query": query, "variables": variables}
    )

    print(response.content)


def remove_sonarr_tag(media_id, series_obj):
    query = """
        mutation ($mediaId: Int, $notes: String) {
            SaveMediaListEntry (mediaId: $mediaId, notes: $notes) {
                id
                notes
            }
        }
        """
    notes = series_obj.notes

    if notes is not None:
        notes = notes.replace('#sonarr', '')

    print(notes)
    print(series_obj.title_english)

    variables = {"mediaId": media_id, "notes": notes}

    url = "https://graphql.anilist.co"

    headers = {
        "Authorization": "Bearer " + accessToken,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    print({"query": query, "variables": variables})

    response = requests.post(
        url, headers=headers, json={"query": query, "variables": variables}
    )

    print(response.content)


def fix_blank_tag(media_id, series_obj):
    query = """
        mutation ($mediaId: Int, $notes: String) {
            SaveMediaListEntry (mediaId: $mediaId, notes: $notes) {
                id
                notes
            }
        }
        """
    notes = series_obj.notes

    if notes is not None and notes == ' ':
        notes = ''

    print(notes)
    print(series_obj.title_english)

    variables = {"mediaId": media_id, "notes": notes}

    url = "https://graphql.anilist.co"

    headers = {
        "Authorization": "Bearer " + accessToken,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    print({"query": query, "variables": variables})

    response = requests.post(
        url, headers=headers, json={"query": query, "variables": variables}
    )

    print(response.content)


def search_by_name(anilist_show_name):
    query = """
        query ($id: Int, $page: Int, $perPage: Int, $search: String) {
            Page (page: $page, perPage: $perPage) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                    perPage
                }
                media (id: $id, search: $search, type: ANIME) {
                    id
                    type
                    format
                    status
                    source
                    season
                    episodes
                    title {
                        romaji
                        english
                        native
                    }
                    synonyms
                    startDate {
                        year
                        month
                        day
                    }
                    endDate {
                        year
                        month
                        day
                    }
                }
            }
        }
        """
    variables = {"search": anilist_show_name, "page": 1, "perPage": 50}
    url = "https://graphql.anilist.co"

    headers = {
        "Authorization": "Bearer " + accessToken,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = requests.post(
        url, headers=headers, json={"query": query, "variables": variables}
    )

    print(response.content)

    f = open("search.json", "w")
    f.write(response.content.decode('utf-8'))
    f.close()

    return json.loads(response.content, object_hook=to_object)


def check_sonarr_for_downloaded_files():
    for sonarrShow in sonarrShows:
        # series_obj = mediaitem_to_object(search_by_name(sonarrShow))
        print(sonarrShow.sortTitle)
        print('Episodes in show: ', sonarrShow.episodeCount)
        print('Episodes downloaded: ', sonarrShow.episodeFileCount)
        if sonarrShow.episodeCount == sonarrShow.episodeFileCount:
            anilist_search = search_by_name(sonarrShow.sortTitle)
            found = False
            for item in anilist_search:
                if item[0].media:
                    for media_item in item[0].media:
                        for aniListShow2 in aniListShows:
                            if media_item.id == aniListShow2.id:
                                if aniListShow2.downloaded and sonarrShow.episodeCount != 0:
                                    found = True
                                    break
                                found = True
                                add_to_downloaded_list(aniListShow2.id, aniListShow2, sonarrShow.episodeCount == 0)
                                break
                        if found:
                            break


def fetch_user_list_by_file():
    with open('list.json') as f:
        data = json.load(f)

    for item in json.loads(json.dumps(data), object_hook=to_object):
        logger.info(item)
        for mediaCollection in item.MediaListCollection.lists:
            for list_entry in mediaCollection.entries:
                aniListShowsFromFile.append(mediaitem_to_object(list_entry))

    print(len(aniListShowsFromFile))


def get_tag_for_show(item):
    season = item.jsonObject.media.season.lower()
    current_year = date.today().year
    tag_name = season + str(current_year)
    if not tags:
        response = requests.get(SONARRURL + 'tag?apikey=' + SONARRAPIKEY)
        for tag in json.loads(response.content, object_hook=to_object):
            tags.append(tag)

    for tag in tags:
        print(tag.label)
        print(tag_name)
        if tag.label == tag_name:
            return tag.id


def add_show_to_sonarr(tvdb_id, title, series, item):
    tag = get_tag_for_show(item)
    print(tvdb_id)
    print(title)
    params = {
        'tvdbId': tvdb_id,
        'title': series.jsonObject.title,
        'titleSlug': series.jsonObject.titleSlug,
        'profileId': 9,
        # 'images' : json.dumps(str(series.jsonObject.images)),
        # 'seasons' : str(series.jsonObject.seasons),
        'seriesType': 'Anime',
        'path': '/tv/Anime/' + series.jsonObject.title,
        'seasonFolder': 'true',
        'tags': [tag]
    }
    response = requests.post(SONARRURL + 'series?apikey=' + SONARRAPIKEY, data=str(params).encode('utf-8'))

    print(response.content.decode('utf-8'))


def tag_show_in_sonarr(tvdb_id, title, anilist_item):
    sonarr_entry = ''
    for item in sonarrShows:
        if item.tvdbId == tvdb_id:
            sonarr_entry = item
            break
    tag = get_tag_for_show(anilist_item)

    sonarr_show_resp = requests.get(SONARRURL + "series/" + str(sonarr_entry.id) + "?apikey=" + SONARRAPIKEY)

    json_object = json.loads(sonarr_show_resp.content.decode('utf-8'))

    if tag in json_object['tags']:
        print("Skipped tagging " + title)
        return

    json_object['tags'].append(tag)

    response = requests.put(SONARRURL + 'series?apikey=' + SONARRAPIKEY, json=json_object)

    print(response.content.decode('utf-8'))


def check_and_add_sonarr_show(tvdb_id, title, series, anilist_item):
    fetch_sonarr_list()
    found = False
    # Skip items in my Ecchi custom list possibly switch to new url/apikey ;)
    if anilist_item.shame:
        return
    for item in sonarrShows:
        if item.tvdbId == tvdb_id:
            found = True
    if not found:
        add_show_to_sonarr(tvdb_id, title, series, anilist_item)
    else:
        tag_show_in_sonarr(tvdb_id, title, anilist_item)


def get_id_from_sonarr(title, item):
    print(title)
    print(title.replace(' ', '%20'))
    response = requests.get(
        SONARRURL + 'series/lookup?apikey=' + SONARRAPIKEY + '&term=' + title.replace(' ', '%20'))

    # print(response.content.decode('utf-8'))

    with io.open("tvdbSearch.json", "w", encoding="utf-8") as f:
        f.write(response.content.decode('utf-8'))

    list_items = json.loads(response.content, object_hook=to_object)

    series_obj = sonarr_item_to_object(list_items[0])

    check_and_add_sonarr_show(series_obj.tvdbId, series_obj.title, series_obj, item)


# NEED TO REFACTOR, MISPLACED RESPONSIBILITY IN get_id_from_sonarr
def get_tvdb_id_for_new_shows():
    for item in newAnilistShows:
        if item.title_english:
            get_id_from_sonarr(item.title_english, item)
        else:
            get_id_from_sonarr(item.title_romaji, item)


def get_new_shows():
    fetch_user_list(USERNAME)
    fetch_user_list_by_file()
    for item in aniListShows:
        found = False
        for item2 in aniListShowsFromFile:
            if item.id == item2.id:
                found = True
        if not found:
            newAnilistShows.append(item)

    for item in newAnilistShows:
        print(item.title_romaji)

    get_tvdb_id_for_new_shows()

    # write updates
    f = open("list.json", "w")
    f.write(user_list_response)
    f.close()

    # list_items = json.loads(response.content, object_hook=to_object)


# sonarrList =  getList(USERNAME)
# Future Use
# if not check_and_get_old_token(): 
#     print('No valid existing token file')
#     getAuth()
# fetch_sonarr_list()
# fetch_user_list(USERNAME)

get_new_shows()
# getTVDBIDforNewShows()


# checkSonarrForDownloadedFiles()

# for entry in sonarrShows:
#     print(entry.title_english)
