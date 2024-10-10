# FROM golang:1.14-buster AS novnc-build

# WORKDIR /src

# RUN go mod init build && \
#     go get github.com/geek1011/easy-novnc@v1.1.0 && \
#     go build -o /bin/easy-novnc github.com/geek1011/easy-novnc

FROM tobix/pywine:3.9

# ----------------------------------------------------------------------------------------------
LABEL org.opencontainers.image.source=https://github.com/FortesenseLabs/metatrader-terminal
LABEL org.opencontainers.image.description="Metatrader 5 Terminal (with RPYC API)"
# ----------------------------------------------------------------------------------------------

ENV DISPLAY=:0
ENV HOME=/root
ENV SERVER_HOST='0.0.0.0'
ENV SERVER_PORT=18812
ENV VNC_DESKTOP_NAME="Metatrader5"
ENV VNC_GEOMETRY="1280x800"
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

# COPY --from=novnc-build /bin/easy-novnc /usr/local/bin/
COPY assets/menu.xml /etc/xdg/openbox/
COPY assets/supervisord.conf /etc/

WORKDIR /$HOME/
COPY assets .

# Install MT5
RUN chmod +x xtigervnc.sh easy-novnc.sh run_server.sh \
    install_metatrader5.sh start_metatrader5.sh && \
    rm menu.xml supervisord.conf

# RUN ./install_metatrader5.sh
RUN tar -xzf Metatrader-5.tar.gz -C "$DRIVE_C/Program Files/" && \
    mv "$DRIVE_C/Program Files/Metatrader-5/" "$DRIVE_C/Program Files/MetaTrader 5/" && \
    mv metatrader.desktop /usr/share/applications/ && \
    rm Metatrader-5.tar.gz 

RUN wine pip install -r requirements.txt

EXPOSE 5900 18812 

CMD ["supervisord"] 
