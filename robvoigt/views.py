import os, sys, json, codecs, urllib2
from bs4 import BeautifulSoup
from robvoigt import app, db
from models import Tango, TangoES
from flask import redirect, render_template, make_response, request, flash
from werkzeug import secure_filename
from utils import do_tango

@app.route('/')
def home():
    return render_template('index.html')
    #return redirect('http://nlp.stanford.edu/robvoigt')

@app.route('/tango_db_es')
def tango_db_es():
    d = {x.split('\t')[0] : x.split('\t')[1] for x in codecs.open(os.path.join(app.static_folder, 'fixed-freedict-spa-eng.dic'), encoding='utf-8')}
    for w in d:
        tango = TangoES.query.get(w)
        if tango: continue

        entry = d[w]
        new_entry = TangoES(w, entry)
        db.session.add(new_entry)
        db.session.commit()


#############
#
# music pages
#
############
@app.route('/facsimiles')
def facsimiles():
    return render_template('facsimiles.html')

@app.route('/radioandfilm')
def radiofilm():
    return render_template('radiofilm.html')



        

#############
#
# games pages
#
#############
@app.route('/whogotit')
def whogotit():
    return render_template('whogotit.html')



#############
#
# tangorisuto
#
#############

@app.route('/tango_db')
def tango_db():
    # initializes tango db - takes a dang while
    d = json.load(codecs.open(os.path.join(app.static_folder, 'edict.json'),encoding='utf-8'))

    for w in d:

        # only do new words or entries we don't already have
        tango = Tango.query.get(w)
        if tango: continue

        entry = ''
        for e in d[w]:
            entry += w + '\t' + e[0] + '\t' + e[1] + '\n' # word, pronunciation, entry
        new_entry = Tango(w, entry)
        

        db.session.add(new_entry)
        db.session.commit()
    return 'ok'

@app.route('/tangorisuto', methods=['GET','POST'])
def tango():
    if request.method == 'POST':
        #return str(request.form) + str(request.files)
        
        text = ''
        fname = 'flashcards'

        if request.form.get('optionsRadios') == "file":

            f = request.files['inputFile']
            if f:
                text = f.read()
                fname = os.path.splitext(secure_filename(f.filename))[0]
        elif request.form.get('optionsRadios') == "web":
            response = urllib2.urlopen(request.form['inputWebsite'])
            text = response.read()
            soup = BeautifulSoup(text)
            text = soup.prettify()
        elif request.form.get('optionsRadios') == "text":
            text = request.form['inputText']
    
        max_freq = int(request.form.get('max_freq',1000))
        min_count = int(request.form.get('min_count',2))
        no_kana = request.form.get('no_kana',False)
        no_gana = request.form.get('no_gana',False)
        jp_to_en = request.form.get('jp_to_en',False)
        en_to_jp = request.form.get('en_to_jp',False)
        if no_kana: no_kana = True
        if no_gana: no_gana = True
        if jp_to_en: jp_to_en = True
        if en_to_jp: en_to_jp = True
        flashcards = do_tango(text, min_count=min_count, max_freq=max_freq, no_kana=no_kana, no_gana=no_gana, jp_to_en=jp_to_en, en_to_jp=en_to_jp)
        if flashcards.strip() == '':
            flash(u'Your requested input generated no flash cards! Check the settings in "Show Advanced Settings" - by default, the 1000 most common words in Japanese are removed, as are words that don\'t appear at least twice in the input.')
            return render_template('tangorisuto.html')
        output = make_response(flashcards)
        output.headers["Content-Disposition"] = "attachment; filename=%s.tsv" %fname
        output.headers["Content-type"] = "text/tsv"
        return output
    return render_template('tangorisuto.html')


################
#
# personal pages
#
################
@app.route('/memoriesofjoan')
def memoriesofjoan():
    mems_json = os.path.join(app.static_folder, 'MemoriesofJoan.json')
    return render_template('memoriesofjoan.html', mems_json=mems_json)
