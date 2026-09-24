import random
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash
)
from flask_login import login_required, current_user
from app.extensions import db
from app.models import NameGroup, NameEntry
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
