#! /bin/sh

# This script compiles all the .py files in the current directory and its subdirectories
# into .mpy files in the build/ directory, ignoring main.py, and preserves folder structure.

# remove existing build directory if it exists
if [ -d "build" ]; then
    echo "Removing existing build directory..."
    rm -rf build
fi

# Compile .py files (excluding only ./main.py and anything in build/)
find . -path ./build -prune -o -type f -name "*.py" ! -path "./main.py" -print | while read src; do
    echo "Compiling $src"
    mpy-cross -march=armv6m "$src"
done

# Move .mpy files to build/, preserving directory structure (excluding build/)
find . -path ./build -prune -o -name "*.mpy" -print | while read src; do
    dest="build/${src#./}"
    mkdir -p "$(dirname "$dest")"
    echo "Moving $src -> $dest"
    mv "$src" "$dest"
done

# Copy all non-.py and non-.mpy files to build/, preserving directory structure (excluding build/)
find . -path ./build -prune -o -type f ! -name "*.py" ! -name "*.mpy" -print | while read src; do
    dest="build/${src#./}"
    mkdir -p "$(dirname "$dest")"
    echo "Copying $src -> $dest"
    cp "$src" "$dest"
done

# Clean up the .pyc files (excluding build/)
find . -path ./build -prune -o -name "*.pyc" -print | while read src; do
    echo "Removing $src"
    rm "$src"
done

cd build
mpremote connect $1 cp -r . :/
cd ..
mpremote connect $1 run main.py