from bs4 import BeautifulSoup
import requests
import socket
import time
import os


def connect(url):

    ERR_SHORT = 10
    ERR_LONG = 30
    MAX_ERRORS = 10

    error_counter = 0

    def handle_errors(err, url, dur=0):
        print(err)
        print('Resuming in ', dur, 'sec...')
        time.sleep(dur)

    def success_connect(res):
        print('Successfully connected to', res.url)
        return BeautifulSoup(res.text, 'lxml'), res

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


def init_seed(path):
    with open(path) as fobj:
        url, pgs, rstr = fobj.readline().split(',')
    if not url.startswith('http'):
        url = 'http://' + url
    pgs = int(pgs) if pgs.isnumeric() else 100
    return url, pgs, rstr


def get_robots(url):
    roburl = url+'/robots.txt'
    if not url.startswith('http'):
        roburl = 'https://'+roburl
    bs, res = connect(roburl)
    return bs.getText()


def get_crawl_delay(url, delay=1):
    # make delay more specific
    robot_txt = get_robots(url)
    lines = [x for x in robot_txt.split('\n') if x.startswith('Crawl-delay')]
    waits = [int(x.split(':')[1]) for x in lines]
    waits.append(delay)
    return max(waits)


def gather_links(url, html):
    # html, res = connect(url)
    links = []
    for a in html.find_all('a'):
        if a.has_attr('href'):
            a = a['href']
            if a.startswith('//'):
                a = 'http:'+a
            elif a.startswith('/'):
                a = url+a
            links.append(a)
    return links


def write_html(url, res):
    fpath = url.replace('/', '.')
    with open('repository/'+fpath+'.html', 'wt') as fobj:
        fobj.write(res.text)


def scrape_page(url):
    html, res = connect(url)
    if html:
        write_html(url, res)
        links = gather_links(url, html)
        return links
    return []


def run():
    url, pgs, rstr = init_seed('specification.csv')
    links = []

    delay = get_crawl_delay(url)
    delay = 1

    while len(os.listdir('repository/')) < pgs:

        # init time, subtract max(delay-time_taken, 0)

        lnk = scrape_page(url)
        links.extend(lnk)
        url, links = links[0], links[1:]
        time.sleep(delay)

        print(url)


if __name__ == '__main__':
    run()

