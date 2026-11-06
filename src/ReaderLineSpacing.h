#pragma once

#include <cstdint>

namespace ReaderLineSpacing {

// Where the reader line height comes from. External .bin and SD card fonts carry their own line height
// (an external .bin's is its glyph cell, with no leading), so they need a wider scale than the built-in
// families, whose line heights already include leading.
enum class Source : uint8_t { FontOwned, BuiltInSerif, BuiltInSans };

// Indexed by CrossPointSettings::LINE_COMPRESSION (TIGHT, NORMAL, WIDE, EXTRA_WIDE).
constexpr uint8_t LEVEL_COUNT = 4;
constexpr uint8_t NORMAL_LEVEL = 1;

constexpr float compression(const Source source, const uint8_t lineSpacing) {
  constexpr float FONT_OWNED[LEVEL_COUNT] = {0.95f, 1.0f, 1.3f, 1.6f};
  constexpr float BUILT_IN_SERIF[LEVEL_COUNT] = {0.95f, 1.0f, 1.1f, 1.2f};
  constexpr float BUILT_IN_SANS[LEVEL_COUNT] = {0.90f, 0.95f, 1.0f, 1.05f};
  const uint8_t level = lineSpacing < LEVEL_COUNT ? lineSpacing : NORMAL_LEVEL;
  switch (source) {
    case Source::FontOwned:
      return FONT_OWNED[level];
    case Source::BuiltInSans:
      return BUILT_IN_SANS[level];
    case Source::BuiltInSerif:
    default:
      return BUILT_IN_SERIF[level];
  }
}

}  // namespace ReaderLineSpacing
