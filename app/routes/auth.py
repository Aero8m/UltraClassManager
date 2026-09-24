from urllib.parse import urlparse

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User

auth_bp = Blueprint('auth', __name__)


def _safe_redirect(target):
    """Only redirect to relative paths — prevent open-redirect attacks."""
    if target and not urlparse(target).netloc:
        return redirect(target)
    return redirect(url_for('group.dashboard'))


@auth_bp.route('/')
def index():
    return render_template('index.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash('用户名和密码不能为空~')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(username=username).first():
            flash('用户名已经被占用啦~')
            return redirect(url_for('auth.register'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('注册成功~ 快登录吧')
        return redirect(url_for('auth.login'))
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'欢迎回来 {username}~')
            next_page = request.args.get('next')
            return _safe_redirect(next_page) if next_page else redirect(url_for('group.dashboard'))
        flash('用户名或密码不对~')
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已登出~ 下次再来玩呀')
    return redirect(url_for('auth.index'))


@auth_bp.route('/reauth', methods=['GET'])
@login_required
def reauth_page():
    """Render the full-page reauth form (server-side fallback)."""
    next_url = request.args.get('next', url_for('group.dashboard'))
    return render_template('reauth.html', next=next_url)


@auth_bp.route('/reauth', methods=['POST'])
@login_required
def reauth_verify():
    password = request.form.get('password', '').strip()
    user = User.query.get(current_user.id)
    next_url = request.form.get('next', '') or request.args.get('next', '')

    if user and user.check_password(password):
        session['reauth_verified'] = True

        # AJAX request (JS modal) — return JSON
        wants_json = (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or 'application/json' in (request.headers.get('Accept') or '')
        )
        if wants_json:
            return {'success': True}

        # Regular form POST — redirect
        if next_url:
            return _safe_redirect(next_url)
        return redirect(url_for('group.dashboard'))

    # Password incorrect
    wants_json = (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in (request.headers.get('Accept') or '')
    )
    if wants_json:
        return {'success': False, 'message': '密码不正确~'}

    flash('密码不正确~')
    if next_url:
        return redirect(url_for('auth.reauth_page', next=next_url))
    return redirect(url_for('auth.reauth_page'))
