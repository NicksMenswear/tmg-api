FROM python:3.12-bullseye
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y libpq-dev postgresql postgresql-contrib python3-dev
RUN pip install --upgrade pip
RUN pip install wheel

RUN pip install psycopg2==2.9.9
# Replace symlinks with hardlinks so lambda can copy libraries
SHELL ["/bin/bash", "-c"]
RUN for l in /usr/lib/x86_64-linux-gnu/*.so*; do \
        if [ -L "$l" ]; then \
            target=$(readlink -f "$l"); \
            ln -f "$target" "$l"; \
        fi; \
    done
