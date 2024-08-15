FROM golang:1.14-buster AS novnc-build

WORKDIR /src

RUN go mod init build && \
    go get github.com/geek1011/easy-novnc@v1.1.0 && \
    go build -o /bin/easy-novnc github.com/geek1011/easy-novnc

FROM tobix/pywine:3.9

# ----------------------------------------------------------------------------
LABEL org.opencontainers.image.source=https://github.com/FortesenseLabs/metatrader-terminal
LABEL org.opencontainers.image.description="Metatrader 5 Terminal RPYC API"
# ----------------------------------------------------------------------------

# USER root
ENV DISPLAY :0
# ENV USER=root
# ENV PASSWORD=root
ENV HOME=/root
ENV SERVER_HOST='0.0.0.0'
ENV SERVER_PORT=18812
ENV DRIVE_C=${WINEPREFIX}/drive_c
STOPSIGNAL SIGRTMIN+3

# Install required packages
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends openbox tigervnc-standalone-server supervisor gosu && \
    rm -rf /var/lib/apt/lists && \
    mkdir -p /usr/share/desktop-directories

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends lxterminal nano openssh-client \ 
    rsync xdg-utils htop \
    tar xzip gzip bzip2 zip unzip wget && \
    apt-get clean && \ 
    rm -rf /var/lib/apt/lists

COPY --from=novnc-build /bin/easy-novnc /usr/local/bin/
COPY assets/menu.xml /etc/xdg/openbox/
COPY assets/supervisord.conf /etc/


WORKDIR /$HOME/
COPY assets .

RUN tar -xzf Metatrader-5.tar.gz -C "$DRIVE_C/" \
    && mv metatrader.desktop /usr/share/applications/ \
    && rm menu.xml supervisord.conf Metatrader-5.tar.gz 

RUN wine pip install -r requirements.txt \
    && chmod +x run_server.sh

EXPOSE 18812 8000 
# 9876 5900 | if tigervnc needs to be accessed use a proxy such as Caddy

CMD ["supervisord"]

# https://www.digitalocean.com/community/tutorials/how-to-remotely-access-gui-applications-using-docker-and-caddy-on-debian-9
# https://github.com/oposs/tl-docker/
# 
# add option to automatically connect to an instance
# /usr/local/bin/easy-novnc --addr :8080 --host localhost --port 5900 --no-url-password --novnc-params "resize=remote"
# Hide connection options from the main screen: --basic-ui
# https://github.com/pgaskin/easy-novnc

# TODO: upgrade to wine >= 8 as wine 7 is unstable and unsupported by MT5  