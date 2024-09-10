#!/bin/sh

# Configuration variables
mt5file='/config/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe'
wine_executable="wine"
mono_url="https://dl.winehq.org/wine/wine-mono/8.0.0/wine-mono-8.0.0-x86.msi"
mt5setup_url="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"

# Function to display a graphical message
show_message() {
    echo $1
}

# Function to check if a dependency is installed
check_dependency() {
    if ! command -v $1 &> /dev/null; then
        echo "$1 is not installed. Please install it to continue."
        exit 1
    fi
}

# Function to check if a Python package is installed
is_python_package_installed() {
    python3 -c "import pkg_resources; exit(not pkg_resources.require('$1'))" 2>/dev/null
    return $?
}

# Function to check if a Python package is installed in Wine
is_wine_python_package_installed() {
    $wine_executable python -c "import pkg_resources; exit(not pkg_resources.require('$1'))" 2>/dev/null
    return $?
}

# Check for necessary dependencies
check_dependency "curl"
check_dependency "$wine_executable"

# Install Mono if not present
if [ ! -e "/config/.wine/drive_c/windows/mono" ]; then
    show_message "[1/7] Downloading and installing Mono..."
    curl -o /config/.wine/drive_c/mono.msi $mono_url
    WINEDLLOVERRIDES=mscoree=d $wine_executable msiexec /i /config/.wine/drive_c/mono.msi /qn
    rm /config/.wine/drive_c/mono.msi
    show_message "[1/7] Mono installed."
else
    show_message "[1/7] Mono is already installed."
fi

# Check if MetaTrader 5 is already installed
if [ -e "$mt5file" ]; then
    show_message "[2/7] File $mt5file already exists."
else
    show_message "[2/7] File $mt5file is not installed. Installing..."
    
    # Set Windows 10 mode in Wine and download and install MT5
    $wine_executable reg add "HKEY_CURRENT_USER\\Software\\Wine" /v Version /t REG_SZ /d "win10" /f
    show_message "[3/7] Downloading MT5 installer..."
    curl -o /config/.wine/drive_c/mt5setup.exe $mt5setup_url
    show_message "[3/7] Installing MetaTrader 5..."
    $wine_executable "/config/.wine/drive_c/mt5setup.exe" "/auto" &
    wait
    rm -f /config/.wine/drive_c/mt5setup.exe
fi

# Recheck if MetaTrader 5 is installed
if [ -e "$mt5file" ]; then
    show_message "[4/7] File $mt5file is installed. Running MT5..."
    $wine_executable "$mt5file" &
else
    show_message "[4/7] File $mt5file is not installed. MT5 cannot be run."
fi


# # MetaTrader download url
# URL="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"

# # Download MetaTrader
# wget $URL

# # Set environment to Windows 10
# winecfg -v=win10
# # Start MetaTrader installer
# wine mt5setup.exe

# # Installing MT5
# echo "Installing MT5"
# if ! test -f "mt5setup.exe"; then
# wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe
# fi
# if ! test -f "/workspaces/releat/data/platforms/mt5/0/MetaTrader 5/terminal64.exe"; then
#     wine mt5setup.exe /auto
#     mkdir -p /workspaces/releat/data/platforms/mt5/0
#     cp -r "/root/.wine/drive_c/Program Files/MetaTrader 5" /workspaces/releat/data/platforms/mt5/0
# fi
# # && rm mt5setup.exe \
# echo "MT5 installed successfully"

# https://github.com/gmag11/MetaTrader5-Docker-Image/
# https://github.com/elestio-examples/metatrader5/