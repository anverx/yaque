# Google Play Release Plan

## 1. Build a Release AAB
- Google Play requires **AAB** (Android App Bundle), not APK
- In `buildozer.spec`: set `android.release_artifact = aab`
- Sign with a **dedicated release keystore** (not the debug one) — keep it safe forever, losing it means you can never update the app
- `buildozer android release`

## 2. Google Play Developer Account
- One-time **$25 registration fee**
- Requires a Google account
- Sign up at [play.google.com/console](https://play.google.com/console)

## 3. Store Listing
- App name, short & full description
- **Screenshots**: at least 2 phone screenshots (min 320px, max 3840px)
- **Feature graphic**: 1024x500 banner
- **App icon**: 512x512 high-res icon
- Privacy policy URL (required even if you collect nothing)
- Category (likely "Puzzle")

## 4. Content & Compliance
- **Content rating questionnaire** (in-console, takes 5 min)
- **Target audience & content** declaration (is it for kids?)
- **Data safety form** — declare what data you collect/share (app is local-only, so minimal)
- Ads declaration (none)

## 5. Release Process
- Upload the signed AAB
- Choose release track: **internal testing** → **closed testing** → **open testing** → **production**
- Google recommends starting with internal/closed testing first
- Review typically takes a few hours to a few days for first submission

## Main Hurdles
- **AAB format** — make sure buildozer produces it correctly
- **Privacy policy** — needs to be hosted at a public URL
- **Screenshots** — need to look polished
- **64-bit requirement** — buildozer needs `android.archs = arm64-v8a` (or both `armeabi-v7a, arm64-v8a`)
