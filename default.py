# -*- coding: utf-8 -*-
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


def http_get_and_remove_whitespace(url: str) -> str:
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3"
        },
    )
    response.raise_for_status()
    return response.text.replace("\t", "").replace("\r", "").replace("\n", "")


def SEZNAM():
    response = requests.get("http://api.play.cz/xml/getRadios", headers=HEADERS)
    response.raise_for_status()
    match = re.compile(
        "<title>.+?CDATA\[(.+?)\]\]></title>\s<description>.+?CDATA\[(.+?)\]\]></description>\s<shortcut>.+?CDATA\[(.+?)\]\]></shortcut>"
    ).findall(response.text)
    for title, description, shortcut in match:
        addDir(
            title,
            shortcut,
            1,
            "http://api.play.cz/static/radio_logo/t200/" + shortcut + ".png",
            description,
        )
    xbmc.executebuiltin("Container.SetViewMode(51)")


def LINK(url):
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
    return addLink(
        f"mp3 {max_bitrate} kbps",
        streams[0],  # Looks like there is always just 1 stream
        f"http://api.play.cz/static/radio_logo/t200/{shortcut}.png",
        "",
    )


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace("?", "")
        if params[len(params) - 1] == "/":
            params = params[0 : len(params) - 2]
        pairsofparams = cleanedparams.split("&")
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split("=")
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param


def addLink(name, url, iconimage, comment):
    liz = xbmcgui.ListItem(name)
    liz.setArt({"icon": iconimage, "thumb": iconimage})
    liz.setInfo(type="music", infoLabels={"title": name, "comment": comment})
    return xbmcplugin.addDirectoryItem(
        handle=int(sys.argv[1]), url=url, listitem=liz, isFolder=False
    )


def addDir(name, url, mode, iconimage, comment):
    u = f"{sys.argv[0]}?url={urllib.parse.quote_plus(url)}&mode={mode}&name={urllib.parse.quote_plus(name)}"
    liz = xbmcgui.ListItem(name)
    liz.setArt({"icon": "DefaultFolder.png", "thumb": iconimage})
    liz.setInfo(type="music", infoLabels={"title": name, "comment": comment})
    return xbmcplugin.addDirectoryItem(
        handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True
    )


params = get_params()
url = None
name = None
mode = None

try:
    url = urllib.parse.unquote_plus(params["url"])
except:
    url = ""
try:
    name = urllib.parse.unquote_plus(params["name"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass


if mode == None or url == None or len(url) < 1:
    SEZNAM()

elif mode == 1:
    LINK(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
