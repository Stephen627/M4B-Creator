import os
import re
import sys
import argparse
import subprocess

def get_duration(file_path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Error getting duration for {file_path}:\n{result.stderr}")
        sys.exit(1)
    return float(result.stdout.strip())

def format_duration(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"

def main():
    parser = argparse.ArgumentParser(description="Convert directory of MP3s to a single M4B file.")
    parser.add_argument("directory", help="Path to the directory containing MP3 files")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    target_dir = os.path.abspath(args.directory)
    if not os.path.isdir(target_dir):
        print(f"Error: Directory '{target_dir}' does not exist.")
        sys.exit(1)

    # Find and parse MP3 files
    pattern = re.compile(r'^(\d+)\s+(.+)\.mp3$', re.IGNORECASE)
    files = []
    for f in os.listdir(target_dir):
        if not f.lower().endswith('.mp3'):
            continue
        match = pattern.match(f)
        if match:
            order = int(match.group(1))
            name = match.group(2)
            files.append({'filename': f, 'order': order, 'name': name})
    
    if not files:
        print("No matching MP3 files found in the directory.")
        print("Expected format: '{order} {name}.mp3'")
        sys.exit(1)

    # Sort files by order
    files.sort(key=lambda x: x['order'])

    # Get durations for display
    for f in files:
        filepath = os.path.join(target_dir, f['filename'])
        f['duration'] = get_duration(filepath)

    # Present order to user
    print(f"\nFound {len(files)} chapters:")
    print("-" * 70)
    for f in files:
        runtime = format_duration(f['duration'])
        print(f"Order: {f['order']:02d} | Chapter Name: {f['name']} | Runtime: {runtime} | File: {f['filename']}")
    print("-" * 70)

    # Ask for confirmation
    if not args.yes:
        confirm = input("\nProceed with generating M4B? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Operation cancelled.")
            sys.exit(0)

    # Prepare inputs.txt for ffmpeg concat
    inputs_txt_path = os.path.join(target_dir, 'inputs.txt')
    metadata_txt_path = os.path.join(target_dir, 'metadata.txt')
    
    # Determine output filename: prefer name.txt, fall back to directory name
    name_txt_path = os.path.join(target_dir, 'name.txt')
    if os.path.isfile(name_txt_path):
        with open(name_txt_path, 'r', encoding='utf-8') as f:
            book_name = f.read().strip()
        if not book_name:
            book_name = os.path.basename(target_dir.rstrip(os.sep))
    else:
        book_name = os.path.basename(target_dir.rstrip(os.sep))
    output_m4b_filename = f"{book_name}.m4b"
    output_m4b_path = os.path.join(target_dir, output_m4b_filename)

    try:
        with open(inputs_txt_path, 'w', encoding='utf-8') as f_in:
            for f in files:
                filepath = os.path.join(target_dir, f['filename'])
                # Escape single quotes for ffmpeg concat file
                safe_filepath = filepath.replace("'", "'\\''")
                f_in.write(f"file '{safe_filepath}'\n")

        # Prepare metadata.txt
        with open(metadata_txt_path, 'w', encoding='utf-8') as f_meta:
            f_meta.write(";FFMETADATA1\n")
            f_meta.write(f"title={os.path.basename(target_dir)}\n\n")

            current_time_ms = 0
            for f in files:
                filepath = os.path.join(target_dir, f['filename'])
                duration_sec = get_duration(filepath)
                duration_ms = int(duration_sec * 1000)
                
                start_time = current_time_ms
                end_time = current_time_ms + duration_ms

                f_meta.write("[CHAPTER]\n")
                f_meta.write("TIMEBASE=1/1000\n")
                f_meta.write(f"START={start_time}\n")
                f_meta.write(f"END={end_time}\n")
                f_meta.write(f"title={f['name']}\n\n")
                
                current_time_ms = end_time

        # Check for cover.jpg
        cover_path = os.path.join(target_dir, 'cover.jpg')
        has_cover = os.path.isfile(cover_path)

        # Construct ffmpeg command
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", inputs_txt_path,
            "-i", metadata_txt_path
        ]

        if has_cover:
            ffmpeg_cmd.extend(["-i", cover_path])

        ffmpeg_cmd.extend([
            "-map_metadata", "1",
            "-map", "0:a"
        ])

        if has_cover:
            ffmpeg_cmd.extend([
                "-map", "2:v",
                "-c:v", "copy",
                "-disposition:v:0", "attached_pic"
            ])

        ffmpeg_cmd.extend([
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_m4b_path
        ])

        print("\nStarting conversion. This may take a while...")
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"\nSuccess! M4B created at: {output_m4b_path}")

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg command failed with error: {e}")
    finally:
        # Clean up temporary files
        if os.path.exists(inputs_txt_path):
            os.remove(inputs_txt_path)
        if os.path.exists(metadata_txt_path):
            os.remove(metadata_txt_path)

if __name__ == "__main__":
    main()