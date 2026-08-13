# Apps for the AppStore

This repository is used by the AppStore app to [list apps](app_index.json).

## App landing pages (QR deep links)

Every app has a landing page at `https://apps.micropythonos.com/app/<fullname>`
— the target of its QR deep link. A MicroPythonOS device scanning that QR
opens the App Store on the app; a phone lands on the page, which shows the
app's info, the QR code itself, and a download link.

The pages under [app/](app/) are generated. After changing
[app_index.json](app_index.json), regenerate them with:

```bash
pip install segno   # once
python3 generate_app_pages.py
```
