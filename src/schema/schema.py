from extensions import db

class Chapter(db.Model):
    __tablename__ = 'Chapter'
    id = db.Column(db.Integer, primary_key=True)
    ChapterName = db.Column(db.Text)
    Description = db.Column(db.Text)

class Section(db.Model):
    __tablename__ = 'Section'
    id = db.Column(db.Integer, primary_key=True)
    ChapterId = db.Column(db.Integer, db.ForeignKey('Chapter.id'))
    SectionName = db.Column(db.Text)
    Description = db.Column(db.Text)

    chapter = db.relationship('Chapter', backref='sections')
