import codecs
from bs4 import BeautifulSoup
from html.parser import HTMLParser
import matplotlib.pyplot as plt
import numpy as np
from os import listdir, getcwd
from os.path import isfile, join



counter = {}
tags = {}
lastTag = ""
myVector = np.zeros(0)
newHTML = []
#tags to ignore as they are usually font related
stopTags = {
    "a": 0,
    "span": 0,
    "i": 0,
    "h1": 0,
    "h2": 0,
    "h3": 0,
    "h4": 0,
    "h5": 0,
    "h6": 0,
    "th": 0,
}

class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        global myVector
        if (not(tag in stopTags)):
            myVector = np.append(myVector, 1)
            newHTML.append('<'+tag+'>')
    def handle_endtag(self, tag):
        global myVector
        if (not(tag in stopTags)):
            myVector = np.append(myVector, 1)
            newHTML.append('</'+tag+'>')
    def handle_data(self, data):
        global myVector
        s = data.split()
        newHTML.extend(s)
        if(len(s) != 0):
            toAdd = np.zeros(len(s))
            myVector = np.append(myVector, toAdd)

def main():
    currDir = getcwd()
    resources = join(currDir, 'resource')
    cleaned = join(currDir, 'cleaned')
    htmlFiles = [f for f in listdir(resources) if isfile(join(resources, f))]
    for fn in htmlFiles:
        resetG()
        cleanPage(fn, resources, cleaned)

def resetG():
    global counter
    counter = {}
    global tags
    tags = {}
    global myVector
    myVector = np.zeros(0)
    global newHTML
    newHTML = []

def cleanPage(fn, r, c):
    rf = join(r, fn)
    cf = join(c, fn)
    f = codecs.open(rf, 'r', 'utf-8')
    soup = BeautifulSoup(f.read(), 'html.parser')
    for script in soup("script"):
        script.decompose()
    f.close()
    #only care about body of page
    para = soup.find('body')
    myStr = str(para)

    parser = MyHTMLParser()
    parser.feed(myStr)

    myMax = maximize(0, myVector.size -1)
    print(myMax)

    tf = codecs.open(cf, "w", 'utf-8')
    tf.write(' '.join(newHTML[myMax[1]: myMax[2]]))
    tf.close()

    #showing token vs tag plot of site
    #comment next block of code out when 
    # toPlot = np.zeros(0)
    # count = 0
    # for index, value in np.ndenumerate(myVector):
    #     if(value == 1):
    #         count += 1
    #     toPlot = np.append(toPlot, (index[0], count))
    # toPlot = np.reshape(toPlot, (-1, 2))
    # p = zip(*toPlot)
    # plt.plot(*p)
    # plt.show()

def maximize(i, j):
    (left, mid, right) = summation(i, j)
    myMax = left+mid+right
    iMax = i
    jMax = j
    threshold = 3
    for x in range(i+1, j):
        if(myVector[x] == 0):
            mid -= 1
            continue
        left += threshold
        tMid = mid
        tRight = right
        for y in range(j, x, -1):
            if(myVector[y] == 0):
                tMid -= 1
                continue
            tRight += threshold
            temp = left + tMid + tRight
            if (temp > myMax):
                myMax = temp
                iMax = x
                jMax = y
    return [myMax, iMax, jMax]

def summation(i, j):
    left = 0
    mid = 0
    right = 0
    for n in range(i-1):
        left += myVector[n] *2
    for n in range(i, j):
        mid += (1 - myVector[n])
    for n in range(j+1, myVector.size-1):
        right += myVector[n] *2
    return (left, mid, right) 
   

if __name__ == "__main__":
    main()