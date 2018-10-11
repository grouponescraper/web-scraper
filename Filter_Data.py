
# coding: utf-8

# In[390]:


from bs4 import BeautifulSoup
import re


# In[391]:


url_address = 'C:/Users/yingy/Desktop/repository/https..en.wikipedia.org.wiki.PortalBiography.html'
page = open(url_address, encoding = 'UTF-8')
soup = BeautifulSoup(page, 'lxml')


# In[392]:


def remove_nav():
    nav_match = soup.find_all('div',{'id': re.compile('.*nav.*', re.I)}) + soup.find_all('div', {'role': re.compile('.*nav.*', re.I)}) 
    for nm in nav_match:
        nm.decompose()
        
    return soup
    


# In[393]:


def remove_footer():
    footer_match = soup.find_all('div', {'id': re.compile('.*footer.*', re.I)})+ soup.find_all('footer') + soup.find_all('div', {'class': re.compile('.*footer.*')})
    for fm in footer_match:
        fm.decompose()
    return soup


# In[394]:


def filter_tags(text):
    re_script = re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>',re.I)#Script
    re_br = re.compile('<br\s*?/?>') #line break
    re_list = re.compile('<li\s*?/?>') #list
    re_tag = re.compile('</?\w+[^>]*>') #HTML tag
    re_comment = re.compile('<!--[^>]*.*-->') #HTML comment
    re_doctype = re.compile('<!DOCTYPE[^>]*>') #DOCTYPE
    re_blankline = re.compile('\n+')
   
    s = re_script.sub('',text) #remove script
    s = re_br.sub('\n',s) #change br to \n
    s = re_list.sub('\n', s) #chang li to \n
    s = re_tag.sub('',s) #remove HTML tag
    s = re_comment.sub('',s) #remove HTML comment
    s=re_doctype.sub('',s) #remove DOCTYPE
    s=re_blankline.sub('\n',s) #remove extra blank lines
    return s
    
def write_text_file(text):
    with open('output.txt', 'w',encoding='UTF-8') as text_file:
        text_file.write(text)

def run_main():
    remove_nav()
    remove_footer()
    result =filter_tags(str(soup))
    write_text_file(result)


if __name__ == '__main__':
    run_main()

