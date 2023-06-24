import logging
from datetime import tzinfo
from os import utime
from pathlib import Path

from dateutil.tz import tzlocal

from SnapchatMemoriesMetadataAdder._ffmpeg import ffmpeg_add_metadata
from SnapchatMemoriesMetadataAdder._vips import vips_add_metadata
from SnapchatMemoriesMetadataAdder.metadata import MediaType, Metadata


def _add_suffix(type: MediaType, path: Path) -> Path:
    """Add the proper suffix for the given MediaType."""
    match type:
        case MediaType.Image:
            return path.with_suffix(".jpg")
        case MediaType.Video:
            return path.with_suffix(".mp4")


def add_metadata(memory_folder: Path,
                 output_folder: Path,
                 metadata: Metadata,
                 tz: tzinfo = tzlocal()):
    """Given an input/output folder, the metadata for the memory, and
    optionally a timezone, add the overlay and timezone to the memory and write
    the file to the output folder."""

    # First, get/validate paths, then prepare for merging
    root = memory_folder / metadata.mid

    base = _add_suffix(metadata.type, root.with_name(root.name + "-main"))

    logging.debug(f"base image found: {base}")
    assert base.exists()

    # Note: all overlays are pngs
    overlay = overlay if (
        overlay :=
        root.with_name(root.name +
                       "-overlay").with_suffix(".png")).exists() else None

    if overlay:
        logging.debug(f"overlay found: {overlay}")
    else:
        logging.debug("No overlay for this image!")

    local_time = metadata.date.astimezone(tz)

    output = _add_suffix(
        metadata.type,
        output_folder / (local_time.strftime('%Y-%m-%d_%H:%M_') + root.name))
    logging.debug(f"output file: {output}")
    assert not output.exists()

    # Merge if there's an overlay!
    match metadata.type:
        case MediaType.Image:
            vips_add_metadata(base, overlay, metadata, tz, output)
        case MediaType.Video:
            ffmpeg_add_metadata(base, overlay, metadata, tz, output)

    # Set the file creation/modification time to the original time!
    utime(output, times=(local_time.timestamp(), local_time.timestamp()))
