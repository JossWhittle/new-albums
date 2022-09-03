FROM ubuntu:22.04

# Install runtime packages
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections && \
    apt-get update -y && apt-get install --no-install-recommends -y dialog apt-utils && \
    apt-get install --no-install-recommends -y python3 python3-pip && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 10 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 10 && \
    apt-get autoremove -y --purge && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt
WORKDIR /usr/local/new-albums
COPY requirements.txt /usr/local/new-albums

# Install dependencies first so they are cached in their own layer,
# allowing faster rebuilding when the application changes...
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/* && rm -rf /tmp/*

# Copy the application
COPY . /usr/local/new-albums

# Install the application
RUN pip install --no-cache-dir --upgrade -e . && \
    python -m pytest tests && \
    rm -rf /root/.cache/* && rm -rf /tmp/*
