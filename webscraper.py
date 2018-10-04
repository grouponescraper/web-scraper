from bs4 import BeautifulSoup
import threading
import requests
import pprint
import shutil
import socket
import time
import os


from urllib import request



ERR_SHORT = 1
ERR_LONG = 3
MAX_ERRORS = 3

CLOCK_ID = 0
REPOSITORY_TOKEN = '.'
TOTAL_PAGES = 1000


'''

def connect(url):

    def handle_errors(err, url, dur=0):
        # TODO uncomment print msg
        # print(err)
        # print('Resuming in ', dur, 'sec...')
        time.sleep(dur)

    def success_connect(res):
        # TODO uncomment print msg
        # print('Successfully connected to', res.url)
        return BeautifulSoup(res.text, 'lxml'), res

    error_counter = 0
    while error_counter < MAX_ERRORS:
        try:
            res = requests.get(url, timeout=1.0)
            res.raise_for_status()
        except requests.exceptions.ConnectTimeout as err:
            handle_errors(err, url, ERR_SHORT)
        except requests.exceptions.ReadTimeout as err:
            handle_errors(err, url, ERR_SHORT)
        except requests.exceptions.Timeout as err:
            handle_errors(err, url, ERR_LONG)
        except socket.timeout as err:
            handle_errors(err, url, ERR_LONG)
        except requests.exceptions.HTTPError as err:
            handle_errors(err, url, ERR_SHORT)
        except requests.exceptions.TooManyRedirects as err:
            handle_errors(err, url, ERR_SHORT)
        except requests.exceptions.ConnectionError as err:
            handle_errors(err, url, ERR_LONG)
        except requests.exceptions.URLRequired as err:
            handle_errors(err, url, ERR_SHORT)
        except TypeError as err:
            handle_errors(err, url)
        except ValueError as err:
            handle_errors(err, url)
        except AttributeError as err:
            handle_errors(err, url)
        except socket.error as err:
            handle_errors(err, url, ERR_LONG)
        except requests.exceptions.RequestException as err:
            handle_errors(err, url, ERR_LONG)
        else:
            return success_connect(res)
        finally:
            error_counter += 1
    return None, None

'''


def connect(url):

    def get_http_headers():
        version_info = (1, 0, 25)
        __version__ = ".".join(map(str, version_info))
        browser_user_agent = 'Parser/%s' % __version__
        headers = {'User-agent': browser_user_agent}
        return headers

    error_counter = 0
    while error_counter < MAX_ERRORS:
        try:
            req = request.Request(url,
                                  headers=get_http_headers())
            res = request.urlopen(req, timeout=30)
            if res is not None:
                # print('connected to', res.geturl())
                return res
        except Exception as err:
            # print(err, url)
            error_counter += 1
            time.sleep(10)


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


def get_robots_txt(url):
    roburl = url+'/robots.txt'
    if not url.startswith('http'):
        roburl = 'https://'+roburl
    res = connect(roburl)
    if res:
        tree = BeautifulSoup(res.read(), 'lxml')
        return tree.getText()
    return ''


def get_crawl_delay(url):
    # make delay more specific
    # pass dict of delay values
    # return early if val present
    robot_txt = get_robots_txt(url)
    lines = [x for x in robot_txt.split('\n') if x.startswith('Crawl-delay')]
    waits = [int(x.split(':')[1]) for x in lines]
    delay_def = 1
    waits.append(delay_def)
    return max(waits)


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
    if '?lang=' in url:
        return None
    if 'mailto:' in url:
        return None

    if url.startswith('/'):
        return baselink

    if '.' in url:
        htoks = [x for x in url.split('/') if x and '.' in x]
        if len(htoks) > 0:
            link = htoks[0]
            return 'https://' + link
    else:
        return baselink


def shape_link(hostname, link):
    url = link.replace('#', '') \
        .replace('www.', '').replace('http://', 'https://')
    if url.startswith('//'):
        url = 'https:' + url
    elif url.startswith('/'):
        url = url.strip('/')
        url = hostname + '/' + url
    elif url.startswith('.'):
        url = hostname
    elif url == '':
        url = hostname
    if not url.startswith('http'):
        url = 'https://' + url
    return url


def shape_links(url, links):
    for i, a in enumerate(links):
        links[i] = shape_link(url, links[i])
    return links


def scrape_page(url):
    res = connect(url)
    if res:
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


def remove_restricted(links, rstr):
    return list(filter(lambda x: rstr in x, links))


def push_links(baselink, directory, expired, links, restrict):

    # TODO test this more!

    for link in links:
        hostname = get_hostname(baselink, link)
        if hostname is not None:
            if hostname not in directory.keys():
                directory[hostname] = [link]
                thr = threading.Thread(target=run_thread, args=(hostname, directory, expired, restrict))
                thr.start()
            if hostname not in expired.keys():
                expired[hostname] = []
            if link not in directory[hostname] and link not in expired[hostname]:
                directory[hostname].append(link)
            elif link not in expired[hostname]:
                expired[hostname].append(link)


def next_url(links):
    if len(links) > 0:
        return links.pop(0)
    return None


def limit_not_reached():
    global TOTAL_PAGES
    return len(os.listdir('repository/')) < TOTAL_PAGES


def has_url(url):
    return url is not None


def run_thread(hostname, directory, expired, restrict):
    url = directory[hostname].pop(0)
    delay = get_crawl_delay(hostname)
    while limit_not_reached() and has_url(url):
        links = scrape_page(url)
        sec_i = init_loop()
        if links:
            append_page_info(url, links)
            links = remove_restricted(links, restrict)
            push_links(hostname, directory, expired, links, restrict)
        url = next_url(directory[hostname])
        end_loop(delay, sec_i)


def run_main():
    url, pgs, rstr = init_seed('specification.csv')
    links = [url]
    directory = {}
    expired = {}
    global TOTAL_PAGES
    TOTAL_PAGES = pgs
    init_dir()
    push_links(url, directory, expired, links, rstr)

    # while limit_not_reached():
    #     time.sleep(0.5)

    # print('init')
    # time.sleep(10)
    # print('\n')
    # pprint.pprint(directory)
    # print('\n\n')
    # pprint.pprint(expired)
    # print('\n')


if __name__ == '__main__':
    # run()
    run_main()


# http://www.rainymood.com/

