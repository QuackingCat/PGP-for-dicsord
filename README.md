# PGP-for-Discord

![Discord PGP Encryption/Decryption](https://img.shields.io/badge/Status-In%20Progress-blue)


Automatically encrypts and decrypts Discord messages using PGP and MITMProxy.

## General Description

This project acts as a proxy that intercepts all HTTP and WebSocket communication related to sent and recieved messages in Discord:

* **Intercept outbound Discord messages** and encrypt them with PGP using the assigned public keys (per channel).
* **Intercept inbound Discord messages** and decrypt them with PGP using your private keys (protected keys aren't supported yet).

All PGP keys (both private and public) are managed and stored in a local file named `keys.json`.

### `keys.json` Format

The `keys.json` file uses the following structure to organize PGP keys:

```json
{
  "private": [
    {
      "name": "MyPersonalKey",
      "key": "-----BEGIN PGP PRIVATE KEY BLOCK-----\n...\n-----END PGP PRIVATE KEY BLOCK-----"
    },
    {
      "name": "AnotherPrivate",
      "key": "-----BEGIN PGP PRIVATE KEY BLOCK-----\n...\n-----END PGP PRIVATE KEY BLOCK-----"
    }
  ],
  "public": {
    "123456789012345678": [  // Example: Discord Channel ID or User ID for public keys
      {
        "name": "FriendA'sKey",
        "key": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n...\n-----END PGP PUBLIC KEY BLOCK-----"
      },
      {
        "name": "FriendB'sKey",
        "key": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n...\n-----END PGP PUBLIC KEY BLOCK-----"
      }
    ],
    "987654321098765432": [
      {
        "name": "GroupChatKey",
        "key": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n...\n-----END PGP PUBLIC KEY BLOCK-----"
      }
    ]
  }
}
```
* **private**: An array of objects, each containing a name and the ASCII-armored key string for your private PGP keys.
* **public**: An object where keys are Discord Channel IDs or User IDs (as strings). Each value is an array of objects, similar to private, containing name and key for public PGP keys associated with that channel/user.

Updates to this file takes effect immediately in the MITMProxy script (a refresh may be needed in discord to apply new keys for already cached messages).

## Dependencies
Before running the project, ensure you have the following installed:
1. **Mitmproxy**: The core proxy framework.
  ```bash
  pip install mitmproxy
  ```
2. **PGPY**: A Python library for PGP operations.
  ```bash
  pip install pgpy
  ```
3. **Tkinter**: (Usually comes with Python) Used for the graphical key manager.

## Getting Started

### Full Application (with Key Manager GUI)

To start the full application, including the Tkinter-based key manager GUI:
```bash
python main.py
```

### MITM Proxy Script Only (No GUI)
If you only want to run the MITM proxy functionality without the Tkinter GUI (and manage keys.json manually), use:
```bash
mitmproxy -s dishook.py
```
