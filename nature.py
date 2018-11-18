import shutil
import urllib.request
import re
import os


def init_dir():
    repdir = 'repository/'
    if os.path.exists(repdir):
        shutil.rmtree(repdir)
    os.mkdir(repdir)


def repository_fpath(url):
    fpath = re.sub('\W+', '', url)
    fpath = fpath[:100]
    return 'repository/'+fpath+'.html'


def scrape():
    init_dir()
    host = 'https://www.nature.com/articles/srep'
    for i in range(1, 10):
        url = host+str(i).zfill(5)
        res = urllib.request.urlopen(url)
        html = res.read()
        print('writing', url)
        with open(repository_fpath(url), 'wb') as fobj:
            fobj.write(html)



if __name__ == '__main__':
    scrape()



