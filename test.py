import collections
import json
import logging
import re
import time
import requests
import traceback
import io
from datetime import date

logger = logging.getLogger("SonarrAniSync")


def to_object(o):
    keys, values = zip(*o.items())
    # print(keys, values)
    return collections.namedtuple("X", keys)(*values)


# need to fill out for this to work
ANILIST_ACCESS_TOKEN = ""
USERNAME = ""
ANICLIENT = ''
ANISECRET = ''
SONARRAPIKEY = ""
SONARRURL = ""
sonarrShows = []
aniListShows = []
aniListShowsFromFile = []
userListResponse = ''


class anilist_series:
    def __init__(
        self,
        id,
        sType,
        sFormat,
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
        bangerOPs,
        bangerEDs,
        keijo,
        sonarr,
        jsonObject,
    ):
        self.id = id
        self.sType = sType
        self.sFormat = sFormat
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
        self.bangerOPs = bangerOPs
        self.bangerEDs = bangerEDs
        self.keijo = keijo
        self.sonarr = sonarr
        self.jsonObject = jsonObject

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)


class sonarr_Item:
    def __init__(
        self,
        id,
        tvdbId,
        sortTitle,
        title,
        jsonObject,
        episodeCount,
        episodeFileCount,
    ):
        self.id = id
        self.tvdbId = tvdbId
        self.sortTitle = sortTitle
        self.title = title
        self.jsonObject = jsonObject
        self.episodeCount = episodeCount
        self.episodeFileCount = episodeFileCount


def check_and_get_old_token():
    try:
        # open the file if it exists
        print('Checking for token file')
        token_file = open('anilist.token', 'r+')
        token_json = json.load(token_file)
        time_now = time.time()

        if time_now < token_json['expires']:
            global access_token
            access_token = token_json['access_token']
            token_file.close()
            print('Token file checked and valid')
            return True
        else:
            token_file.close()
            print('Token file checked and invalid')
            return False

    except Exception as e:
        # Token file doesnt exist or there was some other error
        # create a new empty token file
        print('No existing token file found')
        open('anilist.token', 'w').close()
        return False

def getAuth():
    try:
        print ('Trying to get new anilist token')
        request = requests.post('https://anilist.co/api/v2/oauth/authorize', params={'grant_type':'authorization_code', 'client_id':ANICLIENT, 'client_secret':ANISECRET, 'redirect_uri':REDIRECT})
        print ('Gained anilist token')

        print('Writing new anilist token file')
        request_json = request.json()
        print(request_json)
        f = open('anilist.token', 'w')
        json.dump(request_json, f)
        f.close()
        
        global accessToken
        accessToken = request_json['access_token']
    except Exception as e:
        traceback.print_exc()
        print('Error getting anilist API token')

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

    global userListResponse
    userListResponse = response.content.decode('utf-8')
    # print(response.content.decode('utf-8'))

    # f = open("list.json", "w")
    # f.write(response.content.decode('utf-8'))
    # f.close()

    f = open("list2.json", "w")
    f.write(userListResponse)
    f.close()

    for item in json.loads(response.content, object_hook=to_object):
        logger.info(item)
        for mediaCollection in item.MediaListCollection.lists:
            for list_entry in mediaCollection.entries:
                aniListShows.append(mediaitem_to_object(list_entry))


def getList(username):
    logger.info("[ANILIST] Retrieving AniList list for user: %s" % (username))
    anilist_series = []
    fetch_user_list(username)
    fetch_sonarr_list()
    try:
        if not aniListShows:
            logger.critical(
                "[ANILIST] Failed to return list for user: %s" % (username))
            return None
        else:
            for series_obj in aniListShows:
               # if list_entry.status != "DROPPED" and list_entry.status != "COMPLETED" and list_entry.status != "PAUSED":
                if series_obj.sonarr:
                       # and "#radarr" not in list_entry.notes:
                    anilist_series.append(series_obj)
                    # checkSonarrForDownloadedFiles(series_obj)
                       # fixBlankTag(series_obj.id, series_obj)
                       # break
                else:
                    if list_entry.notes is None:
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
            "[ANILIST] Failed to return list for user: %s" % (username))
        return None

    logger.info("[ANILIST] Found %s anime series on list" %
                (len(anilist_series)))
    return anilist_series


def fetch_sonarr_list():
    response = requests.get(
        'http://192.168.1.44:8989/api/series?apikey=967131e54d324b8b97496273edbe0551')

    list_items = json.loads(response.content, object_hook=to_object)

    for item in list_items:
        series_obj = sonarrItem_To_Object(item)
        sonarrShows.append(series_obj)


def sonarrItem_To_Object(list_entry):
    episodeCount = ''
    episodeFileCount = ''
    seasons = []
    jsonObject = list_entry
    tvdbId = list_entry.tvdbId
    sortTitle = list_entry.sortTitle
    title = list_entry.title
    id = ''
    if hasattr(list_entry, "id"):
        id = list_entry.id
    if hasattr(list_entry, "episodeCount"):
        episodeCount = list_entry.episodeCount
    if hasattr(list_entry, "episodeFileCount"):  
        episodeFileCount = list_entry.episodeFileCount
    if hasattr(list_entry, "seasons"):
        seasons = list_entry.seasons

    sonarrItem = sonarr_Item(
        id,
        tvdbId,
        sortTitle,
        title,
        jsonObject,
        episodeCount,
        episodeFileCount,
    )

    return sonarrItem


def mediaitem_to_object(media_item):
    id = media_item.media.id
    sType = ""
    sFormat = ""
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
    bangerOPs = ""
    bangerEDs = ""
    keijo = ""
    sonarr = ""
    jsonObject = media_item

    if hasattr(media_item.customLists, "Scouting"):
        scouting = media_item.customLists.Scouting
    if hasattr(media_item.customLists, "Downloaded"):
        downloaded = media_item.customLists.Downloaded
    if hasattr(media_item.customLists, "shame"):
        shame = media_item.customLists.Shame
    if hasattr(media_item.customLists, "BANGER_OPs"):
        bangerOPs = media_item.customLists.BANGER_OPs
    if hasattr(media_item.customLists, "BANGER_EDs"):
        bangerEDs = media_item.customLists.BANGER_EDs
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
        sType = media_item.media.type
    if hasattr(media_item.media, "format"):
        sFormat = media_item.media.format
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

    series = anilist_series(
        id,
        sType,
        sFormat,
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
        bangerOPs,
        bangerEDs,
        keijo,
        sonarr,
        jsonObject,
    )

    return series


def addToSonarrList(mediaId, series_obj):
    query = """
        mutation ($mediaId: Int, $customLists: [String]) {
            SaveMediaListEntry (mediaId: $mediaId, customLists: $customLists) {
                id
                customLists
            }
        }
        """
    customLists = ["Sonarr"]
    if(series_obj.downloaded):
        customLists.append("Downloaded")
    if(series_obj.scouting):
        customLists.append("Scouting")
    if(series_obj.shame):
        customLists.append("Shame")
    if(series_obj.bangerOPs):
        customLists.append("BANGER_OPs")
    if(series_obj.bangerEDs):
        customLists.append("BANGER_EDs")
    if(series_obj.keijo):
        customLists.append("Keijo")
    print(customLists)
    print(series_obj.title_english)

    variables = {"mediaId": mediaId, "customLists": ["Sonarr"]}

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


def addToDownloadedList(mediaId, series_obj, removeDownloaded):
    query = """
        mutation ($mediaId: Int, $customLists: [String]) {
            SaveMediaListEntry (mediaId: $mediaId, customLists: $customLists) {
                id
                customLists
            }
        }
        """

    customLists = []
    if removeDownloaded:
        None
    else:
        customLists.append("Downloaded")
    if(series_obj.scouting):
        customLists.append("Scouting")
    if(series_obj.shame):
        customLists.append("Shame")
    if(series_obj.bangerOPs):
        customLists.append("BANGER_OPs")
    if(series_obj.bangerEDs):
        customLists.append("BANGER_EDs")
    if(series_obj.keijo):
        customLists.append("Keijo")
    customLists.append("Sonarr")
    print(customLists)
    print(series_obj.title_english)

    variables = {"mediaId": mediaId, "customLists": customLists}

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


def remove_sonarrTag(mediaId, series_obj):
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

    variables = {"mediaId": mediaId, "notes": notes}

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


def fixBlankTag(mediaId, series_obj):
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

    variables = {"mediaId": mediaId, "notes": notes}

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


def checkSonarrForDownloadedFiles():
    for sonarrShow in sonarrShows:
        # series_obj = mediaitem_to_object(search_by_name(sonarrShow))
        print(sonarrShow.sortTitle)
        print('Episodes in show: ', sonarrShow.episodeCount)
        print('Episodes downloaded: ', sonarrShow.episodeFileCount)
        if sonarrShow.episodeCount == sonarrShow.episodeFileCount:
            aniListSearch = search_by_name(sonarrShow.sortTitle)
            found = False
            for item in aniListSearch:
                if item[0].media:
                    for media_item in item[0].media:
                        for aniListShow2 in aniListShows:
                            if media_item.id == aniListShow2.id:
                                if(aniListShow2.downloaded and sonarrShow.episodeCount != 0):
                                    found = True
                                    break
                                found = True
                                addToDownloadedList(aniListShow2.id, aniListShow2, sonarrShow.episodeCount == 0)
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

newAnilistShows = []
tags = []

def getTagForShow(id, title, series, item):
    season = item.jsonObject.media.season.lower()
    currentYear = date.today().year
    tagName = season + str(currentYear)
    if not tags:
        response = requests.get(SONARRURL + 'tag?apikey=' + SONARRAPIKEY)
        for tag in json.loads(response.content, object_hook=to_object):
            tags.append(tag)
    
    for tag in tags:
        print(tag.label)
        print(tagName)
        if tag.label == tagName:
            return tag.id

def addShowToSonarr(id, title, series, item):
    tag = getTagForShow(id, title, series, item)
    print(id)
    print(title)
    params = {
        'tvdbId' : id,
        'title' : series.jsonObject.title,
        'titleSlug' : series.jsonObject.titleSlug,
        'profileId' : 9,
        # 'images' : json.dumps(str(series.jsonObject.images)),
        # 'seasons' : str(series.jsonObject.seasons),
        'seriesType' : 'Anime',
        'path' : '/tv/Anime/' + series.jsonObject.title,
        'seasonFolder' : 'true',
        'tags' : [tag]
    }
    response = requests.post('http://192.168.1.44:8989/api/series?apikey=' + SONARRAPIKEY, data=str(params).encode('utf-8'))

    print (response.content.decode('utf-8'))

def tagShowInSonarr(id, title, series, aniListItem):
    sonarrEntry = ''
    for item in sonarrShows:
        if item.tvdbId == id:
            sonarrEntry = item
            break
    tag = getTagForShow(id, title, sonarrEntry, aniListItem)
    
    sonarrShowResp = requests.get(SONARRURL + "series/" + str(sonarrEntry.id) + "?apikey=" + SONARRAPIKEY)

    json_object = json.loads(sonarrShowResp.content.decode('utf-8'))

    json_object['tags'].append(tag)
    
    response = requests.put('http://192.168.1.44:8989/api/series?apikey=' + SONARRAPIKEY, json=json_object)

    print (response.content.decode('utf-8'))

def checkAndAddSonarrShow(id, title, series, anilistItem):
    fetch_sonarr_list()
    found = False
    for item in sonarrShows:
        if item.tvdbId == id:
            found = True
    if not found:
        addShowToSonarr(id, title, series, anilistItem)
    else:
        tagShowInSonarr(id, title, series, anilistItem)

def getIDFromSonarr(title, item):
    print(title)
    print(title.replace(' ', '%20'))
    response = requests.get(
        'http://192.168.1.44:8989/api/series/lookup?apikey=967131e54d324b8b97496273edbe0551&term=' + title.replace(' ', '%20'))

    # print(response.content.decode('utf-8'))

    with io.open("tvdbSearch.json", "w", encoding="utf-8") as f:
        f.write(response.content.decode('utf-8'))

    list_items = json.loads(response.content, object_hook=to_object)

    series_obj = sonarrItem_To_Object(list_items[0])

    checkAndAddSonarrShow(series_obj.tvdbId, series_obj.title, series_obj, item)

def getTVDBIDforNewShows():
    tvdbID = ''
    for item in newAnilistShows:
        if item.title_english:
           tvdbID = getIDFromSonarr(item.title_english, item)
        else:
            tvdbID = getIDFromSonarr(item.title_romaji, item)

def getNewShows():
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
        print (item.title_romaji)

    getTVDBIDforNewShows()

# write updates
    f = open("list.json", "w")
    f.write(userListResponse)
    f.close()

    # list_items = json.loads(response.content, object_hook=to_object)


# sonarrList =  getList(USERNAME)
# Future Use
# if not check_and_get_old_token(): 
#     print('No valid existing token file')
#     getAuth()
# fetch_sonarr_list()
# fetch_user_list(USERNAME)

getNewShows()
# getTVDBIDforNewShows()


# checkSonarrForDownloadedFiles()

# for entry in sonarrShows:
#     print(entry.title_english)
