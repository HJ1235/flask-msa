import calendar
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection

todos_bp = Blueprint('todos', __name__, url_prefix='/todos')

VALID_STATUSES = ['미완료', '진행중', '완료', '기간연장']


@todos_bp.route('/')
def todos_list():
    """To-Do 목록을 표시하고 필터링 옵션을 제공합니다."""
    if 'loggedin' not in session:
        flash('To-Do List를 보려면 로그인해야 합니다.', 'error')
        return redirect(url_for('auth.index'))

    status_filter = request.args.get('status', 'all').strip()
    search_query = request.args.get('query', '').strip()

    conn = None
    todos = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = ("SELECT id, task, DATE_FORMAT(due_date, '%%Y-%%m-%%d') AS due_date, "
                   "status, created_at FROM todos WHERE user_id = %s")
            params = [session['id']]
            if status_filter != 'all':
                sql += " AND status = %s"
                params.append(status_filter)
            if search_query:
                sql += " AND task LIKE %s"
                params.append(f"%{search_query}%")
            sql += " ORDER BY created_at DESC"
            cursor.execute(sql, params)
            todos = cursor.fetchall()
    except Exception as e:
        print(f"To-Do 목록 불러오기 오류: {e}")
        flash('To-Do 목록을 불러오는 데 실패했습니다.', 'error')
    finally:
        if conn:
            conn.close()

    return render_template('todos_list.html', todos=todos, username=session['username'],
                           status_filter=status_filter, search_query=search_query,
                           all_statuses=VALID_STATUSES)


@todos_bp.route('/add', methods=['POST'])
def add_todo():
    """새 To-Do 항목을 추가합니다."""
    if 'loggedin' not in session:
        flash('To-Do 항목을 추가하려면 로그인해야 합니다.', 'error')
        return redirect(url_for('auth.index'))

    task = request.form['task'].strip()
    due_date_str = request.form.get('due_date', '').strip()
    status = request.form.get('status', '미완료').strip()

    if not task:
        flash('할 일 내용을 비워둘 수 없습니다.', 'error')
        return redirect(url_for('todos.todos_list'))

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('유효하지 않은 마감일 형식입니다.', 'error')
            return redirect(url_for('todos.todos_list'))

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO todos (user_id, task, due_date, status) VALUES (%s, %s, %s, %s)",
                (session['id'], task, due_date, status)
            )
        conn.commit()
        flash('To-Do 항목이 성공적으로 추가되었습니다!', 'success')
    except Exception as e:
        print(f"To-Do 항목 추가 오류: {e}")
        flash('To-Do 항목 추가에 실패했습니다.', 'error')
    finally:
        if conn:
            conn.close()
    return redirect(url_for('todos.todos_list'))


@todos_bp.route('/update_status/<int:todo_id>/<string:new_status>', methods=['POST'])
def update_todo_status(todo_id, new_status):
    """To-Do 항목의 상태를 업데이트합니다."""
    if 'loggedin' not in session:
        flash('To-Do 항목 상태를 변경하려면 로그인해야 합니다.', 'error')
        return redirect(url_for('auth.index'))

    if new_status not in VALID_STATUSES:
        flash('유효하지 않은 To-Do 상태입니다.', 'error')
        return redirect(url_for('todos.todos_list'))

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM todos WHERE id = %s AND user_id = %s", (todo_id, session['id']))
            if not cursor.fetchone():
                flash('To-Do 항목을 찾을 수 없거나 권한이 없습니다.', 'error')
                return redirect(url_for('todos.todos_list'))
            cursor.execute(
                "UPDATE todos SET status = %s WHERE id = %s AND user_id = %s",
                (new_status, todo_id, session['id'])
            )
        conn.commit()
        flash('To-Do 항목 상태가 성공적으로 업데이트되었습니다!', 'success')
    except Exception as e:
        print(f"To-Do 상태 업데이트 오류: {e}")
        flash('To-Do 항목 상태 업데이트에 실패했습니다.', 'error')
    finally:
        if conn:
            conn.close()
    return redirect(url_for('todos.todos_list'))


@todos_bp.route('/delete/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    """To-Do 항목을 삭제합니다."""
    if 'loggedin' not in session:
        flash('To-Do 항목을 삭제하려면 로그인해야 합니다.', 'error')
        return redirect(url_for('auth.index'))

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM todos WHERE id = %s AND user_id = %s", (todo_id, session['id']))
            if not cursor.fetchone():
                flash('To-Do 항목을 찾을 수 없거나 권한이 없습니다.', 'error')
                return redirect(url_for('todos.todos_list'))
            cursor.execute("DELETE FROM todos WHERE id = %s AND user_id = %s", (todo_id, session['id']))
        conn.commit()
        flash('To-Do 항목이 성공적으로 삭제되었습니다!', 'success')
    except Exception as e:
        print(f"To-Do 항목 삭제 오류: {e}")
        flash('To-Do 항목 삭제에 실패했습니다.', 'error')
    finally:
        if conn:
            conn.close()
    return redirect(url_for('todos.todos_list'))


@todos_bp.route('/reschedule/<int:todo_id>')
@todos_bp.route('/reschedule/<int:todo_id>/<int:year>/<int:month>')
def reschedule_todo_calendar(todo_id, year=None, month=None):
    """특정 To-Do 항목의 마감일을 재조정하기 위한 달력을 표시합니다."""
    if 'loggedin' not in session:
        flash('To-Do 항목 마감일을 재조정하려면 로그인해야 합니다.', 'error')
        return redirect(url_for('auth.index'))

    conn = None
    todo_item = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, task, DATE_FORMAT(due_date, '%%Y-%%m-%%d') AS due_date, status "
                "FROM todos WHERE id = %s AND user_id = %s",
                (todo_id, session['id'])
            )
            todo_item = cursor.fetchone()
            if not todo_item:
                flash('To-Do 항목을 찾을 수 없거나 권한이 없습니다.', 'error')
                return redirect(url_for('todos.todos_list'))
    except Exception as e:
        print(f"reschedule 항목 불러오기 오류: {e}")
        flash('To-Do 항목 정보를 불러오는 데 실패했습니다.', 'error')
        return redirect(url_for('todos.todos_list'))
    finally:
        if conn:
            conn.close()

    today = datetime.now()
    if year is None:
        year = today.year
    if month is None:
        month = today.month

    if not (1 <= month <= 12 and 1900 <= year <= 2100):
        flash('유효하지 않은 연도 또는 월입니다.', 'error')
        return redirect(url_for('todos.reschedule_todo_calendar', todo_id=todo_id))

    prev_month_date = (datetime(year, month, 1) - timedelta(days=1)).replace(day=1)
    next_month_date = (datetime(year, month, 1) + timedelta(days=31)).replace(day=1)
    prev_year, prev_month = prev_month_date.year, prev_month_date.month
    next_year, next_month = next_month_date.year, next_month_date.month

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    return render_template('todos_reschedule.html',
                           todo_item=todo_item, year=year, month=month,
                           month_name=datetime(year, month, 1).strftime('%B'),
                           month_days=month_days,
                           prev_year=prev_year, prev_month=prev_month,
                           next_year=next_year, next_month=next_month,
                           current_day=today.day if today.year == year and today.month == month else None,
                           today=today, username=session['username'])


@todos_bp.route('/set_due_date/<int:todo_id>', methods=['POST'])
def set_new_due_date(todo_id):
    """선택된 날짜로 To-Do 항목의 마감일을 설정합니다."""
    if 'loggedin' not in session:
        flash('To-Do 항목 마감일을 설정하려면 로그인해야 합니다.', 'error')
        return redirect(url_for('auth.index'))

    new_due_date_str = request.form.get('new_due_date', '').strip()
    if not new_due_date_str:
        flash('새로운 마감일을 선택해야 합니다.', 'error')
        return redirect(url_for('todos.todos_list'))

    try:
        new_due_date = datetime.strptime(new_due_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('유효하지 않은 날짜 형식입니다.', 'error')
        return redirect(url_for('todos.todos_list'))

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, status FROM todos WHERE id = %s AND user_id = %s",
                (todo_id, session['id'])
            )
            item_data = cursor.fetchone()
            if not item_data:
                flash('To-Do 항목을 찾을 수 없거나 권한이 없습니다.', 'error')
                return redirect(url_for('todos.todos_list'))

            current_status = item_data['status']
            if current_status == '완료':
                new_status = '미완료'
            elif current_status == '기간연장':
                new_status = '기간연장'
            else:
                new_status = '진행중'

            cursor.execute(
                "UPDATE todos SET due_date = %s, status = %s WHERE id = %s AND user_id = %s",
                (new_due_date, new_status, todo_id, session['id'])
            )
        conn.commit()
        flash(f'할 일의 마감일이 {new_due_date_str}으로 성공적으로 재조정되었습니다!', 'success')
    except Exception as e:
        print(f"To-Do 마감일 설정 오류: {e}")
        flash('마감일 재조정에 실패했습니다.', 'error')
    finally:
        if conn:
            conn.close()
    return redirect(url_for('todos.todos_list'))
