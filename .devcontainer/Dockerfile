FROM python:3.13

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade \
    homeassistant \
    colorlog \
    ruff \
    numpy \
    hassil \
    av \
    go2rtc-client \
    zeroconf \
    async-upnp-client \
    pyserial \
    aiodhcpwatcher \
    PyTurboJPEG \
    aiodiscover \
    ha-ffmpeg \
    home-assistant-intents \
    mutagen

RUN cd && mkdir -p /config/custom_components

WORKDIR /workspace

# Set the default shell to bash instead of sh
ENV SHELL /bin/bash
