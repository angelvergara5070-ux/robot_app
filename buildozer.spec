[app]
title = Robot Arena
package.name = robotarena
package.domain = org.robot
source.dir = .
source.include_exts = py
version = 0.1
requirements = python3,kivy==2.3.0,bleak,pyjnius,android
orientation = landscape
fullscreen = 1
android.api = 34
android.minapi = 26
android.archs = arm64-v8a
android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_SCAN, BLUETOOTH_CONNECT, ACCESS_FINE_LOCATION
p4a.branch = develop

[buildozer]
log_level = 2
