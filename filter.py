import lxml
from lxml import html
from lxml.html import HtmlElement, etree
from lxml.html.clean import Cleaner
from urllib import request
import re
import matplotlib.pyplot as plt
import numpy as np


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


def clean(doc):
    return Cleaner(
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
            'footer',
            'button',
            'embed',
            'textarea',
            # 'img',
            # 'button'
        ),
        # remove_tags=(
        #     'span'
        # ),
    ).clean_html(doc)


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
                # print(word_count, [t.text.split() for t in node.iter() if t.text])
                # print(a_words, [a.text.split() for a in node.iter('a') if a.text])
                # print('\n')
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


def remove_dense_link(doc, fctr=1.0):
    if isinstance(doc, HtmlElement):
        tags = ['div', 'span', 'p', 'tr', 'table', 'ul', 'ol', 'nav']
        remove_nodes = []
        for node in doc.iter(*tags):
            table = ''.join(node.text_content().split())
            table_sum = float(len(table))
            anchors = [''.join(a.text_content().split()) for a in node.iter('a')]
            anchors_sum = float(sum([len(a) for a in anchors]))
            if anchors_sum >= fctr*table_sum != 0:
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


def noise_removal(url):
    doc = retrieve_html(url)
    if isinstance(doc, HtmlElement):
        doc = clean(doc)
        doc = remove_dense_link(doc, 0.75)
    return doc


def run_main():
    url = 'https://edition.cnn.com/2012/02/22/world/europe/uk-occupy-london/index.html'
    # url = 'https://en.wikipedia.org/wiki/Peter_and_Paul_Fortress'

    # doc = retrieve_html(url)
    # slope = document_slope_curve(doc)
    # cumslope = np.cumsum(slope)
    # plt.plot(cumslope)
    # plt.show()

    doc = noise_removal(url)

    print('')
    for node in doc.iter():
        print(node.tag, node.text)
    print('\n')


if __name__ == '__main__':
    run_main()


# end of file

