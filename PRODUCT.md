# Product

<!-- impeccable:product-schema 1 -->

## Platform

desktop

## Users

People converting collections of audio files to MP3, primarily through the graphical interface.

## Product Purpose

m4a-2-mp3 converts audio files and folders to MP3 through a Qt desktop application or command-line interface.

## Positioning

A local batch converter that uses FFmpeg and preserves audio metadata, including embedded cover art where supported by the input.

## Operating Context

The GUI accepts dropped or selected audio files and folders, scans folders recursively, and displays conversion results. The CLI accepts a source directory. FFmpeg must be installed and available on PATH.

## Capabilities and Constraints

Supported audio inputs are M4A, WAV, AIFF, and AIF. Conversion quality and parallelism are configurable. Output can be placed beside the sources or in an artist/album folder structure. Existing MP3s are overwritten by default; source deletion is optional. The GUI supports French, English, and Danish. The project requires Python 3.9+ and is MIT-licensed. The existing automated binary build publishes a Linux x86_64 AppImage on version-tag releases; no ready-to-download Windows or macOS binaries are documented.

## Evidence on Hand

The repository contains the application source, README usage instructions, MIT license, and an AppImage GitHub Actions workflow. No verified testimonials, customer claims, benchmark results, prices, or application screenshots have been supplied. The landing page may use a clearly identified placeholder illustration until the user supplies a screenshot.

## Product Principles

- Convert supported files locally with FFmpeg.
- Keep batch conversion and visible per-file results accessible through the GUI.
- Preserve available metadata during conversion.
- Keep source deletion optional and output behavior configurable.
