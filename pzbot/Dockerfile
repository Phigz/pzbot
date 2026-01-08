FROM python:3.11-slim

# Install dependencies for SteamCMD and Project Zomboid lzma
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y \
    lib32gcc-s1 \
    lib32stdc++6 \
    curl \
    wget \
    ca-certificates \
    git \
    procps \
    xdotool \
    xvfb \
    fluxbox \
    x11vnc \
    && rm -rf /var/lib/apt/lists/*

# Install SteamCMD
ARG STEAM_BETA_BRANCH=""
# Example: --build-arg STEAM_BETA_BRANCH="-beta legacy41_78"
# Note: Should be "-beta <branch>" or empty for stable.

RUN mkdir -p /root/steamcmd && \
    cd /root/steamcmd && \
    curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar zxvf - && \
    ./steamcmd.sh +quit

# Set up environment variables
ENV PATH="/root/steamcmd:${PATH}"
ENV PYTHONUNBUFFERED=1

# Working directory
WORKDIR /app

# Copy requirements if they exist
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy entrypoint
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["tail", "-f", "/dev/null"]
