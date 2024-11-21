# Use an official Alpine image as the base image
FROM alpine:3.20.2

# Install dependencies
RUN apk update && \
    apk add --no-cache \
    build-base \
    linux-headers \
    libffi-dev \
    openssl-dev \
    zlib-dev \
    jpeg-dev \
    bash \
    curl \
    git \
    readline-dev \
    bzip2-dev \
    sqlite-dev \
    xz-dev \
    tk-dev \
    cmake \
    autoconf \
    automake \
    libtool \
    make \
    g++ \
    ninja

# Install pyenv
ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}"

RUN git clone https://github.com/pyenv/pyenv.git ${PYENV_ROOT} && \
    cd ${PYENV_ROOT} && \
    src/configure && \
    make -C src

# Install Python 3.10.14 using pyenv
RUN pyenv install 3.10.14 && \
    pyenv global 3.10.14

# Upgrade pip and install necessary Python packages
RUN pip install --upgrade pip setuptools wheel

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy the pyproject.toml and poetry.lock files into the container
COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false && poetry install --no-root --no-dev

# Copy the rest of the application code into the container
COPY . .

# Expose the port that the Gradio app runs on
EXPOSE 8000

# Command to run the Gradio app
CMD ["poetry", "run", "python", "app.py"]
