
# coding: utf-8

# In[464]:


import re
import string
from numpy import array
import matplotlib
import matplotlib.pyplot as plt



# In[465]:


doc_address = 'C:/Users/yingy/Desktop/doc1.txt'


# In[466]:


frequency = {}
document_text = open(doc_address, encoding ='utf-8', mode ='r')
text_string= document_text.read().lower()
match_pattern = re.findall(r'\b[a-z]{3,15}\b', str(text_string))


# In[467]:


for word in match_pattern:
    count = frequency.get(word,0)
    frequency[word] = count +1   
    frequency_list = frequency.keys()


# In[468]:


freq_sorted= sorted(frequency.items(), key = lambda x: x[1], reverse =True)
freq_sorted_dict = dict(freq_sorted)
sorted_ranks = freq_sorted_dict.values()
sorted_words = freq_sorted_dict.keys()
ranks =[]
freqs=[]
words =[]
for rank, word in enumerate(freq_sorted_dict):
    ranks.append(rank+1)
    freqs.append(freq_sorted_dict[word])
    words.append(word)

for i in range(0:100):
    print(freq_sorted[i])


# In[469]:


plt.loglog(ranks,freqs, marker='.')
plt.title('Zipf Plot', fontsize =14)
plt.xlabel('Rank', fontsize =14)
plt.ylabel('Frequency', fontsize =14)
plt.grid(True)
for n in list(np.logspace(-0.5, np.log10(len(freqs)-1), 20).astype(int)):
    plt_text = plt.text(ranks[n], freqs[n], ' ' + words[n],
                verticalalignment='bottom', horizontalalignment ='left')
plt.show()


total =0;
for n in freqs:
    total += freqs[n]
print(total)
probs = []
for i in range(0, len(freqs)):
    probs.append(freqs[i]/total)
    
plt.title('Zipf Plot', fontsize =14)
plt.xlabel('Rank', fontsize =14)
plt.ylabel('Probability', fontsize =14)
plt.grid(True)
plt.plot(ranks, probs, linewidth=2,color='r')
plt.show()

