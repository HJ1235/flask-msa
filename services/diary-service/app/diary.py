import calendar
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection

diary_bp = Blueprint('diary', __name__, url_prefix='/diary')


@diary_bp.route('/')
@diary_bp.route('/<int:year>/<int:month>')
def diary_calendar(year=None, month=None):
    """사용자별 월 달력을 표시하고 일기 기록 여부를 나타냅니다."""
    if 'loggedin' not in session:
        flash('일기장을 보려면 로그인해야 합니다.', 'error')
        return redirect(url_for('auth.index'))

    today = datetime.now()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    if not (1 <= month <= 12 and 1900 <= year <= 2100):
        flash('유효하지 않은 연도 또는 월입니다.', 'error')
        return redirect(url_for('diary.diary_calendar'))

    prev_month_date = (datetime(year, month, 1) - timedelta(days=1)).replace(day=1)
    next_month_date = (datetime(year, month, 1) + timedelta(days=31)).replace(day=1)
    prev_year, prev_month = prev_month_date.year, prev_month_date.month
    next_year, next_month = next_month_date.year, next_month_date.month

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    diary_dates = set()
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT DATE_FORMAT(entry_date, '%%Y-%%m-%%d') AS entry_date_str "
                "FROM diaries WHERE user_id = %s AND YEAR(entry_date) = %s AND MONTH(entry_date) = %s",
                (session['id'], year, month)
            )
            for row in cursor.fetchall():
                diary_dates.add(row['entry_date_str'])
    except Exception as e:
        print(f"일기 데이터 불러오기 오류: {e}")
        flash('일기 데이터를 불러오는 데 실패했습니다.', 'error')
    finally:
        if conn:
            conn.close()

    return render_template('diary_calendar.html',
                           year=year, month=month,
                           month_name=datetime(year, month, 1).strftime('%B'),
                           month_days=month_days, diary_dates=diary_dates,
                           prev_year=prev_year, prev_month=prev_month,
                           next_year=next_year, next_month=next_month,
                           current_day=today.day if today.year == year and today.month == month else None,
                           today=today, username=session['username'])


@diary_bp.route('/entry/<string:date_str>', methods=['GET', 'POST'])
def diary_entry(date_str):
    """특정 날짜의 일기를 작성/조회/수정합니다."""
    if 'loggedin' not in session:
        flash('일기를 작성/조회하려면 로그인해야 합니다.', 'error')
        return redirect(url_for('auth.index'))

    try:
        entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('유효하지 않은 날짜 형식입니다.', 'error')
        return redirect(url_for('diary.diary_calendar'))

    diary = None
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, content, DATE_FORMAT(entry_date, '%%Y-%%m-%%d') AS entry_date_str "
                "FROM diaries WHERE user_id = %s AND entry_date = %s",
                (session['id'], entry_date)
            )
            diary = cursor.fetchone()

        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            content = request.form['content'].strip()
            if not content:
                flash('일기 내용은 비워둘 수 없습니다.', 'error')
                return redirect(url_for('diary.diary_entry', date_str=date_str))

            with conn.cursor() as cursor:
                if diary:
                    cursor.execute(
                        "UPDATE diaries SET title = %s, content = %s WHERE id = %s AND user_id = %s",
                        (title, content, diary['id'], session['id'])
                    )
                    flash('일기가 성공적으로 수정되었습니다!', 'success')
                else:
                    cursor.execute(
                        "INSERT INTO diaries (user_id, entry_date, title, content) VALUES (%s, %s, %s, %s)",
                        (session['id'], entry_date, title, content)
                    )
                    flash('일기가 성공적으로 작성되었습니다!', 'success')
            conn.commit()
            return redirect(url_for('diary.diary_calendar', year=entry_date.year, month=entry_date.month))

    except Exception as e:
        print(f"diary_entry 데이터베이스 오류: {e}")
        flash('일기 처리 중 오류가 발생했습니다.', 'error')
    finally:
        if conn:
            conn.close()

    return render_template('diary_entry.html', diary=diary, date_str=date_str, username=session['username'])
