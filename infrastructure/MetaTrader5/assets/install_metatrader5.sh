#!/bin/sh

# Run tigervnc
DISPLAY=:0
nohup /root/xtigervnc.sh &
nohup /usr/bin/openbox &
# nohup supervisord &

# MetaTrader download url
URL="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
MT5_FILE="/opt/wineprefix/drive_c/Program Files/MetaTrader 5/terminal64.exe"

# Function to display a graphical message
show_message() {
    echo $1
}

# Check if MetaTrader 5 is already installed
if [ -e "$MT5_FILE" ]; then
    show_message "File $mt5file already exists."
else
    show_message "File $MT5_FILE is not installed. Installing..."
    
    # download and install MT5
    show_message "Downloading MT5 installer..."
    if ! test -f "/root/mt5setup.exe"; then
        wget $URL
    fi
    
    show_message "Installing MetaTrader 5..."
    wine /root/mt5setup.exe /auto & wait
    rm -f /root/mt5setup.exe
    # mkdir /opt/wineprefix/drive_c/Metatrader-5
    # cp -r "/opt/wineprefix/drive_c/Program Files/MetaTrader 5" /opt/wineprefix/drive_c/Metatrader-5
    # rm -r "/opt/wineprefix/drive_c/Program Files/MetaTrader 5"
fi

# Recheck if MetaTrader 5 is installed
if [ -e "$MT5_FILE" ]; then
    show_message "File $MT5_FILE is installed. Running MT5..."
    wine "$MT5_FILE" &
else
    show_message "File $MT5_FILE is not installed. MT5 cannot be run."
fi

show_message "Installing MT5 Terminal Python Dependencies"
wine pip install -r requirements.txt


# References:
# https://github.com/gmag11/MetaTrader5-Docker-Image/
# https://github.com/elestio-examples/metatrader5/