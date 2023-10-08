import re
import urllib
import sys

import requests
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import xbmcplugin


__baseurl__ = "http://api.play.cz/xml"
_UserAgent_ = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3"
addon = xbmcaddon.Addon("plugin.audio.dmd-czech.play.cz")
profile = xbmcvfs.translatePath(addon.getAddonInfo("profile"))
__settings__ = xbmcaddon.Addon(id="plugin.audio.dmd-czech.play.cz")
__lang__ = addon.getLocalizedString
home = __settings__.getAddonInfo("path")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3"
}


def generate_station_list() -> None:
    """Generate and display a mesh of available play.cz stations in Kodi UI."""
    response = requests.get("http://api.play.cz/xml/getRadios", headers=HEADERS)
    response.raise_for_status()
    match = re.compile(
        "<title>.+?CDATA\[(.+?)\]\]></title>\s<description>.+?CDATA\[(.+?)\]\]></description>\s<shortcut>.+?CDATA\[(.+?)\]\]></shortcut>"
    ).findall(response.text)
    for title, description, shortcut in match:
        add_station_to_list(
            title,
            shortcut,
            1,
            "http://api.play.cz/static/radio_logo/t200/" + shortcut + ".png",
            description,
        )
    xbmc.executebuiltin("Container.SetViewMode(51)")


def play_stream(url) -> None:
    """Find the highest bitrate mp3 stream and start playing it."""
    shortcut = url
    url = "http://api.play.cz/xml/getAllStreams/" + url
    xml = http_get_and_remove_whitespace(url)
    streams = re.compile("<streams>(.+?)</streams>").findall(xml)
    # mp3 is always available, ignore the rest
    mp3_stream = next(iter(s for s in streams if "mp3" in s))
    bitrates = re.compile("<loop><\!\[CDATA\[(.+?)\]\]></loop>").findall(mp3_stream)
    max_bitrate = max(bitrates)
    url = f"http://api.play.cz/xml/getStream/{shortcut}/mp3/{max_bitrate}"
    xml = http_get_and_remove_whitespace(url)
    streams = re.compile("<pubpoint>.+?CDATA\[(.+?)\]\]></pubpoint>").findall(xml)

    # Play the music stream
    player = xbmc.Player()
    player.play(streams[0])  # Looks like there is always just 1 stream


def add_station_to_list(name, url, mode, iconimage, comment) -> bool:
    """Add a single station to the mesh of Kodi stations."""
    u = f"{sys.argv[0]}?url={urllib.parse.quote_plus(url)}&mode={mode}&name={urllib.parse.quote_plus(name)}"
    liz = xbmcgui.ListItem(name)
    liz.setArt({"icon": "DefaultFolder.png", "thumb": iconimage})
    liz.setInfo(type="music", infoLabels={"title": name, "comment": comment})
    return xbmcplugin.addDirectoryItem(
        handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True
    )


def http_get_and_remove_whitespace(url: str) -> str:
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3"
        },
    )
    response.raise_for_status()
    return response.text.replace("\t", "").replace("\r", "").replace("\n", "")


def main() -> None:
    """Either display a list of available play.cz stations or start playing on depending on mode."""
    params = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(sys.argv[2]).query))
    mode = params.get("mode")
    if not mode:
        generate_station_list()
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
    elif mode == "1":
        play_stream(params["url"])


if __name__ == "__main__":
    main()
