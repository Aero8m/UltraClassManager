from app.extensions import db


class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('name_groups.id'), nullable=False)

    group = db.relationship(
        'NameGroup',
        backref=db.backref('subjects', lazy=True, cascade='all, delete-orphan')
    )
