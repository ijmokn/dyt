FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 50500

CMD ["gunicorn", "-c", "gunicorn.conf.py", "api.main:app"]