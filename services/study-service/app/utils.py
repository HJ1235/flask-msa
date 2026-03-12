import re
from flask import session


def is_password_strong(password):
    """암호 복잡도 규칙(8자 이상, 대/소문자, 숫자, 특수문자 조합)을 검증합니다."""
    if len(password) < 8:
        return False
    rules = [
        any(c.isupper() for c in password),
        any(c.islower() for c in password),
        any(c.isdigit() for c in password),
        any(c in "!@#$%^&*()_+=:;\"'><.,?/[]}{" for c in password)
    ]
    return sum(rules) == 4


def is_valid_phone_number(phone_number):
    """대한민국 핸드폰 번호 형식인지 정규표현식으로 검증합니다."""
    pattern = re.compile(r'^(010\d{8}|01[1,6-9]\d{7,8})$')
    return pattern.match(phone_number)


def is_admin():
    """세션에 로그인된 사용자가 관리자인지 확인하는 헬퍼 함수"""
    return 'username' in session and session['username'] in ['kevin', 'kwangjin']


def allowed_pdf_file(filename):
    """PDF 파일 확장자만 허용하는지 확인하는 헬퍼 함수"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}
