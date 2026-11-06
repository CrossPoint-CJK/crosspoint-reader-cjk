#!/usr/bin/env python3
"""Compile and run the reader character/word spacing rules."""

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

SOURCE = r'''
#include <cassert>
#include <cstdint>

#include "TextSpacing.h"

using TextSpacing::scaleWordSpace;
using TextSpacing::trackingBetween;

int main() {
  constexpr uint32_t HAN_A = 0x4E00, HAN_B = 0x4E8C, FULLWIDTH_COMMA = 0xFF0C;

  // Tracking goes between every adjacent glyph pair, including CJK punctuation, and may tighten.
  assert(trackingBetween(HAN_A, HAN_B, 2) == 2);
  assert(trackingBetween(HAN_B, FULLWIDTH_COMMA, 2) == 2);
  assert(trackingBetween('a', 'b', -1) == -1);
  assert(trackingBetween(HAN_A, HAN_B, 0) == 0);

  // Never before the first glyph, and never next to a space: word spacing owns those gaps.
  assert(trackingBetween(0, HAN_A, 2) == 0);
  for (const uint32_t space : {uint32_t{' '}, uint32_t{0xA0}, uint32_t{0x3000}}) {
    assert(trackingBetween(space, HAN_A, 2) == 0);
    assert(trackingBetween(HAN_A, space, 2) == 0);
  }

  // N glyphs drawn with tracking t are (N - 1) * t wider, so the measured line grows by the same amount.
  const uint32_t line[] = {HAN_A, HAN_B, HAN_A, FULLWIDTH_COMMA, HAN_B};
  int extra = 0;
  uint32_t prev = 0;
  for (const uint32_t cp : line) {
    extra += trackingBetween(prev, cp, 2);
    prev = cp;
  }
  assert(extra == 8);

  // Word spacing scales the space advance with nearest-pixel rounding; 100% is untouched.
  assert(scaleWordSpace(7, 100) == 7);
  assert(scaleWordSpace(7, 150) == 11);
  assert(scaleWordSpace(7, 50) == 4);
  assert(scaleWordSpace(8, 200) == 16);
  assert(scaleWordSpace(0, 175) == 0);
}
'''

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    source = tmp_path / "text_spacing_test.cpp"
    binary = tmp_path / "text_spacing_test"
    source.write_text(SOURCE.replace("#include <cstdint>", "#include <cstdint>\n#include <initializer_list>"))
    subprocess.run(
        ["c++", "-std=c++20", "-Wall", "-Wextra", "-Werror", "-Ilib/GfxRenderer", str(source), "-o", str(binary)],
        cwd=ROOT,
        check=True,
    )
    subprocess.run([str(binary)], check=True)

print("TEXT_SPACING_OK")
