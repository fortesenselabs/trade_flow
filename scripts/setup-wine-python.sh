#!/bin/bash

# Define download URL and filename with specific version
version="3.11.9"
python_download_url="https://www.python.org/ftp/python/$version/python-$version-embed-amd64.zip"
pip_download_url="https://bootstrap.pypa.io/get-pip.py"
filename="python-embed-amd64.zip"

# Define folder name
folder_path="wenv"

# Check if wget is installed
if ! command -v wget &> /dev/null; then
    echo "Error: wget is not installed. Please install wget before running this script."
    exit 1
fi

# Create the folder (ignore error if it already exists)
mkdir -p "$folder_path"

# Download the Python archive
echo "Downloading Python..."
wget -qO "$folder_path/$filename" "$python_download_url"

# Check if download was successful
if [ $? -ne 0 ]; then
    echo "Error: Download failed."
    exit 1
fi

# Extract the archive
echo "Extracting Python..."
unzip -q "$folder_path/$filename" -d "$folder_path"

# Build the full path to the python executable
python_executable="$folder_path/python.exe"

# Set wine prefix
wine winecfg -v win10

# Check if pip is already installed (optional)
pip_check_output="$(wine $python_executable -m pip --version 2>&1)"
echo $pip_check_output
if [[ $pip_check_output == *"No module named pip"* ]]; then
    echo "Installing pip..."
    
    # Download get-pip.py script (adjust URL if necessary)
    wget -qO $folder_path/get-pip.py "$pip_download_url"
    
    # Install pip within the extracted Python directory
    wine "$python_executable" $folder_path/get-pip.py --target="$folder_path"
    
    if [ $? -ne 0 ]; then
        echo "Warning: pip installation failed. You may need to install it manually."
    fi
else
    echo "pip is already installed."
fi

echo "Python and pip (potentially) installed in: $folder_path"

# Cleanup (optional, remove downloaded archive)
rm -f "$folder_path/$filename"
rm "$folder_path/get-pip.py"  # Clean up get-pip.py

# Install MetaTrader5 package
echo "Installing MetaTrader5 package.."
wine "$python_executable" -m pip install MetaTrader5
echo "Done"

# Install rpyc package
echo "Installing rpyc package.."
wine "$python_executable" -m pip install rpyc==5.2.3
echo "Done"

# Install mt5linux package
echo "Installing mt5linux package.."
wine "$python_executable" -m pip install -e packages/mt5linux
echo "Done"

# Start server
echo "Start mt5linux server"
wine "$python_executable" -m mt5linux $python_executable


# References:
# - https://github.com/pleiszenburg/wenv/
