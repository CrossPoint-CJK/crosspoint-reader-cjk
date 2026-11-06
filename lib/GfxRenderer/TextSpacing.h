#pragma once

#include <cstdint>

// Reader character and word spacing rules shared by layout (ParsedText) and drawing (GfxRenderer), so measured
// and rendered positions stay identical.
namespace TextSpacing {

constexpr bool isSpace(const uint32_t cp) { return cp == ' ' || cp == 0xA0 || cp == 0x3000; }

// Extra pixels between two adjacent glyphs. Whitespace keeps its own advance (word spacing scales it), so
// tracking is never added next to a space or before the first glyph.
constexpr int trackingBetween(const uint32_t leftCp, const uint32_t rightCp, const int8_t tracking) {
  return leftCp == 0 || isSpace(leftCp) || isSpace(rightCp) ? 0 : tracking;
}

// Scales a space advance by the word spacing percentage, rounding to the nearest pixel.
constexpr int scaleWordSpace(const int advance, const uint8_t wordSpacingPercent) {
  return wordSpacingPercent == 100 ? advance : (advance * wordSpacingPercent + 50) / 100;
}

}  // namespace TextSpacing
