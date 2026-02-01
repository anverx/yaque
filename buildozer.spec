[app]

# App name
title = Yaque

# Package name
package.name = yaque

# Package domain (used for Android package identifier)
package.domain = com.yaque

# Source code directory
source.dir = src

# Source files to include
source.include_exts = py,png,jpg,kv,atlas,json,ttf

# Application versioning
version = 0.1

# Application requirements
# Note: Cython<3 is required for pyjnius compatibility
requirements = python3,kivy,pillow,qrcode,pyjnius,cython==0.29.36

# Supported orientations (portrait, landscape, all)
orientation = portrait

# Android fullscreen mode
fullscreen = 1

# Android permissions
android.permissions = INTERNET

# Android API levels
android.minapi = 21
android.api = 33
android.ndk = 25b

# Android architecture
android.archs = arm64-v8a, armeabi-v7a

# Use stable python-for-android
p4a.branch = master

# Android features
android.allow_backup = True

# Custom URL scheme - intent filter for yaque:// links
android.manifest.intent_filters = intent_filters.xml

# Presplash color
android.presplash_color = #F2F2F2

# Debug keystore (for consistent signing across builds)
# On CI, this file is restored from secrets; locally you can create your own
android.debug_keystore = %(source.dir)s/../debug.keystore
android.debug_keystore_alias = androiddebugkey
android.debug_keystore_passwd = android
android.debug_keyalias_passwd = android

# App icon (place icon.png in source directory)
icon.filename = %(source.dir)s/assets/images/icon.png

# Presplash image
# presplash.filename = %(source.dir)s/assets/images/splashscreen.jpg

[buildozer]

# Build log level (0 = error, 1 = info, 2 = debug)
log_level = 2

# Build warnings
warn_on_root = 1
