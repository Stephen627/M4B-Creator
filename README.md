# Audiobook MP3 to M4B Converter

This tool converts a directory of sequentially ordered MP3 files into a single `.m4b` audiobook file. It automatically extracts chapter names from the filenames and embeds them into the resulting audiobook. It also supports embedding a cover image.

## Prerequisites

- Python 3.6+
- `ffmpeg` and `ffprobe` installed and available in your system's PATH.

## File Naming Convention

Your MP3 files must be named in the following format:
`{order} {name}.mp3`

Where `{order}` is a number determining the sequence (e.g., 01, 02) and `{name}` is the title of the chapter.

Example:
- `01 The Beginning.mp3`
- `02 The Journey.mp3`
- `03 The End.mp3`

If a file named `cover.jpg` is present in the directory, it will automatically be embedded as the audiobook's cover art.

## Usage

Run the script from the command line, providing the path to the directory containing your MP3 files:

```bash
python convert_to_m4b.py /path/to/your/audiobook/directory
```

The script will:
1. Scan the directory and parse the files.
2. Present you with the calculated order and chapter names.
3. Ask for your confirmation before proceeding.
4. Generate an `.m4b` file in the provided directory.

### Output Filename

The output filename is determined by:
1. A `name.txt` file in the audiobook directory (if present, the first line is used as the filename).
2. If `name.txt` does not exist, the directory name is used.

For example, if the audiobook directory contains a `name.txt` file with the text `My Book`, the output file will be `My Book.m4b`.

## Docker

You can use Docker to run the converter without having to manually install Python and FFmpeg on your machine.

### Build the Image

```bash
docker build -t audiobook-converter .
```

### Run the Image

To convert a directory of MP3 files, mount the directory to the container and run it:

```bash
docker run -it --rm \
  -v "/path/to/your/audiobook/directory:/audiobook" \
  audiobook-converter /audiobook
```

**Note:**
- Replace `/path/to/your/audiobook/directory` with the actual path on your host machine.
- The resulting `output.m4b` file will be created in the same directory on your host machine.
- You can add the `-y` flag at the end of the command to skip the confirmation prompt:
  ```bash
  docker run -it --rm -v "/path/to/your/audiobook/directory:/audiobook" audiobook-converter /audiobook -y
  ```
