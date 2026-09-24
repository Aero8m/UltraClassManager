from app.extensions import db


class NameGroup(db.Model):
    __tablename__ = 'name_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    names = db.relationship(
        'NameEntry', backref='group', lazy=True,
        cascade='all, delete-orphan'
    )
