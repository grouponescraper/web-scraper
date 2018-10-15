import lxml
from lxml import html
from lxml.html.clean import Cleaner
from lxml.html import HtmlElement, etree
import matplotlib.pyplot as plt
from urllib import request
from copy import deepcopy
import numpy as np
import shutil
import os
import re


# from extractor import goose_extract


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


def retrieve_html(url):
    raw_html = connect(url)
    return lxml.html.fromstring(raw_html)


def retrieve_doc(fpath):
    with open(fpath, 'rb') as fobj:
        text = fobj.read()
    try:
        doc = lxml.html.fromstring(text)
    except etree.ParserError as err:
        print(err)
        doc = ''
    return doc


PRE_CLEANER = Cleaner(
    scripts=True,
    javascript=True,
    style=True,
    inline_style=True,
    comments=True,
    forms=True,
    frames=True,
    embedded=True,
    # meta=True,
    remove_unknown_tags=True,
    kill_tags=(
        'form',
        'input',
        # 'footer',
        # 'button',
        'embed',
        'textarea',
        # 'img',
        # 'button'
    ),
)


POST_CLEANER = Cleaner(
    remove_tags=(
        'a'
    ),
    kill_tags=(
        'img'
    ),
)


def pre_clean(doc):
    return PRE_CLEANER.clean_html(doc)


def post_clean(doc):
    return POST_CLEANER.clean_html(doc)


def get_fmt_tags():
    return [
        'b', 'em', 'i', 'mark', 's', 'small', 'strong', 'sub', 'sup', 'u'
    ]


def get_struct_tags():
    return [
        'a', 'article', 'body', 'div',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'li', 'ol', 'p', 'q', 'section',
        'span', 'table', 'tbody', 'td',
        'title', 'tr', 'ul'
    ]


'''

def remove_link_dense(doc):
    # TODO remove this?
    if isinstance(doc, HtmlElement):
        remove_nodes = []
        tags = ['div', 'span', 'tr', 'p']
        for node in doc.iter(*tags):
            a_words = float(sum([len(a.text.split()) for a in node.iter('a') if a.text]))
            word_count = float(sum([len(t.text.split()) for t in node.iter() if t.text]))
            if a_words >= word_count != 0:
                remove_nodes.append(node)
        for node in remove_nodes:
            node.getparent().remove(node)
    return doc


def remove_link_tables(doc):
    # TODO remove this?
    if isinstance(doc, HtmlElement):
        remove_nodes = []
        tags = ['table', 'ul', 'ol', 'nav']
        tags.extend(['div', 'span', 'p', 'tr'])
        for node in doc.iter(*tags):
            table = ''.join(node.text_content().split())
            table_sum = float(len(table))
            anchors = [''.join(a.text_content().split()) for a in node.iter('a')]
            anchors_sum = float(sum([len(a) for a in anchors]))
            if anchors_sum >= (3/4*table_sum) != 0:
                remove_nodes.append(node)
        for node in remove_nodes:
            node.getparent().remove(node)
    return doc

'''


def remove_dense_link(doc, fctr=1.0):
    if isinstance(doc, HtmlElement):
        tags = ['div', 'span', 'p', 'tr', 'table', 'ul', 'ol', 'nav']
        remove_nodes = []
        for node in doc.iter(*tags):
            table = ''.join(node.text_content().split())
            table_sum = float(len(table))
            anchors = [''.join(a.text_content().split()) for a in node.iter('a')]
            anchors_sum = float(sum([len(a) for a in anchors]))
            if anchors_sum >= fctr*table_sum and anchors_sum != 0:
                remove_nodes.append(node)
        for node in remove_nodes:
            node.getparent().remove(node)
    return doc


def document_slope_curve(doc):
    # TODO update this to include a list of nodes to delete
    TOKEN_TYPES = {
        'word': 0,
        'format': 0,
        'structure': 1
    }
    tag_struct = get_struct_tags()
    tag_fmt = get_fmt_tags()
    slope = []
    tokens = []
    if isinstance(doc, HtmlElement):
        for node in doc.iter():
            tag, text = node.tag, node.text
            if tag not in tag_fmt:
                slope.append(TOKEN_TYPES['structure'])
                tokens.append(tag)
            else:
                slope.append(TOKEN_TYPES['format'])
                tokens.append(tag)
            text = [] if text is None else text.split()
            if tag in tag_struct and tag is not etree.Comment:
                slope.extend([TOKEN_TYPES['word'] for x in text])
                tokens.extend(text)
        i = 1
        for s, t in zip(slope, tokens):
            print(i, ': ', s, ', ', t, sep='')
            i += 1
        print(len(slope), len(tokens))
    return slope


def doc_slope_display(slope):
    cumslope = np.cumsum(slope)
    plt.plot(cumslope)
    plt.show()


def get_server_regex():
    with open('files/adblock_whitelist.txt', 'rt') as fobj:
        whitelist_txt = fobj.read()
    whitelist_re = re.compile(whitelist_txt)
    with open('files/adblock_blacklist.txt', 'rt') as fobj:
        blacklist_txt = fobj.read()
    blacklist_re = re.compile(blacklist_txt)
    return whitelist_re, blacklist_re


def remove_ad_servers(doc):
    if isinstance(doc, HtmlElement):
        remove_nodes = []
        whitelist_re, blacklist_re = get_server_regex()
        for node in doc.iter():
            attribs = [v for k, v in node.attrib.items() if k in {'rel', 'src', 'href'}]
            for attrib in attribs:
                if not whitelist_re.search(attrib) and blacklist_re.search(attrib):
                    # TODO remove, for debugging
                    remove_nodes.append(node)
        for node in remove_nodes:
            node.getparent().remove(node)
    return doc


def noise_removal(doc):
    if isinstance(doc, HtmlElement):
        doc = pre_clean(doc)
        doc_copy = deepcopy(doc)
        try:
            doc = remove_dense_link(doc, 0.75)
        except AttributeError:
            doc = deepcopy(doc_copy)
        doc = remove_ad_servers(doc)
        doc = post_clean(doc)
    return doc


def format_doc(doc):
    webpage = ''
    for node in doc.iter():
        tag, text = node.tag, node.text
        if text is not None:
            text = text.strip()
            if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                webpage += '\n' + text + '\n'
            elif tag in ['p']:
                webpage += '\n' + text + '\n'
            elif tag in ['div']:
                webpage += '\n' + text
            else:
                webpage += text
    return webpage


'''

def write_html(fpath, doc):
    with open(fpath, 'wb') as fobj:
        try:
            html = etree.tostring(doc, pretty_print=True)
        except TypeError:
            html = b''
        fobj.write(html)

'''


def write_html(fpath, doc):
    with open(fpath+'.txt', 'wt') as fobj:
        try:
            text = etree.tostring(doc)
            text = re.sub('/>', ' />', text)
            doc = lxml.html.fromstring(text)
            text = doc.text_content()
        except AttributeError:
            text = ''
        fobj.write(text)


def init_dir():
    repdir = 'cleaned/'
    if os.path.exists(repdir):
        shutil.rmtree(repdir)
    os.mkdir(repdir)
    return repdir


def denoiser(inpath):
    outpath = 'cleaned/'+inpath.split('/', 1)[-1]
    doc = retrieve_doc(inpath)
    if len(doc) > 0:
        doc = noise_removal(doc)
    write_html(outpath, doc)


def run_main():
    init_dir()
    for path in os.listdir('repository/'):
        print(path)
        denoiser('repository/'+path)


if __name__ == '__main__':
    run_main()


# end of file

