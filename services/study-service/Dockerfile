FROM python:3.11-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5004

CMD ["gunicorn", "--bind", "0.0.0.0:5004", "--workers", "2", "--timeout", "120", "app:app"]
