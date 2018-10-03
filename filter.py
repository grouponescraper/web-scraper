import lxml
from lxml import html as html
from lxml.html import HtmlElement
from lxml.html.clean import Cleaner
from urllib import request


def connect(url):

    def get_http_headers():
        version_info = (1, 0, 25)
        __version__ = ".".join(map(str, version_info))
        browser_user_agent = 'Parser/%s' % __version__
        headers = {'User-agent': browser_user_agent}
        return headers

    try:
        req = request.Request(url,
                              headers=get_http_headers())
        res = request.urlopen(req, timeout=30)
        if res is not None:
            return res.read()
    except Exception as err:
        print(err)


def extract_html(url):
    raw_html = connect(url)
    return lxml.html.fromstring(raw_html)


def clean(doc):
    return Cleaner(
        scripts=True,
        javascript=True,
        style=True,
        comments=True,
        forms=True,
        frames=True,
        embedded=True,
        meta=True,
        remove_unknown_tags=True,
        kill_tags=(
            'img'
        ),
    ).clean_html(doc)


def noise_removal(url):
    doc = extract_html(url)
    if isinstance(doc, HtmlElement):
        doc = clean(doc)
    return doc


def run_main():
    url = 'https://edition.cnn.com/2012/02/22/world/europe/uk-occupy-london/index.html'
    doc = noise_removal(url)
    print(doc.text_content())


if __name__ == '__main__':
    run_main()


# end of file

