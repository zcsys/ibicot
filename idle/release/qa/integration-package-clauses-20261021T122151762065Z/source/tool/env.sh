#!/usr/bin/env bash
# Source from the wrappers; all writable SDK/cache state stays inside this project.
TIDEGLASS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export TIDEGLASS_ROOT
export JAVA_HOME="$TIDEGLASS_ROOT/.tooling/java/current/Contents/Home"
export ANDROID_HOME="$TIDEGLASS_ROOT/.tooling/android-sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export ANDROID_AVD_HOME="$TIDEGLASS_ROOT/.tooling/android-avd"
export GRADLE_USER_HOME="$TIDEGLASS_ROOT/.tooling/gradle"
export PUB_CACHE="$TIDEGLASS_ROOT/.tooling/pub-cache"
export DART_SUPPRESS_ANALYTICS=true
export FLUTTER_SUPPRESS_ANALYTICS=true
export CI=true
export PATH="$TIDEGLASS_ROOT/.tooling/flutter/bin:$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
