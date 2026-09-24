from app.extensions import db


class Score(db.Model):
    __tablename__ = 'scores'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('name_groups.id'), nullable=False)
    student_name = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Float, nullable=False)
    exam_note = db.Column(db.String(255), nullable=True)

    group = db.relationship(
        'NameGroup',
        backref=db.backref('scores', lazy=True, cascade='all, delete-orphan')
    )
