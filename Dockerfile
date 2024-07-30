FROM python:3.12-slim

# Install masker itself
RUN --mount=source=dist,target=/dist \
	PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir /dist/*.whl

# COPY masker/dist/*.whl /

# RUN --mount=source=dist,target=/dist \
# 	PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir /dist/*.whl

# Install nopperabo and it's deps
COPY pyproject.toml README.md src/nopperabo/nopperabo.py /scripts/
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir /scripts/

ENTRYPOINT ["/scripts/nopperabo.py"]
