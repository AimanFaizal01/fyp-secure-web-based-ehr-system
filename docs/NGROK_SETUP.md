# Dynamic HTTPS Tunneling with ngrok
 
 > **[ Project Home ](../README.md)** &nbsp;&nbsp; | &nbsp;&nbsp; **[ Implementation Guide ](IMPLEMENTATION_LOG.md)** &nbsp;&nbsp; | &nbsp;&nbsp; **[ Pentest Guide ](PENTEST_GUIDE.md)**

---

Use this guide to generate a secure, public **HTTPS** URL for your local Hospital EHR environment. This permits external stakeholders or presentation screens to access your live portal securely without deploying to the cloud.

## 1. Installation (Mac OS)

The most efficient deployment vector uses Homebrew. Execute the following in your Terminal:

```bash
brew install ngrok/ngrok/ngrok
```

*(Alternative: Download the binary directly from [ngrok.com](https://ngrok.com) and move it to your `/usr/local/bin`).*

---

## 2. Authenticate Daemon

A free ngrok account is required to provision modern HTTPS headers. 
1. Sign up/Log in to the [ngrok Dashboard](https://dashboard.ngrok.com).
2. Copy your Authtoken from the Setup page.
3. Run the following authentication command:

```bash
ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
```

---

## 3. Execute Tunnel Initialization

Once your Django server is running locally (`./venv/bin/python3 manage.py runserver` on port 8000), open a second terminal window and fire the HTTP forwarding daemon:

```bash
ngrok http 8000
```

### Expected Console Output:
```text
ngrok by @inconshreveable                                     (Ctrl+C to quit)
                                                                              
Session Status                online                                          
Account                       Your Name (Plan: Free)                          
Version                       3.X.X                                           
Region                        United States (us)                              
Forwarding                    https://abcd-123-45-678.ngrok-free.app -> http://localhost:8000
```

---

## 4. Presentation Validation

1. **Copy the HTTPS Link:** Locate the `Forwarding` line in your ngrok output and copy the `https://....ngrok-free.app` address.
2. **Send to Stakeholder:** This link can now be accessed by your friend or external evaluators anywhere in the world.
3. **System Whitelisting:** The system settings have already been customized to automatically permit and whitelist `.ngrok.app` and `.ngrok-free.app` headers, eliminating generic `400 Bad Request` blocking errors.

---
