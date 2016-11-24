# WebSearch
# Jonathan Gordon

import sys
import urllib
import requests
import json


class WebSearch:
    def __init__(self, site='google', key=None, cx=None):
        self.site = site
        self.key = key
        self.cx = cx

    def search(self, query, limit=10, offset=0):
        if offset >= limit:
            return []

        if self.site in ['bingweb', 'bingcomposite']:
            results = self.search_bing(query, limit, offset)
        elif self.site == 'google':
            results = self.search_google(query, limit, offset)
        else:
            print('Invalid site', self.site, file=sys.stderr)
            return []

        if results == []:
            return []

        return results + self.search(query, limit=limit,
                                     offset=offset + len(results))


    def search_bing(self, query, limit=50, offset=0):
        if self.site == 'bingweb':
            url = 'https://api.datamarket.azure.com/Bing/SearchWeb/v1/Web'
        elif self.site == 'bingcomposite':
            url = 'https://api.datamarket.azure.com/Bing/Search/v1/Composite'
        else:
            print('Invalid site', self.site, file=sys.stderr)
            return []

        url += '?Query=' + urllib.parse.quote("'{}'".format(query))
        url += '&$skip={}&$format=JSON'.format(offset)

        if self.site == 'bingcomposite':
            url += '&Sources=web'

        r = requests.get(url, auth=('', self.key))

        try:
            j = r.json()
        except (ValueError, KeyError):
            print('WebSearch Error: HTTP %s\n%s' % (r.status_code, r.text),
                  file=sys.stderr)
            return []

        return [WebPage(x) for x in j['d']['results']][:limit - offset]


    def search_google(self, query, limit=10, offset=0):
        if not self.cx:
            print('WebSearch Error: Google Search requires a CX ID.',
                  file=sys.stderr)
            return []

        url = 'https://www.googleapis.com/customsearch/v1'
        vals = {'cx': self.cx,
                'key': self.key,
                'q': query,
                'num': 10}

        if offset != 0:
            vals['start'] = offset

        r = requests.get(url, params=vals)
        try:
            j = json.loads(r.text)
            results = j['items']
        except (ValueError, KeyError):
            print('WebSearch Error: HTTP %s\n%s' % (r.status_code, r.text),
                  file=sys.stderr)
            return []

        return [WebPage(x) for x in results][:limit - offset]



class WebPage:
    def __init__(self, j):
        self.url = None
        self.title = None

        try:
            if 'link' in j:
                self.url = j['link']
            elif 'Url' in j:
                self.url = j['Url']
            else:
                print('WebPage has no URL.', j, file=sys.stderr)
                return None

            if 'title' in j:
                self.title = j['title']
            elif 'Title' in j:
                self.title = j['Title']
            else:
                print('WebPage has no title.', j, file=sys.stderr)
                return None

            if 'snippet' in j:
                self.description = j['snippet']
        except:
            print('WebPage Error: Bad JSON:', file=sys.stderr)
            print(j, file=sys.stderr)
