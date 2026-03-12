FROM python:3.11-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN mkdir -p /app/static/uploads /app/static/pdfs

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5005

CMD ["gunicorn", "--bind", "0.0.0.0:5005", "--workers", "2", "--timeout", "120", "app:app"]
