
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt


FROM python:3.12-slim
RUN useradd -m -u 1000 student
WORKDIR /app

COPY --from=builder /install /usr/local
COPY --chown=student:student . .
USER student

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
