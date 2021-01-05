import collections
import json
import logging
import re
import time
import requests

logger = logging.getLogger("AniSonarrSync")
def to_object(o):
    keys, values = zip(*o.items())
    # print(keys, values)
    return collections.namedtuple("X", keys)(*values)

#need to fill out for this to work
ANILIST_ACCESS_TOKEN = ""
USERNAME = ""


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

    f = open("list.json", "w")
    f.write(response.content.decode('utf-8'))
    f.close()

    return json.loads(response.content, object_hook=to_object)


def getList(username):
    logger.info("[ANILIST] Retrieving AniList list for user: %s" % (username))
    anilist_series = []
    list_items = fetch_user_list(username)
    try:
        if not list_items:
            logger.critical(
                "[ANILIST] Failed to return list for user: %s" % (username))
            return None
        else:
            for item in list_items:
                for mediaCollection in item.MediaListCollection.lists:
                    if hasattr(mediaCollection, "entries"):
                        for list_entry in mediaCollection.entries:
                            # if list_entry.status != "DROPPED" and list_entry.status != "COMPLETED" and list_entry.status != "PAUSED":
                                series_obj = mediaitem_to_object(list_entry)
                                if hasattr(list_entry, "notes"):
                                    if series_obj.sonarr:
                                    # and "#radarr" not in list_entry.notes:
                                            anilist_series.append(series_obj)
                                            fixBlankTag(series_obj.id, series_obj)
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
    #custom Lists
    scouting = ""
    downloaded = ""
    shame = ""
    bangerOPs = ""
    bangerEDs = ""
    keijo = ""
    sonarr = ""

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
        "Authorization": "Bearer " + ANILIST_ACCESS_TOKEN,
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
        "Authorization": "Bearer " + ANILIST_ACCESS_TOKEN,
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
        "Authorization": "Bearer " + ANILIST_ACCESS_TOKEN,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    print({"query": query, "variables": variables})

    response = requests.post(
        url, headers=headers, json={"query": query, "variables": variables}
    )

    print(response.content)

sonarrList =  getList(USERNAME)

for entry in sonarrList:
    print(entry.title_english)
