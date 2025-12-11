# Distro AI PoC - Audio Metadata Tool

## Overview
This tool helps prepare audio files for distribution by enforcing a strict workflow: you must upload cover art before you can edit any metadata. This prevents "faceless" audio uploads.

## File Structure
* **index.html**: The main interface.
* **CoverArtWizard.js**: The logic that listens for image uploads and unlocks the form.
* **app.js**: Main application initialization.
* **distrov2.py / agent_api.py**: Backend python scripts for processing.

## How to Run
1. Open `index.html` in your web browser.
2. Upload a `.jpg` or `.png` image in the "Cover Art" section.
3. Once the image is detected, the metadata fields (Artist, Title) will automatically unlock.
4. Enter your info and click Process.
