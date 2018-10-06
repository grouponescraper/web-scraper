from collections import OrderedDict
from bs4 import BeautifulSoup
import threading
import requests
import pprint
import shutil
import socket
import time
import sys
import os
import re


from urllib import request


ERR_SHORT = 1
ERR_LONG = 3
MAX_ERRORS = 3

CLOCK_ID = 0
REPOSITORY_TOKEN = '.'
TOTAL_PAGES = 1000
MAX_SUB_THREADS = 10


def get_http_headers():
    version_info = (1, 0, 25)
    __version__ = ".".join(map(str, version_info))
    browser_user_agent = 'superscraper/%s' % __version__
    headers = {'User-agent': browser_user_agent}
    return headers


def connect(url, max_errors=3, retry_time=10):
    error_counter = 0
    while error_counter < max_errors:
        try:
            req = request.Request(url,
                                  headers=get_http_headers())
            res = request.urlopen(req, timeout=60)
            if res is not None:
                print('        ', 'connected to', res.geturl())
                return res
        except Exception as err:
            print('        ', err, url)
            error_counter += 1
            time.sleep(retry_time)


def init_dir():
    report = 'report.html'
    if os.path.exists(report):
        os.remove(report)
    repdir = 'repository/'
    if os.path.exists(repdir):
        shutil.rmtree(repdir)
    os.mkdir(repdir)


def init_seed(path):
    with open(path) as fobj:
        url, pgs, rstr = fobj.readline().strip().split(',')
    if not url.startswith('http'):
        url = 'https://' + url
    pgs = int(pgs) if pgs.isnumeric() else 100
    return url, pgs, rstr


def init_crawler():
    init_dir()
    url, pgs, rstr = init_seed('specification.csv')
    hostname = get_hostname(url, '')
    links = []
    directory = OrderedDict()
    directory[hostname] = [url]
    expired = OrderedDict()
    global TOTAL_PAGES
    TOTAL_PAGES = pgs
    return hostname, directory, expired, links, rstr


def get_robots_txt(url):
    roburl = url+'/robots.txt'
    res = connect(roburl, 1, 0)
    if res:
        tree = BeautifulSoup(res.read(), 'lxml')
        return tree.getText()
    return ''


def get_crawl_restrictions(hostname):

    txt = get_robots_txt(hostname)
    lines = [x.lower() for x in txt.split('\n')]
    user_agent = [i for i, x in enumerate(lines) if x.replace(' ', '') == 'user-agent:*']

    disallowed = []
    for i in user_agent:
        j = 1
        while i+j < len(lines) and not lines[i+j].startswith('user-agent:'):
            line = lines[i+j]
            if line.startswith('disallow:'):
                disallowed.append(hostname+line.lstrip('disallow:').strip())
            j += 1

    delay_def = 3
    delays = [float(x.split(':')[1]) for x in lines if x.startswith('crawl-delay')]
    delays.append(delay_def)
    delay = max(delays)

    return disallowed, delay


def init_loop():
    return time.time()


def end_loop(delay, seci):
    dur_sec = time.time() - seci
    pause_time = max(0, delay-dur_sec)
    time.sleep(pause_time)
    return pause_time


def repository_fpath(url):
    return url.replace('/', REPOSITORY_TOKEN)


def write_html_file(url, tree):
    fpath = repository_fpath(url)
    with open('repository/'+fpath+'.html', 'wt') as fobj:
        fobj.write(str(tree))


def gather_links(html):
    return [a['href'] for a in html.find_all('a') if a.has_attr('href')]


def get_hostname(baselink, url):

    if 'javascript:' in url:
        return None
    elif '?lang=' in url:
        return None
    elif 'mailto:' in url:
        return None
    elif '.php' in url:
        return None

    if re.findall('\(|\)|\{|\}|\| ', url):
        return None

    if url.startswith('/'):
        return baselink
    elif url.startswith('#'):
        return baselink
    elif url.startswith('?'):
        return baselink

    if '.' in url:
        htoks = [x for x in re.split(r'\/|\?|\#', url) if '.' in x]
        if len(htoks) > 0:
            link = htoks[0].strip('/')
            return 'https://' + link
    elif '.' in baselink:
        return baselink


def shape_link(hostname, link):
    url = link.replace('#', '') \
        .replace('www.', '').replace('http://', 'https://')
    if url.startswith('//'):
        url = 'https:' + url
    elif url.startswith('/'):
        url = url.lstrip('/')
        url = hostname + '/' + url
    elif url.startswith('.'):
        url = hostname
    elif url == '':
        url = hostname
    if not url.startswith('http'):
        url = 'https://' + url
    url = url.strip('/')
    return url


def shape_links(url, links):
    for i, a in enumerate(links):
        links[i] = shape_link(url, links[i])
    return links


def scrape_page(url):
    res = connect(url)
    if res:
        # status_code = res.getcode()
        tree = BeautifulSoup(res, 'lxml')
        links = gather_links(tree)
        write_html_file(url, tree)
        return shape_links(url, links)


def append_page_info(url, links):
    with open('report.html', 'at') as fobj:
        fpath = repository_fpath(url)
        numlinks = str(len(links))
        line = '<p>' + \
            '<a href='+url+'>'+url+'</a> ' + \
            '<a href='+'repository/'+fpath+'.html>'+fpath+'</a> ' + \
            numlinks + '</p>'
        fobj.write(line)


def remove_restricted(links, rstr, disallowed):
    # TODO test this more!
    fltrd = []
    for link in links:
        for disallow in disallowed:
            if disallow not in link:
                fltrd.append(link)
    fltrd = list(filter(lambda x: rstr in x, fltrd))
    return fltrd


def push_links(baselink, directory, expired, links, restrict):
    for link in links:
        hostname = get_hostname(baselink, link)
        if hostname is not None:
            if hostname not in directory.keys():
                directory[hostname] = [link]
            if hostname not in expired.keys():
                expired[hostname] = []
            if link not in directory[hostname] and link not in expired[hostname]:
                directory[hostname].append(link)


def next_url(links):
    if len(links) > 0:
        return links.pop(0)
    return None


def limit_not_reached():
    global TOTAL_PAGES
    return len(os.listdir('repository/')) < TOTAL_PAGES


def has_url(url):
    return url is not None


def get_wrapped_list(lst, i):
    pass


def get_sub_threads():
    return [x.name for x in threading.enumerate() if x.name != 'MainThread']


def run_thread(hostname, directory, expired, restrict):
    thr = threading.Thread(target=run_hostname, args=(hostname, directory, expired, restrict))
    thr.setName(hostname)
    thr.start()
    return thr


def run_hostname(hostname, directory, expired, restrict):
    url = next_url(directory[hostname])
    disallowed, delay = get_crawl_restrictions(hostname)
    while limit_not_reached() and has_url(url):
        links = scrape_page(url)
        sec_i = init_loop()
        if links:
            append_page_info(url, links)
            links = remove_restricted(links, restrict, disallowed)
            push_links(hostname, directory, expired, links, restrict)
        expired[hostname].append(url)
        url = next_url(directory[hostname])
        end_loop(delay, sec_i)


def run_main():

    hostname, directory, expired, links, rstr = init_crawler()
    iter = 0
    while limit_not_reached() or threading.active_count() > 1:
        hostnames = list(directory.keys())
        hostnames = hostnames[iter:] + hostnames[:iter]
        for hostname in hostnames:
            if threading.active_count()-1 < MAX_SUB_THREADS and limit_not_reached():
                if len(directory[hostname]) > 0:
                    run_thread(hostname, directory, expired, rstr)
                iter = (iter + 1) % len(hostnames)
            else:
                break
        # print(threading.active_count(), end=' ')
        # time.sleep(1)

    print('\n\n')
    pprint.pprint(directory)
    print('\n\n')
    pprint.pprint(expired)
    print('\n')
    print('goodbye!')


if __name__ == '__main__':
    # run()
    run_main()


