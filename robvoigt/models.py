from robvoigt import app, db


class Tango(db.Model):
    word = db.Column(db.String(80), primary_key=True)
    entry = db.Column(db.Text())
    
    def __init__(self, word, entry):
        self.word = word
        self.entry = entry



class TangoES(db.Model):
    word = db.Column(db.String(80), primary_key=True)
    entry = db.Column(db.Text())
    
    def __init__(self, word, entry):
        self.word = word
        self.entry = entry


