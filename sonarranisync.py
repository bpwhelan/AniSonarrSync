import io
import json
import logging
import re
from datetime import date
from dataclasses import dataclass
from pprint import pprint

from api_classes import *
import chardet

import requests

# variables/keys
from auth import ANILIST_ACCESS_TOKEN, USERNAME, SONARRAPIKEY, SONARRURL, BUCKET, BLACKLIST

logger = logging.getLogger("SonarrAniSync")
newAnilistShows = []
tags = []
user_list_response = ''
sonarrShows = []
aniListShows = []
aniListShowsFromFile = []
userListResponse = ''


headers = {
    'X-Api-Key': SONARRAPIKEY
}


# DONE
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
        "Authorization": "Bearer " + ANILIST_ACCESS_TOKEN,
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
    # print(response.content)
    j = json.loads(response.content)
    # print(j)
    lists = json_to_anilist(j['data']['MediaListCollection']['lists'])
    print(lists)
    for anilist_list in lists:
        aniListShows.extend(anilist_list.entries)
    # print(item_list)
    # for item in json.loads(response.content, object_hook=to_object):
    #     logger.info(item)
    #     for mediaCollection in item.MediaListCollection.lists:
    #         for list_entry in mediaCollection.entries:
    #             aniListShows.append(mediaitem_to_object(list_entry))


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


# DONE
def fetch_sonarr_list():
    response = requests.get(
        SONARRURL + "series?apikey=" + SONARRAPIKEY)

    # print(response.content.decode('utf-8'))
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
    genres = []
    if hasattr(list_entry, "id"):
        sonarr_id = list_entry.id
    if hasattr(list_entry, "episodeCount"):
        episode_count = list_entry.episodeCount
    if hasattr(list_entry, "episodeFileCount"):
        episode_file_count = list_entry.episodeFileCount
    if hasattr(list_entry, "seasons"):
        seasons = list_entry.seasons
    if hasattr(list_entry, "genres"):
        genres = list_entry.genres

    sonarr_item = SonarrItem(
        sonarr_id,
        tvdb_id,
        sort_title,
        title,
        json_object,
        episode_count,
        episode_file_count,
        seasons,
        genres,
    )

    return sonarr_item


# DONE
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
        "Authorization": "Bearer " + ANILIST_ACCESS_TOKEN,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # print({"query": query, "variables": variables})

    response = requests.post(
        url, headers=headers, json={"query": query, "variables": variables}
    )

    print(response.content)


# DONE
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
        "Authorization": "Bearer " + ANILIST_ACCESS_TOKEN,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # print({"query": query, "variables": variables})

    response = requests.post(
        url, headers=headers, json={"query": query, "variables": variables}
    )

    print(response.content)

# DONE
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
        "Authorization": "Bearer " + ANILIST_ACCESS_TOKEN,
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
    filename = 'list.json'
    enc = chardet.detect(open(filename, 'rb').read())['encoding']
    with open('list.json', 'r', encoding=enc) as f:
        data = json.load(f)

    # for item in json.loads(json.dumps(data), object_hook=to_object):
    #     logger.info(item)
    #     for mediaCollection in item.MediaListCollection.lists:
    #         for list_entry in mediaCollection.entries:
    #             aniListShowsFromFile.append(mediaitem_to_object(list_entry))

        lists = json_to_anilist(data['data']['MediaListCollection']['lists'])
        for anilist_list in lists:
            aniListShowsFromFile.extend(anilist_list.entries)

    print(len(aniListShowsFromFile))


def json_to_anilist(j):
    # return AnilistQuery.schema().loads(j)
    return list(map(convert_list, j))


def convert_list(data):
    # print(data)+
    return AniListListData(**data)


def create_tag_for_show(item, tag_name):
    params = {
        'label': tag_name
    }

    response = requests.post(SONARRURL + 'tag', headers=headers, json=params)
    print(response.content.decode('utf-8'))
    tag = json.loads(response.content, object_hook=to_object)

    return tag.id


def get_tag_for_show(item):
    print(item['media'])
    try:
        season = item['media']['season'].lower()
    except AttributeError:
        return 29
    year = item['media']['startDate']['year']
    tag_name = season + str(year)
    if not tags:
        response = requests.get(SONARRURL + 'tag?apikey=' + SONARRAPIKEY)
        for tag in json.loads(response.content, object_hook=to_object):
            tags.append(tag)

    for tag in tags:
        print(tag.label)
        print(tag_name)
        if tag.label == tag_name:
            return tag.id
    return create_tag_for_show(item, tag_name)


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
        'tags': [29, tag]
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
    if anilist_item['customLists']['Shame'] or anilist_item['customLists']['Smut']:
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
    title = regex_out_title(title)
    search_string = title.replace(' ', '%20') + '%20' + str(item['media']['startDate']['year'])
    print(search_string)
    response = requests.get(
        SONARRURL + 'series/lookup?apikey=' + SONARRAPIKEY + '&term=' + search_string)

    # print(response.content.decode('utf-8'))

    with io.open("tvdbSearch.json", "w", encoding="utf-8") as f:
        f.write(response.content.decode('utf-8'))

    list_items = json.loads(response.content, object_hook=to_object)

    # print(list_items[0])

    series_obj = list(map(sonarr_item_to_object, list_items))

    for tvdb_search in series_obj:
        if "anime" or "animation" in list(map(lambda x: x.lower(), item.genres)):
            logger.info(tvdb_search.jsonObject)
            check_and_add_sonarr_show(tvdb_search.tvdbId, tvdb_search.title, tvdb_search, item)
            break


def regex_out_title(title):
    title = re.sub(" (season|part|cour) \\d", "", title, flags=re.IGNORECASE)
    title = re.sub(" [IVX]+$", "", title)
    return title


# NEED TO REFACTOR, MISPLACED RESPONSIBILITY IN get_id_from_sonarr
def get_tvdb_id_for_new_shows():
    for item in newAnilistShows:
        show_in_blacklist = False
        for blacklisted in BLACKLIST:
            if blacklisted.lower() in item['media']['title']['english'].lower():
                show_in_blacklist = True
        if item['media']['format'] == 'TV' and not show_in_blacklist and item['media']['status'] not in ['DROPPED', 'FINISHED']:
            if item['media']['title']['english']:
                get_id_from_sonarr(item['media']['title']['english'], item)
            else:
                get_id_from_sonarr(item['media']['title']['romaji'], item)


def get_new_shows():
    fetch_user_list(USERNAME)
    fetch_user_list_by_file()
    print(len(aniListShows))
    print(len(aniListShowsFromFile))
    for item in aniListShows:
        # print(item.media)
        found = False
        for item2 in aniListShowsFromFile:
            if item['media']['id'] == item2['media']['id']:
                found = True
        if not found:
            newAnilistShows.append(item)

    print(len(newAnilistShows))

    for item in newAnilistShows:
        print(item)

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
#
get_new_shows()

# create_tag_for_show(tag_name='')
# getTVDBIDforNewShows()


# checkSonarrForDownloadedFiles()

# for entry in sonarrShows:
#     print(entry.title_english)
