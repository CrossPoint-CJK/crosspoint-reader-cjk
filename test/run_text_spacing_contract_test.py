#!/usr/bin/env python3
"""Ensure reader character/word spacing reaches every measure, draw, layout gap and cache path."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
failures = []


def read(path):
    return (ROOT / path).read_text()


def require(condition, message):
    if not condition:
        failures.append(message)


def function_body(source, signature):
    start = source.find(signature)
    if start < 0:
        return ""
    end = source.find("\n}\n", start)
    return source[start:end]


gfx = read("lib/GfxRenderer/GfxRenderer.cpp")
measure = function_body(gfx, "int GfxRenderer::measureTextAdvance(")
draw = function_body(gfx, "bool GfxRenderer::drawText(")
kerning = function_body(gfx, "int GfxRenderer::getKerning(")
# Measurement has three loops (SD advance table, SD metrics, generic); drawing has one. Each must add the same
# tracking at the same step, or layout positions drift from the drawn glyphs.
require(measure.count("TextSpacing::trackingBetween(") == 3, "measureTextAdvance must track in all three loops")
require(draw.count("TextSpacing::trackingBetween(prevCp, cp, tracking)") == 1, "drawText must track glyph pairs")
require(kerning.count("return trackingPx;") == 3 and "+ trackingPx;" in kerning,
        "getKerning must add tracking on every return path, including fallback glyphs")
require("measureTextAdvance(resolvedFontId, fontIt->second, renderedText, style, tracking)" in gfx,
        "getTextAdvanceX must forward tracking")

layout = read("lib/Epub/Epub/ParsedText.cpp")
require(not re.search(r"^\s+(gap|spacing) = 0;", layout, re.M), "a no-space break gap ignores character spacing")
require(not re.search(r"nextNoSpace\s*\?\s*0\b", layout), "a no-space break position ignores character spacing")
space_calls = len(re.findall(r"renderer\.getSpaceAdvance\(", layout))
require(space_calls > 0 and space_calls == len(re.findall(r"scaleWordSpace\(\s*renderer\.getSpaceAdvance\(", layout)),
        "every inter-word space must be scaled by word spacing")
for call in re.findall(r"renderer\.getKerning\((.*?)\);", layout, re.S):
    require("blockStyle.characterSpacing" in call, f"getKerning without character spacing: {call.split(',')[0]}")
for call in re.findall(r"measureWordWidth\((renderer.*?)\);", layout, re.S):
    require("wordSpacingPercent" in call, "measureWordWidth call without spacing arguments")

block = read("lib/Epub/Epub/blocks/TextBlock.cpp")
require("writePod(file, blockStyle.characterSpacing)" in block and "readPod(file, blockStyle.characterSpacing)" in block,
        "TextBlock must persist character spacing")
require(block.count("cancellation ? cancellation->context : nullptr, tracking)") == 3,
        "every TextBlock drawText call must pass tracking")

section = read("lib/Epub/Epub/Section.cpp")
version = int(re.search(r"SECTION_FILE_VERSION = (\d+);", section).group(1))
require(version >= 36, "section cache version must change with the new header fields")
for field in ("characterSpacing", "wordSpacingPercent"):
    require(f"writePod(file, spec.{field})" in section, f"section header must write {field}")
    file_field = "file" + field[0].upper() + field[1:]
    require(f"spec.{field} != {file_field}" in section, f"section cache must be invalidated by {field}")
require("parser->setTextSpacing(spec.characterSpacing, spec.wordSpacingPercent)" in section,
        "section build must hand spacing to the parser")

if failures:
    print("\n".join(failures), file=sys.stderr)
    raise SystemExit(1)
print("TEXT_SPACING_CONTRACT_OK")
