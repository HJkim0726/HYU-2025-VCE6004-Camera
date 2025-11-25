#!/bin/bash

set -o errexit

echo "This is a script to assist with installation of the Spinnaker SDK."
echo "Automatically installing all Spinnaker SDK packages without prompts."
echo

set +o errexit
EXISTING_VERSION=$(dpkg -s spinnaker 2> /dev/null | grep '^Version:' | sed 's/^.*: //')
set -o errexit

if [ ! -z "$EXISTING_VERSION" ]; then
    echo "A previous installation of Spinnaker has been detected on this machine (Version: $EXISTING_VERSION)." >&2
    echo "Continuing with installation and overwriting/keeping packages as per dpkg defaults."
fi

echo "Installing Spinnaker packages..."

sudo dpkg -i libgentl_*.deb
sudo dpkg -i libspinnaker_*.deb
sudo dpkg -i libspinnaker-dev_*.deb
sudo dpkg -i libspinnaker-c_*.deb
sudo dpkg -i libspinnaker-c-dev_*.deb
sudo dpkg -i libspinvideo_*.deb
sudo dpkg -i libspinvideo-dev_*.deb
sudo dpkg -i libspinvideo-c_*.deb
sudo dpkg -i libspinvideo-c-dev_*.deb
sudo dpkg -i spinview-qt_*.deb
sudo dpkg -i spinview-qt-dev_*.deb
sudo dpkg -i spinupdate_*.deb
sudo dpkg -i spinupdate-dev_*.deb
sudo dpkg -i spinnaker_*.deb
sudo dpkg -i spinnaker-doc_*.deb

echo
echo "Adding udev entry to allow access to USB hardware (non-interactive)..."
echo "Launching udev configuration script..."
sudo sh configure_spinnaker.sh

echo
echo "Setting USB-FS memory size to 1000 MB at startup via /etc/rc.local (non-interactive)..."
echo "Launching USB-FS configuration script..."
sudo sh configure_usbfs.sh

echo
echo "Adding Spinnaker prebuilt examples to system path (non-interactive)..."
echo "Launching Spinnaker paths configuration script..."
sudo sh configure_spinnaker_paths.sh

echo

ARCH=$(ls libspinnaker_* | grep -oP '[0-9]_\K.*(?=.deb)' || [[ $? == 1 ]])
if [ "$ARCH" = "arm64" ]; then
    BITS=64
elif [ "$ARCH" = "armhf" ]; then
    BITS=32
fi

if [ -z "$BITS" ]; then
    echo "Could not automatically add the Spinnaker GenTL Producer to the GenTL environment variable."
    echo "To use the Spinnaker GenTL Producer, please follow the GenTL Setup notes in the included README."
else
    echo
    echo "Automatically adding the Spinnaker GenTL Producer to GENICAM_GENTL${BITS}_PATH (non-interactive)..."
    echo "Launching GenTL path configuration script..."
    sudo sh configure_gentl_paths.sh $BITS
fi

echo
echo "Assuming you will be acquiring images with GigEVision cameras."
echo "Please review section 4 of the README to configure your network adapter appropriately."
echo "For a quick temporary setup, run the network tuning script provided with the SDK that utilizes a standard tool named \"ethtool\"."
echo
echo "To install ethtool, run the following command:"
echo "  sudo apt install ethtool"
echo
echo "To adjust network interface eth0, use the following terminal command to run the script (administrator privileges are required):"
echo "  sudo /opt/spinnaker/bin/gev_nettweak eth0"

echo
echo "Installation complete. You may need to reboot your system for all changes to take effect."
echo
echo "Thank you for installing the Spinnaker SDK."
exit 0
