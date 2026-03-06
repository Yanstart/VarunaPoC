#!/bin/bash
# Pre-commit hook: verify docs/implementation/info.md references all numbered docs
DOCS_DIR="docs/implementation"

if [ ! -f "$DOCS_DIR/info.md" ]; then
  echo "WARNING: $DOCS_DIR/info.md missing"
  exit 0
fi

MISSING=0
for f in "$DOCS_DIR"/[0-9]*.md; do
  [ -f "$f" ] || continue
  NUM=$(basename "$f" .md | grep -oP '^\d+')
  if ! grep -q "$NUM" "$DOCS_DIR/info.md"; then
    echo "ERROR: $f not referenced in $DOCS_DIR/info.md"
    MISSING=1
  fi
done

if [ "$MISSING" -eq 1 ]; then
  echo "Update docs/implementation/info.md to reference all implementation docs"
  exit 1
fi
