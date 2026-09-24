import random
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session
)
from flask_login import login_required, current_user
from app.extensions import db
from app.models import NameGroup, NameEntry, Score, Subject
from app.decorators import require_reauth

group_bp = Blueprint('group', __name__)


@group_bp.route('/dashboard')
@login_required
def dashboard():
    groups = NameGroup.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', groups=groups)


@group_bp.route('/group/create', methods=['POST'])
@login_required
@require_reauth
def create_group():
    name = request.form.get('name', '').strip()
    if not name:
        flash('组名不能为空~')
        return redirect(url_for('group.dashboard'))
    group = NameGroup(name=name, user_id=current_user.id)
    db.session.add(group)
    db.session.commit()
    flash(f'班级 "{name}" 创建成功~')
    return redirect(url_for('group.dashboard'))


@group_bp.route('/group/<int:group_id>/delete', methods=['POST'])
@login_required
@require_reauth
def delete_group(group_id):
    group = NameGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('这不是你的组~')
        return redirect(url_for('group.dashboard'))
    db.session.delete(group)
    db.session.commit()
    flash('班级已删除~')
    return redirect(url_for('group.dashboard'))


@group_bp.route('/group/<int:group_id>')
@login_required
def view_group(group_id):
    group = NameGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('这不是你的组~')
        return redirect(url_for('group.dashboard'))
    names = NameEntry.query.filter_by(group_id=group_id).all()
    name_list = [n.name for n in names]
    return render_template('group.html', group=group, names=name_list)


@group_bp.route('/group/<int:group_id>/add', methods=['POST'])
@login_required
@require_reauth
def add_name(group_id):
    group = NameGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('这不是你的组~')
        return redirect(url_for('group.dashboard'))
    name = request.form.get('name', '').strip()
    if not name:
        flash('学生名不能为空~')
        return redirect(url_for('group.view_group', group_id=group_id))
    existing = NameEntry.query.filter_by(
        group_id=group_id, name=name
    ).first()
    if existing:
        flash(f'"{name}" 已经存在了，不能重复添加~')
        return redirect(url_for('group.view_group', group_id=group_id))
    entry = NameEntry(name=name, group_id=group_id)
    db.session.add(entry)
    db.session.commit()
    flash(f'"{name}" 已添加到班级里~')
    return redirect(url_for('group.view_group', group_id=group_id))


@group_bp.route('/group/<int:group_id>/import', methods=['POST'])
@login_required
@require_reauth
def import_names(group_id):
    group = NameGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('这不是你的组~')
        return redirect(url_for('group.dashboard'))
    text = request.form.get('text', '').strip()
    if not text:
        flash('请输入学生名~')
        return redirect(url_for('group.view_group', group_id=group_id))
    names = [
        n.strip() for n in text.replace('\n', ',').split(',') if n.strip()
    ]
    # 去重：先查已有名单
    existing_names = {
        e.name for e in
        NameEntry.query.filter_by(group_id=group_id).all()
    }
    added = 0
    skipped = 0
    for n in names:
        if n in existing_names:
            skipped += 1
            continue
        entry = NameEntry(name=n, group_id=group_id)
        db.session.add(entry)
        existing_names.add(n)
        added += 1
    db.session.commit()
    msg = f'成功导入 {added} 个学生~'
    if skipped > 0:
        msg += f'（{skipped} 个已存在，已跳过）'
    flash(msg)
    return redirect(url_for('group.view_group', group_id=group_id))


@group_bp.route('/group/<int:group_id>/delete_name', methods=['POST'])
@login_required
@require_reauth
def delete_name(group_id):
    group = NameGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('这不是你的组~')
        return redirect(url_for('group.dashboard'))
    target_name = request.form.get('name', '').strip()
    if target_name:
        entry = NameEntry.query.filter_by(
            group_id=group_id, name=target_name
        ).first()
        if entry:
            db.session.delete(entry)
            db.session.commit()
    flash('学生已删除~')
    return redirect(url_for('group.view_group', group_id=group_id))


@group_bp.route('/group/<int:group_id>/pick', methods=['POST'])
@login_required
def pick_name(group_id):
    group = NameGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('这不是你的组~')
        return redirect(url_for('group.dashboard'))
    entries = NameEntry.query.filter_by(group_id=group_id).all()
    if not entries:
        flash('组里没有学生可以抽~')
        return redirect(url_for('group.view_group', group_id=group_id))
    count = int(request.form.get('count', 1))
    count = max(1, min(count, len(entries)))
    picked = random.sample(entries, count)
    result = [p.name for p in picked]
    name_list = [e.name for e in entries]
    return render_template(
        'group.html', group=group, names=name_list, result=result
    )


@group_bp.route('/group/<int:group_id>/scores')
@login_required
def view_subjects(group_id):
    """Subject list — first level of score management."""
    group = NameGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('这不是你的组~')
        return redirect(url_for('group.dashboard'))

    # ── Build subject list ──────────────────────────────────────
    from collections import defaultdict

    scores = Score.query.filter_by(group_id=group_id).all()
    subj_data = defaultdict(list)
    for s in scores:
        subj_data[s.subject].append(s.score)

    # Merge: registered subjects + subjects with scores
    registered = {s.name for s in Subject.query.filter_by(group_id=group_id).all()}
    all_subj_names = set(subj_data.keys()) | registered

    subjects = []
    for subj in sorted(all_subj_names):
        vals = subj_data.get(subj, [])
        subjects.append({
            'name': subj,
            'count': len(vals),
            'avg': round(sum(vals) / len(vals), 1) if vals else 0,
            'max': max(vals) if vals else 0,
            'min': min(vals) if vals else 0,
            'is_registered': subj in registered,
        })

    # Per-student averages for chart (all subjects combined)
    stu_data = defaultdict(list)
    for s in scores:
        stu_data[s.student_name].append(s.score)
    chart_labels = []
    chart_values = []
    for stu, vals in sorted(stu_data.items()):
        chart_labels.append(stu)
        chart_values.append(round(sum(vals) / len(vals), 1))

    return render_template(
        'scores_subjects.html', group=group, subjects=subjects,
        chart_labels=chart_labels, chart_values=chart_values,
    )


@group_bp.route('/group/<int:group_id>/scores/subject/add', methods=['POST'])
@login_required
@require_reauth
def add_subject(group_id):
    group = NameGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('这不是你的组~')
        return redirect(url_for('group.dashboard'))
    subj_name = request.form.get('subject_name', '').strip()
    if subj_name:
        existing = Subject.query.filter_by(group_id=group_id, name=subj_name).first()
        if existing:
            flash(f'考试 "{subj_name}" 已存在~')
        else:
            db.session.add(Subject(name=subj_name, group_id=group_id))
            db.session.commit()
            flash(f'考试 "{subj_name}" 已添加~')
    else:
        flash('考试名不能为空~')
    return redirect(url_for('group.view_subjects', group_id=group_id))


@group_bp.route('/group/<int:group_id>/scores/subject/delete', methods=['POST'])
@login_required
@require_reauth
def delete_subject(group_id):
    group = NameGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('这不是你的组~')
        return redirect(url_for('group.dashboard'))
    subj_name = request.form.get('subject_name', '').strip()
    if subj_name:
        subj = Subject.query.filter_by(group_id=group_id, name=subj_name).first()
        score_count = 0
        for s in Score.query.filter_by(group_id=group_id, subject=subj_name).all():
            db.session.delete(s)
            score_count += 1
        if subj:
            db.session.delete(subj)
        db.session.commit()
        if subj or score_count > 0:
            flash(f'考试 "{subj_name}" 及相关成绩已删除~')
        else:
            flash('考试不存在~')
    return redirect(url_for('group.view_subjects', group_id=group_id))


@group_bp.route('/group/<int:group_id>/scores/<path:subject>')
@login_required
def view_subject_scores(group_id, subject):
    """Scores for a single subject — second level."""
    group = NameGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('这不是你的组~')
        return redirect(url_for('group.dashboard'))

    scores = Score.query.filter_by(group_id=group_id, subject=subject).order_by(
        Score.student_name
    ).all()
    names = NameEntry.query.filter_by(group_id=group_id).all()
    name_list = [n.name for n in names]
    subjects_list = [s.name for s in Subject.query.filter_by(group_id=group_id).order_by(Subject.name).all()]
    # Also include subjects that have scores but aren't registered
    from collections import defaultdict
    for s in Score.query.filter_by(group_id=group_id).all():
        if s.subject not in subjects_list:
            subjects_list.append(s.subject)

    scores_json = [
        {
            'id': s.id,
            'student_name': s.student_name,
            'subject': s.subject,
            'score': s.score,
            'exam_note': s.exam_note or '',
        }
        for s in scores
    ]

    edit_id = request.args.get('edit', type=int)
    edit_score = Score.query.get(edit_id) if edit_id else None
    if edit_score and edit_score.group_id != group_id:
        edit_score = None

    total_count = len(scores)
    if total_count > 0:
        all_vals = [s.score for s in scores]
        avg_score = round(sum(all_vals) / total_count, 1)
        max_score = max(all_vals)
        min_score = min(all_vals)
    else:
        avg_score = max_score = min_score = 0

    return render_template(
        'scores.html',
        group=group, subject=subject, names=name_list,
        subjects_list=subjects_list,
        edit_score=edit_score, scores_json=scores_json,
        total_count=total_count, avg_score=avg_score,
        max_score=max_score, min_score=min_score,
    )


@group_bp.route('/group/<int:group_id>/scores/add', methods=['POST'])
@login_required
def add_score(group_id):
    group = NameGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('这不是你的组~')
        return redirect(url_for('group.dashboard'))

    student_name = request.form.get('student_name', '').strip()
    subject = request.form.get('subject', '').strip()
    raw_score = request.form.get('score', '').strip()
    exam_note = request.form.get('exam_note', '').strip()
    redirect_subject = request.form.get('redirect_subject', subject).strip()

    if not student_name or not subject or not raw_score:
        flash('学生、考试和分数都不能为空~')
        return redirect(url_for('group.view_subjects', group_id=group_id))

    try:
        score_val = float(raw_score)
    except ValueError:
        flash('分数必须是数字~')
        return redirect(url_for('group.view_subjects', group_id=group_id))

    if score_val < 0 or score_val > 100:
        flash('分数必须在 0~100 之间~')
        return redirect(url_for('group.view_subjects', group_id=group_id))

    # Check for duplicates
    existing = Score.query.filter_by(
        group_id=group_id, student_name=student_name, subject=subject
    ).first()
    if existing:
        flash(f'{student_name} 的 {subject} 成绩已存在，请使用编辑功能修改~')
        return redirect(url_for('group.view_subject_scores',
                                group_id=group_id, subject=redirect_subject))

    db.session.add(Score(
        group_id=group_id,
        student_name=student_name,
        subject=subject,
        score=score_val,
        exam_note=exam_note or None,
    ))
    db.session.commit()
    flash('成绩已添加~')
    return redirect(url_for('group.view_subject_scores',
                            group_id=group_id, subject=redirect_subject))


@group_bp.route('/group/<int:group_id>/scores/<int:score_id>/edit', methods=['POST'])
@login_required
@require_reauth
def edit_score(group_id, score_id):
    group = NameGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('这不是你的组~')
        return redirect(url_for('group.dashboard'))

    score = Score.query.get_or_404(score_id)
    if score.group_id != group_id:
        flash('成绩不属于这个组~')
        return redirect(url_for('group.view_subjects', group_id=group_id))

    student_name = request.form.get('student_name', '').strip()
    subject = request.form.get('subject', '').strip()
    raw_score = request.form.get('score', '').strip()
    exam_note = request.form.get('exam_note', '').strip()
    redirect_subject = request.form.get('redirect_subject', subject).strip()

    if not student_name or not subject or not raw_score:
        flash('学生、考试和分数都不能为空~')
        return redirect(url_for('group.view_subjects', group_id=group_id))

    try:
        score_val = float(raw_score)
    except ValueError:
        flash('分数必须是数字~')
        return redirect(url_for('group.view_subjects', group_id=group_id))

    if score_val < 0 or score_val > 100:
        flash('分数必须在 0~100 之间~')
        return redirect(url_for('group.view_subjects', group_id=group_id))

    score.student_name = student_name
    score.subject = subject
    score.score = score_val
    score.exam_note = exam_note or None
    db.session.commit()
    flash('成绩已更新~')
    return redirect(url_for('group.view_subject_scores',
                            group_id=group_id, subject=redirect_subject))


@group_bp.route('/group/<int:group_id>/scores/<int:score_id>/delete', methods=['POST'])
@login_required
@require_reauth
def delete_score(group_id, score_id):
    group = NameGroup.query.get_or_404(group_id)
    if group.user_id != current_user.id:
        flash('这不是你的组~')
        return redirect(url_for('group.dashboard'))

    score = Score.query.get_or_404(score_id)
    if score.group_id != group_id:
        flash('成绩不属于这个组~')
        return redirect(url_for('group.view_subjects', group_id=group_id))

    old_subject = score.subject
    db.session.delete(score)
    db.session.commit()
    flash('成绩已删除~')
    return redirect(url_for('group.view_subject_scores',
                            group_id=group_id, subject=old_subject))
