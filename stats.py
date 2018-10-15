import matplotlib.pyplot as plt
import pprint
import string
import math
import os
import re


def read_file(path):
    with open(path, 'rt') as fobj:
        file = fobj.read()
    return file


def remove_non_alpha(raw_text):
    if isinstance(raw_text, str):
        text = raw_text.translate(str.maketrans('', '', string.punctuation))
        # text = re.sub('\W+', ' ', text)
        text = re.sub('[^a-zA-Z]', ' ', text)
        text = text.lower()
        return text
    return ''


def index_text(text):
    index = {}
    if isinstance(text, str):
        for w in text.split():
            if w in index.keys():
                index[w] += 1
            else:
                index[w] = 1
    return index


def index_add_text(index, text):
    if isinstance(text, str):
        for w in text.split():
            if w in index.keys():
                index[w] += 1
            else:
                index[w] = 1
    return index


def get_all_words(*wordlists):
    words = []
    for w in wordlists:
        if isinstance(w, dict):
            w = w.keys()
        words += w
    return list(set(words))


def compare_texts(a, b):
    c = {}
    words = get_all_words(a, b)
    for w in words:
        c[w] = 0
        if w in a.keys():
            c[w] = a[w]
        if w in b.keys():
            c[w] = abs(c[w] - b[w])
    return c


def order_index(index):
    zipf = sorted(index.items(), key=lambda i: (1/i[1], i[0]))
    return zipf


def plot_zipf(index):
    dstr_unc = [i for _, i in index]
    plt.plot(dstr_unc)
    plt.show()


def plot_zipf_detail(index):
    dstr_unc = [i for _, i in index]
    plt.title('Zipf Plot', fontsize=14)
    plt.xlabel('Rank', fontsize=14)
    plt.ylabel('Frequency', fontsize=14)
    plt.grid(True)
    plt.plot(dstr_unc, linewidth=2, color='r')
    plt.show()
    plt.title('Log Zipf Plot', fontsize=14)
    plt.xlabel('Rank', fontsize=14)
    plt.ylabel('Log Frequency', fontsize=14)
    plt.grid(True)
    plt.loglog(dstr_unc, linewidth=2, color='b')
    plt.show()


def run_stats():
    raw_text = read_file('files/schopenhauer.txt')
    text = remove_non_alpha(raw_text)
    index = index_text(text)
    # idiff = compare_texts(index, index)
    # print(idiff)
    zipf = order_index(index)
    pprint.pprint(zipf)
    plot_zipf(zipf)


def write_freq(fpath, index):
    with open(fpath, 'wt') as fobj:
        for i, (k, v) in enumerate(index):
            fobj.write(str(i) + ': ' + str(v) + ' ' + str(k) + '\n')


def run_main():
    index = {}
    bpath = 'cleaned/'
    for path in os.listdir(bpath):
        text = read_file(bpath+path)
        text = remove_non_alpha(text)
        index_add_text(index, text)
    zipf = order_index(index)
    pprint.pprint(zipf)
    write_freq('index.txt', zipf)
    plot_zipf_detail(zipf)


if __name__ == '__main__':
    run_main()

