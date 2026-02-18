# Belgian eHealth Organizational Certificate Setup Guide

**Document Version:** 1.0
**Date:** 2026-02-18
**Classification:** Integration Guide (Documentation Only)
**Applicable Standards:** Belgian eHealth Platform, X.509v3, SAML 2.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Belgian eHealth Platform Overview](#2-belgian-ehealth-platform-overview)
3. [Prerequisites](#3-prerequisites)
4. [Application Process](#4-application-process)
5. [Certificate Format and Key Management](#5-certificate-format-and-key-management)
6. [Integration with VarunaPoC Keycloak](#6-integration-with-varunapoc-keycloak)
7. [Testing with eHealth Acceptance Environment](#7-testing-with-ehealth-acceptance-environment)
8. [Certificate Renewal Procedures](#8-certificate-renewal-procedures)
9. [Security Considerations](#9-security-considerations)
10. [Troubleshooting](#10-troubleshooting)
11. [References](#11-references)

---

## 1. Executive Summary

Belgian healthcare applications that interact with federal eHealth services must authenticate
using organizational certificates issued by the Belgian eHealth Platform. This guide provides
a step-by-step process for CHU UCL Namur to obtain and integrate an eHealth organizational
certificate with VarunaPoC's Keycloak-based authentication system.

**Why this matters for VarunaPoC:**
- CHU UCL Namur is the primary deployment site for VarunaPoC
- Belgian hospital applications accessing eHealth services (eHealthBox, MyCareNet, KMEHR
  messaging) require eHealth certificates for mutual TLS authentication
- Future integration with Belgian national health data infrastructure (eHealth Platform,
  BMSP -- Belgian Medical Software Platform) requires this certificate
- Keycloak, VarunaPoC's identity provider, can federate with eHealth via SAML 2.0

**Current state:** VarunaPoC uses Keycloak for OIDC PKCE authentication. The eHealth
certificate integration described here is a preparatory step for when the platform
needs to connect to Belgian national health services.

---

## 2. Belgian eHealth Platform Overview

### 2.1 What is the eHealth Platform?

The Belgian eHealth Platform (Plateforme eHealth / eHealth-platform) is a federal public
institution that provides a set of basic services for secure electronic data exchange in
Belgian healthcare. It acts as a trusted intermediary between healthcare actors.

### 2.2 Key Services Relevant to VarunaPoC

| Service | Description | VarunaPoC Relevance |
|---------|-------------|-------------------|
| **eHealthBox** | Secure messaging between healthcare providers | Pathology report exchange |
| **Consult RN** | National Registry consultation | Patient identification |
| **MyCareNet** | Social security data exchange | Reimbursement context |
| **KMEHR** | Belgian health message standard | Structured pathology reports |
| **Recip-e** | Electronic prescription | Not directly relevant |
| **STS (Secure Token Service)** | SAML token issuance | Authentication federation |

### 2.3 Authentication Architecture

```
+-------------------+          +----------------------+
|   VarunaPoC       |          |  eHealth Platform    |
|   (Keycloak SP)   |          |  (STS / IdP)         |
|                   |          |                      |
| 1. User login     |          |                      |
|    via Keycloak   |          |                      |
|                   |  SAML    |                      |
| 2. Keycloak ------+--------->| 3. Validate org cert |
|    sends SAML     |  Request |    + user identity   |
|    AuthnRequest   |          |                      |
|                   |  SAML    |                      |
| 5. Keycloak <-----+----------| 4. Issue SAML        |
|    receives       | Response |    assertion with     |
|    assertion      |          |    eHealth attributes |
|                   |          |                      |
| 6. Map to local   |          |                      |
|    Keycloak roles  |          |                      |
+-------------------+          +----------------------+
        |
        | mTLS with eHealth org certificate
        v
+-------------------+
| eHealth Web       |
| Services (SOAP)   |
| eHealthBox, etc.  |
+-------------------+
```

---

## 3. Prerequisites

### 3.1 Organizational Requirements

| Requirement | Description | How to Obtain |
|-------------|-------------|---------------|
| **KBO/BCE Number** | Enterprise number in the Crossroads Bank for Enterprises | CHU UCL Namur already has this (format: 0xxx.xxx.xxx) |
| **NISS/SSIN** | National Social Security Number of the responsible person | Belgian national ID of the IT security officer or delegated person |
| **eHealth Platform Registration** | Organization must be registered with eHealth | Apply via https://www.ehealth.fgov.be |
| **Technical Contact** | Named person responsible for certificate management | Designate from CHU UCL Namur IT department |
| **Legal Mandate** | Organization must have legal capacity to act as healthcare provider | Hospital has this by default |

### 3.2 Technical Requirements

| Requirement | Specification | Notes |
|-------------|--------------|-------|
| **Java / OpenSSL** | For CSR generation and keystore management | OpenSSL 1.1+ recommended |
| **PKCS#12 Keystore** | Required format for eHealth certificates | .p12 / .pfx format |
| **DNS** | Stable FQDN for the application server | e.g., varuna.chuuclnamur.be |
| **Network** | Outbound HTTPS to eHealth endpoints | Port 443 to *.ehealth.fgov.be |
| **Keycloak** | Version 22+ with SAML SP capability | VarunaPoC already uses Keycloak |

### 3.3 Belgian eID Infrastructure

The eHealth certificate workflow involves the Belgian eID (electronic identity card) for
personal authentication of the responsible person during the application process. Ensure
the responsible person has:

- A valid Belgian eID card
- An eID card reader
- The Belgium eID middleware installed (https://eid.belgium.be)

---

## 4. Application Process

### Step 1: Register on the eHealth Platform Portal

1. Navigate to https://www.ehealth.fgov.be/ehealthplatform
2. Click "Registration" / "Enregistrement"
3. Authenticate using Belgian eID of the responsible person (NISS/SSIN holder)
4. Register the organization using the KBO/BCE enterprise number
5. Designate the technical contact person

### Step 2: Request an Organizational Certificate

1. Log in to the eHealth Platform portal with eID
2. Navigate to "Certificate Management" / "Gestion des certificats"
3. Select "Request new organizational certificate"
4. Fill in the required fields:

| Field | Value | Example for CHU UCL Namur |
|-------|-------|--------------------------|
| Organization Name | Legal name from KBO/BCE | Centre Hospitalier Universitaire UCL Namur |
| KBO/BCE Number | Enterprise number | 0xxx.xxx.xxx |
| Application Name | Name of the software system | VarunaPoC |
| Environment | Acceptance or Production | Start with Acceptance |
| Certificate Usage | Authentication + Signing | Select both |

### Step 3: Generate Certificate Signing Request (CSR)

Generate a CSR using OpenSSL:

```bash
# Generate a 2048-bit RSA private key
openssl genrsa -aes256 -out varunapoc-ehealth.key 2048

# Generate the CSR
openssl req -new -key varunapoc-ehealth.key -out varunapoc-ehealth.csr \
  -subj "/C=BE/ST=Namur/L=Yvoir/O=CHU UCL Namur/OU=Anatomie Pathologique/CN=VarunaPoC"
```

**Important:** The CSR must match the organization details registered on the eHealth portal.

### Step 4: Upload CSR and Complete Request

1. Upload the generated CSR file (varunapoc-ehealth.csr) to the eHealth portal
2. Review the certificate details
3. Confirm the request
4. The eHealth Platform will process the request (typically 1-5 business days)

### Step 5: Download and Install the Certificate

1. Once approved, download the signed certificate from the eHealth portal
2. The certificate will be in X.509 PEM format (.cer or .pem)
3. Create a PKCS#12 keystore combining the private key and certificate:

```bash
# Combine into PKCS#12 keystore
openssl pkcs12 -export \
  -in varunapoc-ehealth.cer \
  -inkey varunapoc-ehealth.key \
  -certfile ehealth-ca-chain.pem \
  -out varunapoc-ehealth.p12 \
  -name "varunapoc-ehealth"

# Verify the keystore
openssl pkcs12 -info -in varunapoc-ehealth.p12
```

### Step 6: Install CA Chain

Download the eHealth CA certificate chain from:
https://www.ehealth.fgov.be/ehealthplatform/nl/ehealth-certificaten

Install the CA chain in the application's trust store to validate eHealth server certificates
during mTLS handshakes.

---

## 5. Certificate Format and Key Management

### 5.1 Certificate Details

| Attribute | Value |
|-----------|-------|
| Format | X.509v3 |
| Key Algorithm | RSA 2048-bit (minimum) |
| Signature Algorithm | SHA-256 with RSA |
| Validity Period | Typically 3 years |
| Key Usage | Digital Signature, Key Encipherment |
| Extended Key Usage | Client Authentication (1.3.6.1.5.5.7.3.2) |
| Issuer | Belgian eHealth Platform CA |
| Subject | Organization CN (as registered) |

### 5.2 Key Management Best Practices

| Practice | Description |
|----------|-------------|
| **Private key protection** | Store in hardware security module (HSM) or encrypted keystore |
| **Access control** | Restrict keystore file permissions to application service account only |
| **Backup** | Encrypted backup of keystore in secure, separate location |
| **Rotation tracking** | Calendar reminders for certificate expiry (90 days, 30 days, 7 days before) |
| **Revocation readiness** | Know the revocation procedure in case of compromise |
| **Audit logging** | Log all certificate-related operations |

### 5.3 Storage Recommendations for VarunaPoC

```
/etc/varunapoc/certs/
  +-- varunapoc-ehealth.p12          # PKCS#12 keystore (chmod 600)
  +-- ehealth-ca-chain.pem           # CA certificate chain (chmod 644)
  +-- varunapoc-ehealth.key          # Private key backup (chmod 600, encrypted)
```

**Docker deployment:** Mount the certificate directory as a read-only volume:

```yaml
# docker-compose.yml excerpt
services:
  keycloak:
    volumes:
      - /etc/varunapoc/certs:/opt/keycloak/certs:ro
```

---

## 6. Integration with VarunaPoC Keycloak

### 6.1 Architecture Overview

VarunaPoC uses Keycloak as its OIDC identity provider. To integrate with eHealth, Keycloak
is configured as a SAML Service Provider (SP) that federates with the eHealth Secure Token
Service (STS) as the SAML Identity Provider (IdP).

### 6.2 Keycloak SAML SP Configuration

**Step 1: Add eHealth as Identity Provider**

1. Log in to Keycloak Admin Console
2. Navigate to Identity Providers > Add provider > SAML v2.0
3. Configure the following:

| Setting | Value |
|---------|-------|
| Alias | ehealth-sts |
| Display Name | Belgian eHealth Platform |
| Service Provider Entity ID | https://varuna.chuuclnamur.be/auth/realms/varunapoc |
| Single Sign-On Service URL | https://services.ehealth.fgov.be/IAM/Saml2/SSO |
| Single Logout Service URL | https://services.ehealth.fgov.be/IAM/Saml2/SLO |
| NameID Policy Format | urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified |
| Want AuthnRequests Signed | ON |
| Want Assertions Signed | ON |
| Validate Signature | ON |
| SAML Signature Key Name | CERT_SUBJECT |

**Step 2: Import eHealth IdP Metadata**

Download the eHealth STS metadata from:
- Acceptance: https://services-acpt.ehealth.fgov.be/IAM/Saml2/MSS
- Production: https://services.ehealth.fgov.be/IAM/Saml2/MSS

Import via Keycloak Admin Console > Identity Providers > ehealth-sts > Import from URL.

**Step 3: Configure Signing Key**

1. Navigate to Realm Settings > Keys > Providers
2. Add a new RSA key provider using the eHealth PKCS#12 keystore:

| Setting | Value |
|---------|-------|
| Name | ehealth-signing-key |
| Priority | 100 |
| Keystore | /opt/keycloak/certs/varunapoc-ehealth.p12 |
| Keystore Password | (stored in Keycloak vault) |
| Key Alias | varunapoc-ehealth |

**Step 4: Configure Attribute Mapping**

Map eHealth SAML attributes to Keycloak user attributes:

| eHealth SAML Attribute | Keycloak User Attribute | Description |
|----------------------|------------------------|-------------|
| urn:be:fgov:ehealth:1.0:certificateholder:enterprise:cbe-number | cbe_number | Organization KBO/BCE |
| urn:be:fgov:person:ssin | niss | National Registry Number |
| urn:be:fgov:ehealth:1.0:nihii | nihii | NIHII number (healthcare provider) |
| urn:be:fgov:ehealth:1.0:professional:role | ehealth_role | Professional role |

### 6.3 VarunaPoC Role Mapping

Map eHealth professional roles to VarunaPoC application roles:

| eHealth Role | VarunaPoC Role | Access Level |
|-------------|---------------|-------------|
| physician-specialist (pathology) | pathologist | Full viewer + annotations + ML |
| physician | clinician | Viewer + read-only annotations |
| nurse | technician | Viewer only |
| laboratory-technologist | lab_tech | Viewer + upload |
| administrator | admin | Full admin access |

### 6.4 Authentication Flow

```
1. User navigates to VarunaPoC
2. VarunaPoC redirects to Keycloak login page
3. User selects "Login with eHealth" (Belgian eID)
4. Keycloak sends SAML AuthnRequest to eHealth STS
   (signed with eHealth organizational certificate)
5. eHealth STS authenticates user via Belgian eID
6. eHealth STS returns SAML Response with attributes
7. Keycloak validates response, maps attributes to user profile
8. Keycloak issues OIDC token to VarunaPoC
9. VarunaPoC grants access based on mapped roles
```

---

## 7. Testing with eHealth Acceptance Environment

### 7.1 Acceptance Environment Endpoints

| Service | URL |
|---------|-----|
| Portal | https://www.ehealth.fgov.be/ehealthplatform (acceptance section) |
| STS Metadata | https://services-acpt.ehealth.fgov.be/IAM/Saml2/MSS |
| STS SSO | https://services-acpt.ehealth.fgov.be/IAM/Saml2/SSO |
| eHealthBox | https://services-acpt.ehealth.fgov.be/ehBoxConsultation/v3 |

### 7.2 Testing Procedure

1. **Request acceptance certificate** (separate from production)
   - Follow the same application process (Section 4) but select "Acceptance" environment
   - Acceptance certificates cannot be used in production and vice versa

2. **Configure Keycloak for acceptance**
   - Use acceptance STS URLs in the Identity Provider configuration
   - Import acceptance environment metadata

3. **Test authentication flow**
   ```bash
   # Verify eHealth STS metadata is accessible
   curl -v https://services-acpt.ehealth.fgov.be/IAM/Saml2/MSS

   # Verify mTLS with eHealth acceptance
   curl -v --cert varunapoc-ehealth.cer --key varunapoc-ehealth.key \
     https://services-acpt.ehealth.fgov.be/IAM/Saml2/MSS
   ```

4. **Test with simulated users**
   - eHealth provides test NISS/SSIN numbers for the acceptance environment
   - Use eID test cards or simulated authentication as provided by eHealth support

5. **Validate attribute mapping**
   - Verify that eHealth SAML attributes appear correctly in Keycloak user profile
   - Verify that VarunaPoC role mapping assigns correct permissions

### 7.3 Common Testing Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| SAML signature validation failure | Clock skew between servers | Synchronize NTP; allow 5-minute skew in Keycloak |
| Certificate not recognized | Wrong environment certificate used | Ensure acceptance cert for acceptance, production for production |
| Missing attributes in assertion | Attribute mapping not configured | Check Keycloak IdP mapper configuration |
| mTLS handshake failure | CA chain not installed | Import eHealth CA chain into truststore |

---

## 8. Certificate Renewal Procedures

### 8.1 Renewal Timeline

| Milestone | Action |
|-----------|--------|
| **90 days before expiry** | Initiate renewal process on eHealth portal |
| **60 days before expiry** | Generate new CSR and submit to eHealth |
| **30 days before expiry** | Install new certificate in parallel (testing) |
| **14 days before expiry** | Switch to new certificate in production |
| **0 days (expiry)** | Old certificate becomes invalid |

### 8.2 Renewal Steps

1. Log in to eHealth Platform portal
2. Navigate to Certificate Management
3. Select the expiring certificate
4. Click "Renew" / "Renouveler"
5. Generate a new CSR (same or updated key pair)
6. Upload the new CSR
7. Once approved, download the new certificate
8. Create a new PKCS#12 keystore
9. Update the Keycloak keystore configuration
10. Test in acceptance environment first
11. Deploy to production

### 8.3 Automated Monitoring

Implement certificate expiry monitoring:

```bash
# Check certificate expiry date
openssl x509 -enddate -noout -in varunapoc-ehealth.cer

# Script for automated alerting (add to cron)
#!/bin/bash
CERT_FILE="/etc/varunapoc/certs/varunapoc-ehealth.cer"
DAYS_WARN=90
EXPIRY=$(openssl x509 -enddate -noout -in "$CERT_FILE" | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

if [ "$DAYS_LEFT" -lt "$DAYS_WARN" ]; then
  echo "WARNING: eHealth certificate expires in $DAYS_LEFT days" | \
    mail -s "VarunaPoC eHealth Certificate Expiry Warning" it-team@chuuclnamur.be
fi
```

---

## 9. Security Considerations

### 9.1 Certificate Security

| Threat | Mitigation |
|--------|-----------|
| Private key compromise | Store in HSM or encrypted keystore; restrict file permissions |
| Man-in-the-middle attack | mTLS ensures both server and client authentication |
| Certificate theft | Monitor usage via eHealth audit logs; immediate revocation if suspected |
| Weak cryptography | Use RSA 2048+ or ECDSA P-256+; SHA-256 signatures |

### 9.2 GDPR/RGPD Alignment

The eHealth certificate integration involves processing of personal data (NISS/SSIN numbers,
professional identifiers). Ensure:

- NISS/SSIN values are treated as personal data under RGPD
- Data minimization: only request necessary eHealth attributes
- Keycloak stores eHealth attributes with appropriate access controls
- Data retention policy covers eHealth-sourced user attributes
- DPIA (Data Protection Impact Assessment) is updated to include eHealth data flows

### 9.3 Audit Requirements

Log all eHealth certificate operations:

- Certificate installation and updates
- mTLS connection attempts (success and failure)
- SAML authentication requests and responses
- User attribute provisioning from eHealth

VarunaPoC's existing audit logging infrastructure can be extended to capture these events.

---

## 10. Troubleshooting

### 10.1 Certificate Issues

**Problem:** "Certificate chain validation failed"
```
Solution: Ensure the full CA chain is imported:
1. Download root CA and intermediate CA from eHealth
2. Concatenate into chain file:
   cat ehealth-intermediate-ca.pem ehealth-root-ca.pem > ehealth-ca-chain.pem
3. Import into application truststore
```

**Problem:** "PKCS#12 keystore cannot be loaded"
```
Solution: Verify keystore integrity:
   openssl pkcs12 -info -in varunapoc-ehealth.p12
   Check password, key alias, and certificate chain presence
```

**Problem:** "SAML AuthnRequest signature validation failed at eHealth"
```
Solution:
1. Ensure Keycloak is signing with the eHealth certificate (not its default key)
2. Verify the signing key priority in Keycloak Realm Keys
3. Check that the SAML SP metadata published by Keycloak contains the correct certificate
```

### 10.2 Network Issues

**Problem:** Cannot reach eHealth endpoints
```
Solution:
1. Verify DNS resolution: nslookup services.ehealth.fgov.be
2. Verify firewall allows outbound HTTPS (port 443)
3. Check proxy configuration if applicable
4. Verify with: curl -v https://services.ehealth.fgov.be/IAM/Saml2/MSS
```

### 10.3 Support Contacts

| Contact | Channel | Purpose |
|---------|---------|---------|
| eHealth Service Desk | https://support.ehealth.fgov.be | Certificate issues, portal access |
| eHealth Technical Support | support@ehealth.fgov.be | Integration questions |
| CHU UCL Namur IT | Internal | Local infrastructure, network, Keycloak |

---

## 11. References

1. **Belgian eHealth Platform** -- Official portal.
   https://www.ehealth.fgov.be

2. **eHealth Certificate Documentation** -- Certificate management guide.
   https://www.ehealth.fgov.be/ehealthplatform/nl/ehealth-certificaten

3. **Belgian eID Middleware** -- Installation and usage.
   https://eid.belgium.be

4. **Keycloak SAML Identity Provider** -- Official documentation.
   https://www.keycloak.org/docs/latest/server_admin/#saml-v2-0-identity-providers

5. **OASIS SAML 2.0** -- Security Assertion Markup Language specification.
   http://docs.oasis-open.org/security/saml/v2.0/

6. **Belgian Crossroads Bank for Enterprises (KBO/BCE)**.
   https://kbopub.economie.fgov.be

7. **VarunaPoC Architecture** -- OIDC PKCE authentication design.
   See docs/architecture/SYSTEM_PATTERNS.md

---

*This document is for integration planning purposes only. Actual certificate application
requires coordination with CHU UCL Namur IT department and the Belgian eHealth Platform.
Configuration values shown are illustrative and must be adapted to the actual deployment.*

*Last updated: 2026-02-18*
