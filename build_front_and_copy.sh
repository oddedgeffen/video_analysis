#!/usr/bin/env bash
set -euo pipefail

### CONFIG – tweak these if your folders live elsewhere ###
FRONTEND_DIR="frontend"
BUILD_DIR="$FRONTEND_DIR/build"
STATIC_DIR="static"
TEMPLATES_DIR="templates"

JS_TARGET="$STATIC_DIR/js"
CSS_TARGET="$STATIC_DIR/css"
INDEX_TARGET="$TEMPLATES_DIR/index.html"
##########################################################

echo "🔨 Building React frontend…"
cd "$FRONTEND_DIR"
npm install --silent
npm run build
cd ..

echo "🧹 Cleaning old assets…"
rm -rf "$JS_TARGET"/* 
rm -rf "$CSS_TARGET"/*
rm -f  "$INDEX_TARGET"

echo "📁 Ensuring target dirs exist…"
mkdir -p "$JS_TARGET" "$CSS_TARGET" "$TEMPLATES_DIR"

echo "🚚 Copying new build files…"
cp -r "$BUILD_DIR/static/js/"*  "$JS_TARGET/"
cp -r "$BUILD_DIR/static/css/"* "$CSS_TARGET/"
cp     "$BUILD_DIR/index.html"  "$INDEX_TARGET"

echo "🔧 Adding Django template tags..."
# First, let's format the HTML file
sed -i 's/></>\n</g' "$INDEX_TARGET"
sed -i 's/^/    /' "$INDEX_TARGET"
sed -i 's/    <\/html>/\n<\/html>/' "$INDEX_TARGET"

# Add {% load static %} after <html> tag
sed -i '/<html/a {% load static %}' "$INDEX_TARGET"

# Replace static file references with Django template tags
sed -i 's|src="/static/js/\([^"]*\)"|src="{% static '\''js/\1'\'' %}"|g' "$INDEX_TARGET"
sed -i 's|href="/static/css/\([^"]*\)"|href="{% static '\''css/\1'\'' %}"|g' "$INDEX_TARGET"
sed -i 's|href="/manifest.json"|href="{% static '\''manifest.json'\'' %}"|g' "$INDEX_TARGET"
sed -i 's|href="/favicon.ico"|href="{% static '\''favicon.ico'\'' %}"|g' "$INDEX_TARGET"
sed -i 's|href="/logo192.png"|href="{% static '\''logo192.png'\'' %}"|g' "$INDEX_TARGET"
sed -i 's|href="/logo512.png"|href="{% static '\''logo512.png'\'' %}"|g' "$INDEX_TARGET"

echo "✅ Frontend build & copy complete."
