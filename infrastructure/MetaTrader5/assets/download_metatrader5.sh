#!/bin/sh

# MetaTrader download url
URL="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"

# Download MetaTrader
wget $URL

# Set environment to Windows 10
winecfg -v=win10
# Start MetaTrader installer
wine mt5setup.exe