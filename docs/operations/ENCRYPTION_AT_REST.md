# Encryption at Rest

Guide for encrypting slide storage and database volumes in VarunaPoC deployments.

## Overview

Hospital slide data is Protected Health Information (PHI). Encryption at rest protects against physical theft or unauthorized disk access. This guide covers Linux (LUKS) and Windows NAS (VeraCrypt) scenarios.

## 1. Linux: LUKS Encrypted Volume

### Initial Setup

```bash
# Create encrypted partition (LUKS2, AES-256-XTS)
sudo cryptsetup luksFormat --type luks2 /dev/sdX

# Open the encrypted volume
sudo cryptsetup open /dev/sdX slides_crypt

# Create filesystem
sudo mkfs.ext4 /dev/mapper/slides_crypt

# Mount
sudo mkdir -p /data/slides
sudo mount /dev/mapper/slides_crypt /data/slides
```

### Automated Script

Use `scripts/setup-encrypted-volume.sh` to automate LUKS setup:

```bash
sudo ./scripts/setup-encrypted-volume.sh /dev/sdX /data/slides
```

### Auto-Unlock at Boot

For servers with TPM2 or a key file (not recommended for highest security):

```bash
# Option A: Key file (requires secure key storage)
sudo cryptsetup luksAddKey /dev/sdX /root/slides.key
# Add to /etc/crypttab:
# slides_crypt /dev/sdX /root/slides.key luks

# Option B: systemd-cryptenroll with TPM2 (recommended)
sudo systemd-cryptenroll --tpm2-device=auto /dev/sdX
```

### Docker Mount (Read-Only)

In `docker-compose.production.yml`:

```yaml
services:
  backend:
    volumes:
      - /data/slides:/Slides:ro  # Encrypted volume, mounted read-only
```

The Docker container sees decrypted files. Encryption is transparent at the block level.

## 2. PostgreSQL Volume Encryption

### Option A: LUKS for the Entire Data Directory

```bash
# Encrypt the PostgreSQL data volume
sudo cryptsetup luksFormat /dev/sdY
sudo cryptsetup open /dev/sdY pgdata_crypt
sudo mkfs.ext4 /dev/mapper/pgdata_crypt
sudo mount /dev/mapper/pgdata_crypt /data/pgdata
```

Docker compose:

```yaml
services:
  db:
    volumes:
      - /data/pgdata:/var/lib/postgresql/data
```

### Option B: PostgreSQL TDE (Transparent Data Encryption)

PostgreSQL 16+ supports TDE via extensions. Not yet standard in Alpine images. LUKS is the recommended approach for now.

## 3. Windows NAS: VeraCrypt

For Windows-based NAS hosting slides:

1. Install VeraCrypt on the NAS server
2. Create an encrypted volume container or encrypt the slide partition
3. Mount the volume and share via SMB
4. Docker host mounts the SMB share:

```yaml
volumes:
  slides:
    driver: local
    driver_opts:
      type: cifs
      o: "username=${SMB_USER},password=${SMB_PASS},uid=1000"
      device: "//nas-server/slides"
```

## 4. Key Management

### LUKS Header Backup

**Critical:** Back up the LUKS header. If the header is corrupted, all data is permanently lost.

```bash
# Backup header
sudo cryptsetup luksHeaderBackup /dev/sdX --header-backup-file luks-header-slides.bin

# Store backup: separate physical location, encrypted USB, or HSM
# Never store header backup on the same disk as the encrypted volume
```

### Passphrase Storage

- **Development:** Password manager (1Password, Bitwarden)
- **Production:** Hardware Security Module (HSM) or HashiCorp Vault
- **Minimum:** Sealed envelope in hospital safe (two-person rule)

### Recovery Procedure

1. Boot from recovery media
2. Restore LUKS header if needed: `cryptsetup luksHeaderRestore /dev/sdX --header-backup-file luks-header-slides.bin`
3. Open volume: `cryptsetup open /dev/sdX slides_crypt`
4. Mount and verify: `mount /dev/mapper/slides_crypt /data/slides && ls /data/slides`

## 5. Verification

```bash
# Verify volume is encrypted
sudo cryptsetup status slides_crypt

# Verify encryption algorithm
sudo cryptsetup luksDump /dev/sdX | grep -E "Cipher|Key"

# Expected: aes-xts-plain64, Key: 512 bits
```

## 6. GDPR Compliance Note

Article 32 GDPR requires "encryption of personal data" as a security measure. With LUKS:
- Data is encrypted with AES-256 at the block level
- Decryption requires the passphrase/key (not accessible from a stolen disk)
- Audit trail (`auth/audit.py`) logs all data access for Art. 30 register

**Status:** Documented and scripted. Deployment-specific (depends on hardware and hospital IT policy).
