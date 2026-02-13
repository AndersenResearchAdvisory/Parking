#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v sips >/dev/null 2>&1; then
  echo "Error: sips is not available on this system."
  exit 1
fi

if [ "${1:-}" = "" ]; then
  echo "Usage: ./generate-icons.sh /absolute/or/relative/path/to/source.png"
  echo "Example: ./generate-icons.sh ./app-icon-source.png"
  exit 1
fi

SOURCE_INPUT="$1"
if [ -f "$SOURCE_INPUT" ]; then
  SOURCE_PATH="$SOURCE_INPUT"
elif [ -f "$PROJECT_DIR/$SOURCE_INPUT" ]; then
  SOURCE_PATH="$PROJECT_DIR/$SOURCE_INPUT"
else
  echo "Error: source PNG not found: $SOURCE_INPUT"
  exit 1
fi

if ! sips -g format "$SOURCE_PATH" 2>/dev/null | grep -qi "png"; then
  echo "Error: source file must be a PNG."
  exit 1
fi

create_icon() {
  local size="$1"
  local out_name="$2"
  local out_path="$PROJECT_DIR/$out_name"

  cp "$SOURCE_PATH" "$out_path"
  sips -z "$size" "$size" "$out_path" >/dev/null
  echo "Created $out_name (${size}x${size})"
}

create_icon 180 "apple-touch-icon.png"
create_icon 192 "icon-192.png"
create_icon 512 "icon-512.png"

echo "Done. Icons were written to:"
echo "  $PROJECT_DIR/apple-touch-icon.png"
echo "  $PROJECT_DIR/icon-192.png"
echo "  $PROJECT_DIR/icon-512.png"
