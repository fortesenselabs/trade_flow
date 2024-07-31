FROM alpine:3.15 AS st-builder

RUN apk add --no-cache make gcc git freetype-dev \
    fontconfig-dev musl-dev xproto libx11-dev \
    libxft-dev libxext-dev
RUN git clone https://github.com/DenisKramer/st.git /work
WORKDIR /work
RUN make

# ----------------------------------------------------------------------------

FROM alpine:3.15 AS xdummy-builder

RUN apk add --no-cache make gcc freetype-dev \
    fontconfig-dev musl-dev xproto libx11-dev \
    libxft-dev libxext-dev avahi-libs libcrypto3 libssl3 libvncserver libx11 libxdamage libxext libxfixes libxi libxinerama libxrandr libxtst musl samba-winbind 
RUN apk add --no-cache linux-headers
RUN apk add x11vnc 
RUN Xdummy -install

# ----------------------------------------------------------------------------

LABEL org.opencontainers.image.source=https://github.com/FortesenseLabs/metatrader-terminal
LABEL org.opencontainers.image.description="Metatrader 5 Terminal API"
LABEL org.opencontainers.image.licenses=MIT

# ----------------------------------------------------------------------------
FROM alpine:3.15 AS base


USER root
ENV WINEPREFIX=/root/.wine
ENV WINEARCH=win64
ENV DISPLAY :0
ENV USER=root
ENV PASSWORD=root
ENV HOME=/root