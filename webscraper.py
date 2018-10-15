from collections import OrderedDict
from bs4 import BeautifulSoup
from urllib import request
import threading
import shutil
import time
import os
import re


ERR_SHORT = 1
ERR_LONG = 3
MAX_ERRORS = 3

CLOCK_ID = 0
REPOSITORY_TOKEN = '.'
TOTAL_PAGES = 1000
MAX_SUB_THREADS = 25


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
                print('            ', 'connected to', res.geturl())
                return res
        except Exception:
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
    pgs = int(pgs) if pgs.isnumeric() else TOTAL_PAGES
    return url, pgs, rstr


def init_crawler():
    init_dir()
    url, pgs, rstr = init_seed('specification.csv')
    hostname = get_hostname(url, '')
    directory = OrderedDict()
    directory[hostname] = [url]
    expired = OrderedDict()
    global TOTAL_PAGES
    TOTAL_PAGES = pgs
    return hostname, directory, expired, rstr


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
    delays = []
    for i in user_agent:
        j = 1
        while i+j < len(lines) and not lines[i+j].startswith('user-agent:'):
            line = lines[i+j]
            if line.startswith('disallow:'):
                disallowed.append(hostname+line.lstrip('disallow:').strip())
            if line.startswith('crawl-delay:'):
                delays.append(float(line.lstrip('crawl-delay:')))
            j += 1

    delay_def = 1
    # delay_def = 3
    delays.append(delay_def)
    delay = max(delays)
    return disallowed, delay


def init_loop():
    return time.time()


def end_loop(delay, seci):
    # dur_sec = time.time() - seci
    # pause_time = max(0, delay-dur_sec)

    while time.time() < delay + seci and limit_not_reached():
        time.sleep(1)

    # return pause_time


def repository_fpath(url):
    fpath = re.sub('\W+', '', url)
    fpath = fpath[:100]
    return fpath


def write_html_file(url, tree):
    fpath = repository_fpath(url)
    with open('repository/'+fpath+'.html', 'wt') as fobj:
        fobj.write(str(tree))


def gather_links(html):
    return [a['href'] for a in html.find_all('a') if a.has_attr('href')]


def get_hostname(baselink, resource):
    remove = ['javascript:', '?lang=', 'mailto:', '.php', '.asp', '{', '}']
    if any(r in resource for r in remove):
        return None

    def tokenize(link):
        lnk = [x for x in re.split('/|#|\|| ', link.strip()) if '.' in x]
        if lnk:
            return 'https://' + lnk[0]

    rsrc = tokenize(resource)
    if rsrc:
        return rsrc
    blnk = tokenize(baselink)
    if blnk:
        return blnk


def shape_link(baselink, resource):
    hostname = get_hostname(baselink, baselink)
    url = re.sub('www.|http:|https:|/$|#$', '', resource.strip())
    if url.startswith('//'):
        url = 'https:' + url
    elif url.startswith(('/', '?', '#', '.')):
        url = hostname + url
    elif url.startswith(('.', 'javascript:')) or not url:
        url = hostname
    elif url[0].isalnum():
        url = hostname+'/'+url
    return url


def shape_links(url, links):
    for i, a in enumerate(links):
        links[i] = shape_link(url, links[i])
    return links


def get_imgs(tree):
    return len([i for i in tree.find_all('img')])


def scrape_page(res, url):
    # res = connect(url, 1, 0)
    if res:
        tree = BeautifulSoup(res, 'lxml')
        links = gather_links(tree)
        imgs = get_imgs(tree)
        write_html_file(url, tree)
        return shape_links(url, links), imgs
    return [], 0


def table_res_head():
    with open('report.html', 'at') as fobj:
        line = '<table><tr>' + \
            '<th>Weblink</th> ' + \
            '<th>Local File</th> ' + \
            '<th>Response Code</th> ' + \
            '<th>Num Out Links</th> ' + \
            '<th>Num Images</th></tr>'
        fobj.write(line)


def table_res_tail():
    with open('report.html', 'at') as fobj:
        fobj.write('</table>')


def append_page_info(res, url, links, imgs):
    with open('report.html', 'at') as fobj:
        fpath = repository_fpath(url)
        numlinks = str(len(links))
        line = '<tr>' + \
            '<th><a href='+url+'>'+url+'</a></th> ' + \
            '<th><a href='+'repository/'+fpath+'.html>'+fpath+'</a></th> ' + \
            '<th>'+str(res.getcode())+'</th> '+ \
            '<th>'+numlinks + '</th> ' + \
            '<th>'+str(imgs) + '</th></tr>'
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
                directory[hostname] = []
            if hostname not in expired.keys():
                expired[hostname] = []
            if link not in directory[hostname] and link not in expired[hostname]:
                directory[hostname].append(link)


def next_url(links):
    if len(links) > 0:
        return links.pop(0)
    return None


def limit_not_reached():
    return len(os.listdir('repository')) < TOTAL_PAGES


def has_url(url):
    return url is not None


def get_sub_threads():
    return [x.name for x in threading.enumerate() if x.name != 'MainThread']


def run_thread(hostname, directory, expired, restrict):
    thr = threading.Thread(target=run_hostname, args=(hostname, directory, expired, restrict))
    thr.setName(hostname)
    thr.start()
    return thr


def run_hostname(hostname, directory, expired, restrict):
    url = next_url(directory[hostname])
    expired[hostname] = [url]
    disallowed, delay = get_crawl_restrictions(hostname)
    while limit_not_reached() and has_url(url):
        res = connect(url, 1, 0)
        sec_i = init_loop()
        links, imgs = scrape_page(res, url)
        if res:
            append_page_info(res, url, links, imgs)
            links = remove_restricted(links, restrict, disallowed)
            push_links(hostname, directory, expired, links, restrict)
        expired[hostname].append(url)
        url = next_url(directory[hostname])
        end_loop(delay, sec_i)


def run_main():
    hostname, directory, expired, rstr = init_crawler()
    iter = 0
    table_res_head()
    while limit_not_reached() or threading.active_count() > 1:
        hostnames = list(directory.keys())
        hostnames = hostnames[iter:] + hostnames[:iter]
        for hostname in hostnames:
            if threading.active_count()-1 < MAX_SUB_THREADS and limit_not_reached():
                if len(directory[hostname]) > 0 and hostname not in get_sub_threads():
                    run_thread(hostname, directory, expired, rstr)
                iter = (iter + 1) % len(hostnames)
            else:
                break
        time.sleep(1)
    table_res_tail()


if __name__ == '__main__':
    run_main()

