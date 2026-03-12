import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from db import get_db_connection
from utils import is_admin, allowed_pdf_file

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
def admin_dashboard():
    """관리자 메인 대시보드 페이지"""
    if not is_admin():
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('auth.index'))
    return render_template('admin_dashboard.html', username=session['username'])


@admin_bp.route('/upload_image', methods=['POST'])
def upload_image():
    """Summernote 에디터에서 이미지 업로드를 처리합니다."""
    if not is_admin():
        return jsonify({'error': '권한이 없습니다.'}), 403

    if 'file' not in request.files:
        return jsonify({'error': '파일이 없습니다.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    filename = secure_filename(file.filename)
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    if extension not in allowed_extensions:
        return jsonify({'error': '허용되지 않는 파일 형식입니다.'}), 400

    unique_filename = f"{uuid.uuid4()}.{extension}"
    from flask import current_app
    save_path = os.path.join(current_app.root_path, 'static/uploads', unique_filename)

    try:
        file.save(save_path)
        url = url_for('static', filename=f'uploads/{unique_filename}')
        return jsonify({'url': url})
    except Exception as e:
        from flask import current_app as app
        app.logger.error(f"Image save failed: {e}", exc_info=True)
        return jsonify({'error': '파일 저장 중 서버 오류가 발생했습니다.'}), 500


@admin_bp.route('/content')
def manage_content():
    """전체 학습 콘텐츠 목록을 보여주는 관리 페이지"""
    if not is_admin():
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('auth.index'))

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT c.id, c.title, c.content_type, s.name as subject_name
                   FROM contents c JOIN subjects s ON c.subject_id = s.id
                   ORDER BY s.name, c.created_at DESC"""
            )
            contents = cursor.fetchall()
        return render_template('manage_content.html', contents=contents)
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"콘텐츠 목록 불러오기 오류: {e}", exc_info=True)
        flash('콘텐츠 목록을 불러오는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    finally:
        if conn:
            conn.close()


@admin_bp.route('/add_content', methods=['GET', 'POST'])
def add_content():
    """새로운 학습 콘텐츠를 등록하는 페이지"""
    if not is_admin():
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('auth.index'))

    from flask import current_app
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM subjects ORDER BY name ASC")
            subjects = cursor.fetchall()

            if request.method == 'POST':
                storage_type = request.form.get('storage_type')
                subject_id = request.form.get('subject_id')
                content_type = request.form.get('content_type')
                title = request.form.get('title', '').strip()

                if not all([storage_type, subject_id, content_type, title]):
                    flash('모든 필수 항목을 입력해주세요.', 'error')
                    return render_template('add_content.html', subjects=subjects)

                if storage_type == 'editor':
                    body = request.form.get('body', '').strip()
                    if not body:
                        flash('에디터 내용을 입력해주세요.', 'error')
                        return render_template('add_content.html', subjects=subjects)
                    cursor.execute(
                        "INSERT INTO contents (subject_id, content_type, storage_type, title, body, is_active) "
                        "VALUES (%s, %s, %s, %s, %s, 0)",
                        (subject_id, content_type, storage_type, title, body)
                    )

                elif storage_type == 'pdf':
                    if 'pdf_file' not in request.files or request.files['pdf_file'].filename == '':
                        flash('PDF 파일을 선택해주세요.', 'error')
                        return render_template('add_content.html', subjects=subjects)
                    file = request.files['pdf_file']
                    if not (file and allowed_pdf_file(file.filename)):
                        flash('PDF 파일만 업로드할 수 있습니다.', 'error')
                        return render_template('add_content.html', subjects=subjects)

                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    save_path = os.path.join(current_app.root_path, 'static/pdfs', unique_filename)
                    file.save(save_path)
                    pdf_path = f"pdfs/{unique_filename}"
                    cursor.execute(
                        "INSERT INTO contents (subject_id, content_type, storage_type, title, pdf_path, is_active) "
                        "VALUES (%s, %s, %s, %s, %s, 0)",
                        (subject_id, content_type, storage_type, title, pdf_path)
                    )

                conn.commit()
                flash('새로운 콘텐츠가 성공적으로 등록되었습니다.', 'success')
                return redirect(url_for('admin.manage_content'))

            return render_template('add_content.html', subjects=subjects)
    except Exception as e:
        from flask import current_app as app
        app.logger.error(f"콘텐츠 추가 오류: {e}", exc_info=True)
        flash('콘텐츠 추가 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    finally:
        if conn:
            conn.close()


@admin_bp.route('/edit_content/<int:content_id>', methods=['GET', 'POST'])
def edit_content(content_id):
    """기존 학습 콘텐츠를 수정하는 페이지"""
    if not is_admin():
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('auth.index'))

    from flask import current_app
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if request.method == 'POST':
                storage_type = request.form.get('storage_type')
                subject_id = request.form.get('subject_id')
                content_type = request.form.get('content_type')
                title = request.form.get('title', '').strip()

                if storage_type == 'editor':
                    body = request.form.get('body', '').strip()
                    cursor.execute(
                        "UPDATE contents SET subject_id=%s, content_type=%s, storage_type='editor', "
                        "title=%s, body=%s, pdf_path=NULL WHERE id=%s",
                        (subject_id, content_type, title, body, content_id)
                    )

                elif storage_type == 'pdf':
                    pdf_path_updated = False
                    if 'pdf_file' in request.files and request.files['pdf_file'].filename != '':
                        file = request.files['pdf_file']
                        if file and allowed_pdf_file(file.filename):
                            filename = secure_filename(file.filename)
                            unique_filename = f"{uuid.uuid4()}_{filename}"
                            save_path = os.path.join(current_app.root_path, 'static/pdfs', unique_filename)
                            file.save(save_path)
                            pdf_path = f"pdfs/{unique_filename}"
                            cursor.execute(
                                "UPDATE contents SET subject_id=%s, content_type=%s, storage_type='pdf', "
                                "title=%s, body=NULL, pdf_path=%s WHERE id=%s",
                                (subject_id, content_type, title, pdf_path, content_id)
                            )
                            pdf_path_updated = True

                    if not pdf_path_updated:
                        cursor.execute(
                            "UPDATE contents SET subject_id=%s, content_type=%s, "
                            "storage_type='pdf', title=%s WHERE id=%s",
                            (subject_id, content_type, title, content_id)
                        )

                conn.commit()
                flash('콘텐츠가 성공적으로 수정되었습니다.', 'success')
                return redirect(url_for('admin.manage_content'))

            # GET 요청
            cursor.execute("SELECT * FROM contents WHERE id = %s", (content_id,))
            content = cursor.fetchone()
            cursor.execute("SELECT id, name FROM subjects ORDER BY name ASC")
            subjects = cursor.fetchall()
            return render_template('edit_content.html', content=content, subjects=subjects)

    except Exception as e:
        from flask import current_app as app
        app.logger.error(f"콘텐츠 수정 오류: {e}", exc_info=True)
        flash('콘텐츠 처리 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin.manage_content'))
    finally:
        if conn:
            conn.close()


@admin_bp.route('/delete_content/<int:content_id>', methods=['POST'])
def delete_content(content_id):
    """특정 학습 콘텐츠를 삭제합니다."""
    if not is_admin():
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('auth.index'))

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM contents WHERE id = %s", (content_id,))
        conn.commit()
        flash('콘텐츠가 삭제되었습니다.', 'success')
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"콘텐츠 삭제 오류: {e}", exc_info=True)
        flash('콘텐츠 삭제 중 오류가 발생했습니다.', 'error')
    finally:
        if conn:
            conn.close()
    return redirect(url_for('admin.manage_content'))


@admin_bp.route('/subjects', methods=['GET', 'POST'])
def manage_subjects():
    """과목 목록을 보고, 새 과목을 등록하는 페이지"""
    if not is_admin():
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('auth.index'))

    conn = None
    try:
        conn = get_db_connection()
        if request.method == 'POST':
            name = request.form['name'].strip()
            if name:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM subjects WHERE name = %s", (name,))
                    if cursor.fetchone():
                        flash('이미 존재하는 과목 이름입니다.', 'error')
                    else:
                        cursor.execute("INSERT INTO subjects (name) VALUES (%s)", (name,))
                        conn.commit()
                        flash('새로운 과목이 성공적으로 등록되었습니다.', 'success')
            else:
                flash('과목 이름을 입력해주세요.', 'error')
            return redirect(url_for('admin.manage_subjects'))

        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM subjects ORDER BY name ASC")
            subjects = cursor.fetchall()
        return render_template('manage_subjects.html', subjects=subjects, username=session['username'])
    except Exception as e:
        print(f"과목 관리 페이지 오류: {e}")
        flash('과목 관리 페이지를 로드하는 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    finally:
        if conn:
            conn.close()


@admin_bp.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    """기존 과목의 이름을 수정하는 페이지"""
    if not is_admin():
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('auth.index'))

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if request.method == 'POST':
                new_name = request.form['name'].strip()
                if not new_name:
                    flash('과목 이름은 비워둘 수 없습니다.', 'error')
                else:
                    cursor.execute(
                        "SELECT id FROM subjects WHERE name = %s AND id != %s",
                        (new_name, subject_id)
                    )
                    if cursor.fetchone():
                        flash('이미 존재하는 과목 이름입니다.', 'error')
                    else:
                        cursor.execute("UPDATE subjects SET name = %s WHERE id = %s", (new_name, subject_id))
                        conn.commit()
                        flash('과목 이름이 성공적으로 수정되었습니다.', 'success')
                        return redirect(url_for('admin.manage_subjects'))

            cursor.execute("SELECT id, name FROM subjects WHERE id = %s", (subject_id,))
            subject = cursor.fetchone()
            if not subject:
                flash('존재하지 않는 과목입니다.', 'error')
                return redirect(url_for('admin.manage_subjects'))

            return render_template('edit_subject.html', subject=subject, username=session['username'])
    except Exception as e:
        print(f"과목 수정 오류: {e}")
        flash('과목 수정 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('admin.manage_subjects'))
    finally:
        if conn:
            conn.close()


@admin_bp.route('/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    """특정 과목을 삭제하는 기능"""
    if not is_admin():
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('auth.index'))

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM subjects WHERE id = %s", (subject_id,))
        conn.commit()
        flash('과목 및 관련 콘텐츠가 모두 삭제되었습니다.', 'success')
    except Exception as e:
        print(f"과목 삭제 오류: {e}")
        flash('과목 삭제 중 오류가 발생했습니다.', 'error')
    finally:
        if conn:
            conn.close()
    return redirect(url_for('admin.manage_subjects'))
