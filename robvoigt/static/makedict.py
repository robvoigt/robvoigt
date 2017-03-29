import codecs, json
from collections import defaultdict

d=defaultdict(list)

for l in codecs.open('edict.utf8', encoding='utf-8'):
    s = l.split('/')
    w = s[0]
    definition = ', '.join(s[1:]).strip().strip(',')
    if not '[' in w:
        word = w.strip()
        pron = ''
    else:
        word, pron = w.split('[')
        word = word.strip()
        pron = pron.strip().strip(']')

    d[word].append([pron, definition])
    
json.dump(d, codecs.open('edict.json','w',encoding='utf-8'))
