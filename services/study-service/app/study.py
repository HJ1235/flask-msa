from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection
from utils import is_admin

study_bp = Blueprint('study', __name__, url_prefix='/study')


@study_bp.route('/')
def study_list():
    """전체 학습 과목 목록을 표시합니다."""
    if 'loggedin' not in session:
        flash('학습 콘텐츠를 보려면 로그인해야 합니다.', 'error')
        return redirect("http://auth-service:5000/")

    conn = None
    subjects = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM subjects ORDER BY name ASC")
            subjects = cursor.fetchall()
    except Exception as e:
        print(f"과목 목록 불러오기 오류: {e}")
        flash('과목 목록을 불러오는 데 실패했습니다.', 'error')
    finally:
        if conn:
            conn.close()

    return render_template('study_list.html', subjects=subjects, username=session['username'])


@study_bp.route('/<int:subject_id>')
def subject_detail(subject_id):
    """특정 과목의 이론/실습 콘텐츠 목록을 표시합니다."""
    if 'loggedin' not in session:
        flash('학습 콘텐츠를 보려면 로그인해야 합니다.', 'error')
        return redirect("http://auth-service:5000/")

    conn = None
    subject = None
    theory_contents = []
    lab_contents = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM subjects WHERE id = %s", (subject_id,))
            subject = cursor.fetchone()
            if not subject:
                flash('존재하지 않는 과목입니다.', 'error')
                return redirect(url_for('study.study_list'))

            cursor.execute(
                "SELECT id, title, created_at, is_active FROM contents "
                "WHERE subject_id = %s AND content_type = '이론' ORDER BY created_at ASC",
                (subject_id,)
            )
            theory_contents = cursor.fetchall()

            cursor.execute(
                "SELECT id, title, created_at, is_active FROM contents "
                "WHERE subject_id = %s AND content_type = '실습' ORDER BY created_at ASC",
                (subject_id,)
            )
            lab_contents = cursor.fetchall()
    except Exception as e:
        print(f"콘텐츠 목록 불러오기 오류: {e}")
        flash('콘텐츠 목록을 불러오는 데 실패했습니다.', 'error')
    finally:
        if conn:
            conn.close()

    return render_template('subject_detail.html', subject=subject,
                           theory_contents=theory_contents, lab_contents=lab_contents,
                           username=session['username'])


@study_bp.route('/content/<int:content_id>')
def view_content(content_id):
    """개별 콘텐츠(이론 또는 실습)의 상세 내용을 표시합니다."""
    if 'loggedin' not in session:
        flash('콘텐츠를 보려면 로그인해야 합니다.', 'error')
        return redirect("http://auth-service:5000/")

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT c.id, c.title, c.body, c.content_type, c.storage_type,
                          c.pdf_path, c.created_at, c.is_active, s.name as subject_name, c.subject_id
                   FROM contents c JOIN subjects s ON c.subject_id = s.id
                   WHERE c.id = %s""",
                (content_id,)
            )
            content = cursor.fetchone()
            if not content:
                flash('존재하지 않는 콘텐츠입니다.', 'error')
                return redirect(url_for('study.study_list'))

            if not is_admin() and not content['is_active']:
                flash('아직 활성화되지 않은 콘텐츠입니다.', 'error')
                return redirect(url_for('study.subject_detail', subject_id=content['subject_id']))

            return render_template('view_content.html', content=content)
    except Exception as e:
        print(f"콘텐츠 불러오기 오류: {e}")
        flash('콘텐츠를 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('study.study_list'))
    finally:
        if conn:
            conn.close()


@study_bp.route('/content/toggle_status/<int:content_id>', methods=['POST'])
def toggle_content_status(content_id):
    """학습 콘텐츠의 활성화 상태를 변경(토글)합니다."""
    if not is_admin():
        flash('이 작업을 수행할 권한이 없습니다.', 'error')
        return redirect(request.referrer or url_for('study.study_list'))

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT subject_id FROM contents WHERE id = %s", (content_id,))
            content = cursor.fetchone()
            if not content:
                flash('존재하지 않는 콘텐츠입니다.', 'error')
                return redirect(url_for('study.study_list'))

            cursor.execute("UPDATE contents SET is_active = NOT is_active WHERE id = %s", (content_id,))
        conn.commit()
        flash('콘텐츠 상태가 성공적으로 변경되었습니다.', 'success')
        return redirect(url_for('study.subject_detail', subject_id=content['subject_id']))
    except Exception as e:
        print(f"콘텐츠 상태 변경 오류: {e}")
        flash('콘텐츠 상태 변경에 실패했습니다.', 'error')
        return redirect(request.referrer or url_for('study.study_list'))
    finally:
        if conn:
            conn.close()
