from app.extensions import db


class NameEntry(db.Model):
    __tablename__ = 'name_entries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    group_id = db.Column(
        db.Integer, db.ForeignKey('name_groups.id'), nullable=False
    )
