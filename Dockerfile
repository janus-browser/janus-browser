ARG dataset_source=kaggle

FROM python:3.13-slim AS base
    COPY . /tf-disco
    WORKDIR /tf-disco

    # image metadata
    LABEL org.opencontainers.image.description="Docker image for the TF-DISCO Browser"
    LABEL org.opencontainers.image.authors="Sreenikethan Iyer, Joseph Cijo"
    LABEL org.opencontainers.image.documentation="https://github.com/tf-disco/tf-disco/blob/main/README.md"

    # uv, because pip is slow
    ENV UV_PROJECT_ENVIRONMENT=/usr/local
    RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/uv ["/uv", "sync"]

    # get muscle
    ADD https://github.com/tf-disco/muscle/releases/download/v5.3/muscle-linux-x86.v5.3 ./muscle
    RUN chmod +x ./muscle
    ENV MUSCLE_PATH=muscle

    ENV IS_DOCKER=1

    # datatset shenanigans
    FROM base AS stage_copy
        ENV DATASET_PATH_OVERRIDE=./tf-disco-data
        COPY --from=dataset_path . ./tf-disco-data

    FROM base AS stage_mount
        ENV DATASET_PATH_OVERRIDE=/tf-disco-data
        VOLUME ["/tf-disco-data"]

    FROM base AS stage_kaggle
        RUN python -c "import kagglehub; from app.utils.constants import KAGGLE_HANDLE; kagglehub.dataset_download(handle=KAGGLE_HANDLE)"

FROM stage_${dataset_source} AS final
    EXPOSE 8501
    ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
