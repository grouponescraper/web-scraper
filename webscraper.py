from bs4 import BeautifulSoup
import requests
import shutil
import socket
import time
import os


ERR_SHORT = 10
ERR_LONG = 30
MAX_ERRORS = 10

CLOCK_ID = 0

REPOSITORY_TOKEN = '.'


def connect(url):

    def handle_errors(err, url, dur=0):
        print(err)
        print('Resuming in ', dur, 'sec...')
        time.sleep(dur)

    def success_connect(res):
        print('Successfully connected to', res.url)
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
    bs, res = connect(roburl)
    return bs.getText()


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
    return time.clock_gettime(CLOCK_ID)


def end_loop(delay, seci):
    dur_sec = time.clock_gettime(CLOCK_ID) - seci
    pause_time = max(0, delay-dur_sec)
    time.sleep(pause_time)
    return pause_time


def repository_fpath(url):
    return url.replace('/', REPOSITORY_TOKEN)


def write_html_file(url, res):
    fpath = repository_fpath(url)
    with open('repository/'+fpath+'.html', 'wt') as fobj:
        fobj.write(res.text)


def gather_links(html):
    return [a['href'] for a in html.find_all('a') if a.has_attr('href')]


def shape_links(url, links):
    for i, a in enumerate(links):
        if a.startswith('//'):
            links[i] = 'https:' + a
        elif a.startswith('/'):
            links[i] = url + a
    return links


def scrape_page(url):
    html, res = connect(url)
    if html:
        write_html_file(url, res)
        links = gather_links(html)
        return shape_links(url, links)
    return []


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


def next_links(links, lnk):
    links.extend(lnk)
    return links.pop(0)


def limit_not_reached(pages):
    return len(os.listdir('repository/')) < pages


def run():
    init_dir()
    url, pgs, rstr = init_seed('specification.csv')

    links = []
    directory = {}

    while limit_not_reached(pgs):
        sec_i = init_loop()
        # delay = get_crawl_delay(url)
        delay = 1
        lnk = scrape_page(url)
        append_page_info(url, lnk)
        lnk = remove_restricted(lnk, rstr)
        url = next_links(links, lnk)
        end_loop(delay, sec_i)


if __name__ == '__main__':
    run()


# http://www.rainymood.com/

