# -*- coding: utf-8 -*-                                                                                   
import sys, codecs, string, subprocess, os
from robvoigt import app, db
from collections import defaultdict
from models import Tango

my_env = os.environ
my_env['PYTHONIOENCODING'] = 'utf-8'


reload(sys)
sys.setdefaultencoding('utf-8')

ranges = [
  {"from": ord(u"\u3300"), "to": ord(u"\u33ff")},         # compatibility ideographs                     
  {"from": ord(u"\ufe30"), "to": ord(u"\ufe4f")},         # compatibility ideographs                     
  {"from": ord(u"\uf900"), "to": ord(u"\ufaff")},         # compatibility ideographs                     
  {"from": ord(u"\U0002F800"), "to": ord(u"\U0002fa1f")}, # compatibility ideographs                     
  {"from": ord(u"\u30a0"), "to": ord(u"\u30ff")},         # Japanese Kana                                
  {"from": ord(u"\u3041"), "to": ord(u"\u309c")},         # Japanese hiragana                            
  {"from": ord(u"\u2e80"), "to": ord(u"\u2eff")},         # cjk radicals supplement                      
  {"from": ord(u"\u4e00"), "to": ord(u"\u9fff")},
  {"from": ord(u"\u3400"), "to": ord(u"\u4dbf")},
  {"from": ord(u"\U00020000"), "to": ord(u"\U0002a6df")},
  {"from": ord(u"\U0002a700"), "to": ord(u"\U0002b73f")},
  {"from": ord(u"\U0002b740"), "to": ord(u"\U0002b81f")},
  {"from": ord(u"\U0002b820"), "to": ord(u"\U0002ceaf")}  # included as of Unicode 8.0      
]

usable_pos = [u'名詞',u'動詞',u'形容詞',u'副詞']



def smart_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Returns a bytestring version of 's', encoded as specified in 'encoding'.
    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if strings_only and isinstance(s, (types.NoneType, int)):
        return s
    elif not isinstance(s, basestring):
        try:
            return str(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                # An Exception subclass containing non-ASCII data that doesn't
                # know how to print itself properly. We shouldn't raise a
                # further exception.
                return ' '.join([smart_str(arg, encoding, strings_only,
                        errors) for arg in s])
            return unicode(s).encode(encoding, errors)
    elif isinstance(s, unicode):
        return s.encode(encoding, errors)
    elif s and encoding != 'utf-8':
        return s.decode('utf-8', errors).encode(encoding, errors)
    else:
        return s

def is_cjk(char):
    return any([range["from"] <= ord(char) <= range["to"] for range in ranges])

def do_tango_es(text, max_freq=1000, min_count=2, es_to_en=True, en_to_es=True):
    if not isinstance(text, unicode):
        text = unicode(text, errors='ignore')
    freq = set([])
    for l in codecs.open(os.path.join(app.static_folder, 'internet-es.num'), encoding='utf-8'):
        num, count, word = l.strip().split()
        if int(num) > max_freq: break
        freq.add(word)
    counts = defaultdict(int)
    for l in text.splitlines():
        output = subprocess.check_output("echo %s | /root/software/treetagger/cmd/tree-tagger-spanish" %str(l), shell=True)
        for o in output.splitlines():
            try:
                word, pos, lemma = o.strip().split('\t')
            except:
                continue

            if lemma == '<unknown>': continue
            tango = TangoES.query.get(lemma)
            if tango:
                counts[lemma] += 1
            else:
                tango = TangoES.query.get(word)
                if tango:
                    counts[word] += 1
            

    flashcards = ''
    for i in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        word, count = i
        if count < min_count: continue # skip infrequent
        tango = Tango.query.get(word)
        if not tango: continue

        definition = tango.entry.strip()
        if es_to_en:
            flashcards += '%s \t %s\n' %(word, definition)
        if en_to_es:
            flashcards += '%s \t %s\n' %(definition, word)            
    return flashcards



def do_tango(text, max_freq=1000, min_count=2, no_kana=True, no_gana=False, jp_to_en=True, en_to_jp=True):
    if not isinstance(text, unicode):
        text = unicode(text, errors='ignore')
    freq = set([])
    for l in codecs.open(os.path.join(app.static_folder, 'internet-jp.num'), encoding='utf-8'):
        num, count, word = l.strip().split()
        if int(num) > max_freq: break
        freq.add(word)
    counts = defaultdict(int)
    for l in text.splitlines():
        cjk = ''.join([ch for ch in l if is_cjk(ch)]).strip()
        if len(cjk) == 0: continue
        output = subprocess.check_output("echo %s | mecab " %str(cjk), shell=True)
        for o in output.splitlines():
            try:
                word, other = o.split()
            except:
                continue
            s = other.split(',')
            pos = unicode(s[0])
            #if not pos in usable_pos: # get rid of particles etc                                         
            #    continue
            lemma = unicode(s[6].strip())
            if u'*' in lemma: continue
            if no_kana and all(ord(u"\u30a0") <= ord(ch) <= ord(u"\u30ff") for ch in lemma): 
                continue
            if no_gana and all(ord(u"\u3041") <= ord(ch) <= ord(u"\u309c") for ch in lemma):
                continue
            if lemma not in freq:
                counts[lemma] += 1

    flashcards = ''
    for i in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        word, count = i
        if count < min_count: continue # skip infrequent
        tango = Tango.query.get(word)
        if not tango: continue

        defs = {}
        nopron = False
        for entry in tango.entry.strip().splitlines():
            s = entry.split('\t')
            word = s[0] 
            pron = s[1]
            
            if pron.strip() == '':
                nopron = True
            
            definition = ' '.join(s[2:]).strip(',/ ')
            if '(ok)' in definition or '(oK)' in definition: continue # remove obsolete
                
            priority = False
            if '(P)' in definition:
                definition = definition.replace('(P)','').strip(',/ ')
                priority = True

            if not definition in defs:
                defs[definition] = {'prons':[], 'priority':[]}            

            if priority:
                defs[definition]['priority'].append(pron)
            else:
                defs[definition]['prons'].append(pron)
                
        for definition in defs:

            if nopron:
                pron = ''
            else:
                pron = '('
                if len(defs[definition]['priority']) > 0:
                    for i, p in enumerate(defs[definition]['priority']):
                        pron += p
                        if not i == len(defs[definition]['priority']) - 1:
                            pron += ', '
                    if len(defs[definition]['prons']) > 0:
                        pron += ' ; also '

                for i, p in enumerate(defs[definition]['prons']):
                    pron += p
                    if not i == len(defs[definition]['prons']) - 1:
                        pron += ', '
                pron += ')'

            if jp_to_en:
                flashcards += '%s   %s \t %s\n' %(word, pron, definition)
            if en_to_jp:
                flashcards += '%s \t %s   %s\n' %(definition, word, pron)            
    return flashcards


def make_memories_json():
    import csv, json
    csv_in = os.path.join(app.static_folder, 'MemoriesofJoan.csv')
    json_out = os.path.join(app.static_folder, 'MemoriesofJoan.json')
    jdict = []
    with open(csv_in) as csvfile:
        reader = csv.DictReader(csv_in)
        for row in reader:
            try:
                ts = row['Timestamp'].split()[0].split('/')
            except:
                continue
            date = ts[1] + '/' + ts[0] + '/' + ts[2]
            name = row['Name']
            mems = row['Your Memories and Reflections']
            jdict.append({'name':name,
                          'date':date,
                          'mems':mems})
    json.dump(jdict, open(json_out,'w'))
    return json_out
    

        
