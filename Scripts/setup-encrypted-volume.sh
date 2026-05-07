#!/usr/bin/env bash
# Setup LUKS2 encrypted volume for slide storage
# Usage: sudo ./setup-encrypted-volume.sh /dev/sdX /data/slides
#
# Prerequisites: cryptsetup, root access
# WARNING: This will DESTROY all data on the target device.

set -euo pipefail

DEVICE="${1:?Usage: $0 <device> <mount-point>}"
MOUNT_POINT="${2:?Usage: $0 <device> <mount-point>}"
MAPPER_NAME="slides_crypt"

# Safety checks
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Must run as root" >&2
    exit 1
fi

if [ ! -b "$DEVICE" ]; then
    echo "ERROR: $DEVICE is not a block device" >&2
    exit 1
fi

if mount | grep -q "$DEVICE"; then
    echo "ERROR: $DEVICE is currently mounted. Unmount first." >&2
    exit 1
fi

echo "=== VarunaPoC Encrypted Volume Setup ==="
echo "Device:      $DEVICE"
echo "Mount point: $MOUNT_POINT"
echo "Mapper:      /dev/mapper/$MAPPER_NAME"
echo ""
echo "WARNING: All data on $DEVICE will be DESTROYED."
read -rp "Type 'yes' to continue: " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

# Step 1: Format with LUKS2 (AES-256-XTS)
echo ""
echo "[1/5] Formatting $DEVICE with LUKS2..."
cryptsetup luksFormat --type luks2 --cipher aes-xts-plain64 --key-size 512 "$DEVICE"

# Step 2: Open encrypted volume
echo "[2/5] Opening encrypted volume..."
cryptsetup open "$DEVICE" "$MAPPER_NAME"

# Step 3: Create filesystem
echo "[3/5] Creating ext4 filesystem..."
mkfs.ext4 -L slides "/dev/mapper/$MAPPER_NAME"

# Step 4: Mount
echo "[4/5] Mounting at $MOUNT_POINT..."
mkdir -p "$MOUNT_POINT"
mount "/dev/mapper/$MAPPER_NAME" "$MOUNT_POINT"

# Step 5: Backup LUKS header
HEADER_BACKUP="$MOUNT_POINT/../luks-header-$(basename "$DEVICE").bin"
echo "[5/5] Backing up LUKS header to $HEADER_BACKUP..."
cryptsetup luksHeaderBackup "$DEVICE" --header-backup-file "$HEADER_BACKUP"
chmod 600 "$HEADER_BACKUP"

echo ""
echo "=== Setup Complete ==="
echo "Encrypted volume mounted at: $MOUNT_POINT"
echo "LUKS header backup:          $HEADER_BACKUP"
echo ""
echo "IMPORTANT: Move the header backup to a separate, secure location."
echo ""
echo "To use with Docker, add to docker-compose.yml:"
echo "  volumes:"
echo "    - $MOUNT_POINT:/Slides:ro"
