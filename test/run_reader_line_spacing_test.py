#!/usr/bin/env python3
"""Compile and run the reader line-spacing scale contract."""

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

SOURCE = r'''
#include <cassert>
#include <cmath>
#include <cstdint>
#include <initializer_list>

#include "ReaderLineSpacing.h"

using ReaderLineSpacing::Source;
using ReaderLineSpacing::compression;

namespace {
constexpr uint8_t TIGHT = 0, NORMAL = 1, WIDE = 2, EXTRA_WIDE = 3;

// Mirrors GfxRenderer::getLineHeight(fontId, compression) rounding.
int linePitch(const int lineHeight, const float scale) { return static_cast<int>(lineHeight * scale + 0.5f); }
}  // namespace

int main() {
  // A 33x39 external .bin reports its 39 px glyph cell as line height, so every level above Normal must
  // open a visible gap: Wide was 1.1x (4 px) before; it is now 12 px and Extra Wide 23 px.
  assert(linePitch(39, compression(Source::FontOwned, NORMAL)) == 39);
  assert(linePitch(39, compression(Source::FontOwned, WIDE)) - 39 == 12);
  assert(linePitch(39, compression(Source::FontOwned, EXTRA_WIDE)) - 39 == 23);

  // Built-in families keep their existing Tight/Normal/Wide values and gain Extra Wide.
  assert(compression(Source::BuiltInSerif, TIGHT) == 0.95f);
  assert(compression(Source::BuiltInSerif, WIDE) == 1.1f);
  assert(compression(Source::BuiltInSerif, EXTRA_WIDE) == 1.2f);
  assert(compression(Source::BuiltInSans, NORMAL) == 0.95f);
  assert(compression(Source::BuiltInSans, WIDE) == 1.0f);
  assert(compression(Source::BuiltInSans, EXTRA_WIDE) == 1.05f);

  // Every scale grows with the level.
  for (const Source source : {Source::FontOwned, Source::BuiltInSerif, Source::BuiltInSans}) {
    for (uint8_t level = TIGHT; level < EXTRA_WIDE; ++level) {
      assert(compression(source, level) < compression(source, level + 1));
    }
  }

  // Corrupt persisted values fall back to Normal instead of reading past the table.
  assert(compression(Source::FontOwned, 4) == compression(Source::FontOwned, NORMAL));
  assert(compression(Source::BuiltInSans, 255) == compression(Source::BuiltInSans, NORMAL));
}
'''

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    source = tmp_path / "reader_line_spacing_test.cpp"
    binary = tmp_path / "reader_line_spacing_test"
    source.write_text(SOURCE)
    subprocess.run(
        ["c++", "-std=c++20", "-Wall", "-Wextra", "-Werror", "-Isrc", str(source), "-o", str(binary)],
        cwd=ROOT,
        check=True,
    )
    subprocess.run([str(binary)], check=True)

print("READER_LINE_SPACING_OK")
