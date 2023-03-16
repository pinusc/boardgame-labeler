#!/usr/bin/env bash
VERSION="$(poetry version --short)"
PLATFORM="$(python -c 'import sys; print(sys.platform)')"
NAME="boardgame-labeler-$VERSION-$PLATFORM"
echo "$PWD"
pyinstaller --onefile \
    --specpath "pyinstaller" \
    --workpath "pyinstaller/build-$PLATFORM" \
    --distpath "pyinstaller/dist" \
    --add-data="$PWD/res/*:res" \
    --hidden-import pkg_resources \
    "$@" \
    -n "$NAME" main.py
