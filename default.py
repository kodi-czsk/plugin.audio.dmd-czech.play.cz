# -*- coding: utf-8 -*-
import re
import urllib

import urllib2
import xbmcaddon
import xbmcgui
# from urlparse import urlparse
import xbmcplugin
from parseutils import *
from stats import *

# import json
# import simplejson as json

__baseurl__ = "http://api.play.cz/xml"
_UserAgent_ = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3"
addon = xbmcaddon.Addon("plugin.audio.dmd-czech.play.cz")
profile = xbmc.translatePath(addon.getAddonInfo("profile"))
__settings__ = xbmcaddon.Addon(id="plugin.audio.dmd-czech.play.cz")
__lang__ = addon.getLocalizedString
home = __settings__.getAddonInfo("path")


def SEZNAM():
    url = "http://api.play.cz/xml/getRadios"
    req = urllib2.Request(url)
    req.add_header(
        "User-Agent",
        " Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3",
    )
    response = urllib2.urlopen(req)
    httpdata = response.read()
    link = response.read()
    response.close()
    match = re.compile(
        "<title>.+?CDATA\[(.+?)\]\]></title>\s<description>.+?CDATA\[(.+?)\]\]></description>\s<shortcut>.+?CDATA\[(.+?)\]\]></shortcut>"
    ).findall(httpdata)
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
    req = urllib2.Request(url)
    req.add_header(
        "User-Agent",
        " Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3",
    )
    response = urllib2.urlopen(req)
    httpdata = response.read()
    link = response.read()
    response.close()
    httpdata = httpdata.replace("\r", "")
    httpdata = httpdata.replace("\n", "")
    httpdata = httpdata.replace("\t", "")
    match = re.compile("<streams>(.+?)</streams>").findall(httpdata)
    for streams in match:
        match2 = re.compile("<(.+?)>(.+?)</loop></").findall(streams)
        for suffix, bitrates in match2:
            bitrates = bitrates + "</loop>"
            match3 = re.compile("<loop>.+?CDATA\[(.+?)\]\]></loop>").findall(bitrates)
            if suffix != "wma":
                for bitrate in match3:
                    addLink(
                        suffix + " " + bitrate + " kbps",
                        "http://api.play.cz/plain/getStream/"
                        + shortcut
                        + "/"
                        + suffix
                        + "/"
                        + bitrate,
                        "http://api.play.cz/static/radio_logo/t200/"
                        + shortcut
                        + ".png",
                        "",
                    )
            else:
                for bitrate in match3:
                    url = (
                        "http://api.play.cz/xml/getStream/"
                        + shortcut
                        + "/"
                        + suffix
                        + "/"
                        + bitrate
                    )
                    req = urllib2.Request(url)
                    req.add_header(
                        "User-Agent",
                        " Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3",
                    )
                    response = urllib2.urlopen(req)
                    httpdata = response.read()
                    link = response.read()
                    response.close()
                    httpdata = httpdata.replace("\r", "")
                    httpdata = httpdata.replace("\n", "")
                    httpdata = httpdata.replace("\t", "")
                    match = re.compile(
                        "<pubpoint>.+?CDATA\[(.+?)\]\]></pubpoint>"
                    ).findall(httpdata)
                    for stream in match:
                        addLink(
                            suffix + " " + bitrate + " kbps",
                            stream,
                            "http://api.play.cz/static/radio_logo/t200/"
                            + shortcut
                            + ".png",
                            "",
                        )


def http_build_query(params, topkey=""):
    from urllib import quote_plus

    if len(params) == 0:
        return ""

    result = ""

    # is a dictionary?
    if type(params) is dict:
        for key in params.keys():
            newkey = quote_plus(key)

            if topkey != "":
                newkey = topkey + quote_plus("[" + key + "]")

            if type(params[key]) is dict:
                result += http_build_query(params[key], newkey)

            elif type(params[key]) is list:
                i = 0
                for val in params[key]:
                    if type(val) is dict:
                        result += http_build_query(val, newkey + "[" + str(i) + "]")

                    else:
                        result += (
                            newkey
                            + quote_plus("[" + str(i) + "]")
                            + "="
                            + quote_plus(str(val))
                            + "&"
                        )

                    i = i + 1

            # boolean should have special treatment as well
            elif type(params[key]) is bool:
                result += newkey + "=" + quote_plus(str(int(params[key]))) + "&"

            # assume string (integers and floats work well)
            else:
                try:
                    result += (
                        newkey + "=" + quote_plus(str(params[key])) + "&"
                    )  # OPRAVIT ... POKUD JDOU U params[key] ZNAKY > 128, JE ERROR, ALE FUNGUJE TO I TAK
                except:
                    result += newkey + "=" + quote_plus("") + "&"

    # remove the last '&'
    if (result) and (topkey == "") and (result[-1] == "&"):
        result = result[:-1]

    return result


def get_params():
    param = []
    paramstring = sys.argv[2]
    # print "PARAMSTRING: "+urllib.unquote_plus(paramstring)
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
    ok = True
    liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo(type="Audio", infoLabels={"Title": name, "Plot": comment})
    ok = xbmcplugin.addDirectoryItem(
        handle=int(sys.argv[1]), url=url, listitem=liz, isFolder=False
    )
    return ok


def addDir(name, url, mode, iconimage, comment):
    u = (
        sys.argv[0]
        + "?url="
        + urllib.quote_plus(url)
        + "&mode="
        + str(mode)
        + "&name="
        + urllib.quote_plus(name)
    )
    ok = True
    liz = xbmcgui.ListItem(
        name, iconImage="DefaultFolder.png", thumbnailImage=iconimage
    )
    liz.setInfo(type="Audio", infoLabels={"Title": name, "Comment": comment})
    ok = xbmcplugin.addDirectoryItem(
        handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True
    )
    return ok


params = get_params()
url = None
name = None
mode = None

try:
    url = urllib.unquote_plus(params["url"])
except:
    url = ""
try:
    name = urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass

# print "Mode: "+str(mode)
# print "URL: "+str(url)
# print "Name: "+str(name)

if mode == None or url == None or len(url) < 1:
    # print ""
    STATS("SEZNAM", "Function")
    SEZNAM()

elif mode == 1:
    # print ""+url
    STATS(name, "Item")
    LINK(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
