__author__ = 'rjewing'

import feedparser
from email.mime.text import MIMEText
import smtplib
import os
import time

# KEYWORDS - The key should be the section to search, the value should be a dict
# with the keyword to search for and the value should be either a list in the
# format [[list_of_cities], seller, {'constraints': value,}]
# seller is either o(owner), d(dealer), a(both)
KEYWORDS = {
    'cars': {'matrix': [['eugene', 'portland', 'eastoregon', 'corvallis', 'salem',
                         'roseburg', 'seattle', 'bend', 'medford', 'oregoncoast',
                         'yakima'], 'a', {'maxAsk': 8500, 'autoMaxYear': 2009, 'minAsk': 1000}],
             'scion xa': [['eugene', 'portland', 'corvallis', 'salem',
                         'roseburg', 'bend', 'medford', 'oregoncoast',],
                          'a', {'maxAsk': 8500, 'autoMaxYear': 2009, 'minAsk': 1000}],
             'mazda 3': [['eugene', 'portland', 'eastoregon', 'corvallis', 'salem',
                         'roseburg', 'seattle', 'bend', 'medford', 'oregoncoast',
                         'yakima'], 'a', {'maxAsk': 8500, 'autoMaxYear': 2009,
                                          'autoMinYear': 2004, 'minAsk': 1000}],
             'hyundai elantra touring': [['eugene', 'portland', 'eastoregon', 'corvallis', 'salem',
                         'roseburg', 'seattle', 'bend', 'medford', 'oregoncoast',
                         'yakima'], 'a', {'maxAsk': 8500, 'autoMaxYear': 2009, 'minAsk': 1000}],
             'scion xd': [['eugene', 'portland', 'eastoregon', 'corvallis', 'salem',
                         'roseburg', 'seattle', 'bend', 'medford', 'oregoncoast',
                         'yakima'], 'a', {'maxAsk': 9000, 'autoMaxYear': 2009, 'minAsk': 1000}],
             'ford focus wagon': [['eugene', 'portland', 'corvallis', 'salem',
                         'roseburg', 'bend', 'medford', 'oregoncoast',],
                                   'a', {'maxAsk': 8500, 'autoMinYear': 2005,
                                          'autoMaxYear': 2009, 'minAsk': 1000}]},
    'photo': {'nikon': [['eugene', 'corvallis'], 'a', {'maxAsk': 350}],
              'cannon': [['eugene', 'corvallis'], 'a', {'maxAsk': 350}]}
}

CATEGORY_MAPPER = {
    'cars': 'ct',
    'photo': 'ph'
}
SEND_TO = os.environ['GMAIL']
EXISTING_LINKS_FILE = "/Users/rjewing/PycharmProjects/craigslist_finder/existing_links.txt"

URL_TEMPLATE = "http://{city}.craigslist.org/search/{category}{seller}?query={keyword}&format=rss"

def send_email(links_dict):
    body = ''

    for keyword, v in links_dict.iteritems():
        if v:
            section = '<h1>{}</h1>'.format(keyword.encode('utf-8'))
            for city, links in v.iteritems():
                section = section + '<h3>{}</h3>'.format(city.encode('utf-8'))
                for link, title in links:
                    if [link, title] == links[-1]:
                        section = section + '<a href="{link}">{link}</a> - {title}' \
                                            '<br><br>'.format(link=link.encode('utf-8'),
                                                              title=title.encode('utf-8'))
                    else:
                        section = section + '<a href="{link}">{link}</a> - {title}' \
                                            '<br>'.format(link=link.encode('utf-8'),
                                                          title=title.encode('utf-8'))

            body = body + section

    msg = MIMEText(body, 'html')

    msg['Subject'] = "New Craigslists ads"
    msg['From'] = os.environ['GMAIL']
    msg['To'] = SEND_TO

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(os.environ['GMAIL'], os.environ['GMAIL_PASS'])
    s.sendmail(os.environ['GMAIL'], SEND_TO, msg.as_string())
    s.quit()

def fetch_rss(url):
    feed = feedparser.parse(url)

    if getattr(feed, 'status', False) != 200:
        return False
    else:
        return feed['entries']

def get_existing_links():
    links = []
    with open(EXISTING_LINKS_FILE, 'r') as f:
        contents = f.readlines()

    for l in contents:
        links.append(l.rstrip('\n'))
    return links

def update_existing_links(links):
    with open(EXISTING_LINKS_FILE, 'w') as f:
        f.write('\n'.join(i for i in links))

def parse_links(url, existing_links):
    entries = fetch_rss(url)
    l = []

    if entries:
        for entry in entries:
            link = entry.get('link', None)
            title = entry.get('title', None)

            if not link:
                break
            elif existing_links and link in existing_links:
                if l:
                    existing_links.remove(str(link))
                break

            l.append([link, title])

    if l:
        existing_links.append(l[0][0])
    return l


def main():
    new_links = False
    links_dict = {}
    existing_links = get_existing_links()

    for category, v in KEYWORDS.iteritems():

        category = CATEGORY_MAPPER[category]

        for keyword, search_terms in v.iteritems():
            links_dict[keyword] = {}
            for city in search_terms[0]:

                url = URL_TEMPLATE.format(**{'city': city, 'category': category,
                                             'seller': search_terms[1],
                                             'keyword': keyword.replace(' ',
                                                                        '+')})

                # add search constraints to url
                for k, v in search_terms[2].iteritems():
                    url = url + '&{}={}'.format(k, v)

                l = parse_links(url, existing_links)
                if l:
                    new_links = True
                    links_dict[keyword][city] = l

    if new_links:
        send_email(links_dict)

    update_existing_links(existing_links)

    # make sure program runs for at least 10 sec so launchd doesn't freak out
    time.sleep(10)

if __name__ == '__main__':
    main()