[app]
title = Robot Arena
package.name = robotarena
package.domain = org.robot
source.dir = .
source.include_exts = py
version = 0.1
requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.1,bleak,pyjnius,android
orientation = landscape
fullscreen = 1
android.api = 35
android.ndk = 25b
android.minapi = 26
android.archs = arm64-v8a
android.accept_sdk_license = True
android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_SCAN, BLUETOOTH_CONNECT, ACCESS_FINE_LOCATION
#p4a.branch = develop

[buildozer]
log_level = 2
