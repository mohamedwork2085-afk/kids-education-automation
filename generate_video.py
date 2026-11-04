import shutil, subprocess
from pathlib import Path

from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips, vfx

OUTPUT = Path("output")
AUDIO = OUTPUT / "narration.mp3"
TEXT = OUTPUT / "narration.txt"
VIDEO = OUTPUT / "final_video.mp4"
COUNT = 8


def main():
    if not AUDIO.exists() or not TEXT.exists():
        raise FileNotFoundError("Narration text/audio missing")

    blender = shutil.which("blender")
    if not blender:
        raise RuntimeError("Blender executable not found")

    scenes = OUTPUT / "scenes"
    scenes.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            blender, "-b", "--python", "blender_scene.py", "--",
            "--output", str(scenes.resolve()), "--count", str(COUNT)
        ],
        check=True
    )

    # Check all Blender outputs before MoviePy tries to open them.
    scene_paths = [
        scenes / "scene_{:02d}.mp4".format(i + 1)
        for i in range(COUNT)
    ]
    missing = [str(path) for path in scene_paths if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError(
            "Blender did not create all expected scene videos. Missing or empty: "
            + ", ".join(missing)
        )

    words = TEXT.read_text(encoding="utf-8").split()
    if len(words) < COUNT:
        raise RuntimeError("Narration too short")

    weights = [
        max(1, len(words[(i * len(words)) // COUNT:((i + 1) * len(words)) // COUNT]))
        for i in range(COUNT)
    ]

    audio = AudioFileClip(str(AUDIO))
    clips = []
    final = None
    try:
        for path, weight in zip(scene_paths, weights):
            source = VideoFileClip(str(path))
            duration = audio.duration * weight / sum(weights)
            clips.append(
                source.with_effects([vfx.Loop(duration=duration)]).with_duration(duration)
            )

        final = concatenate_videoclips(clips, method="compose").with_audio(audio)
        final.write_videofile(
            str(VIDEO),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=2
        )
        print("3D CARTOON VIDEO CREATED", flush=True)
    finally:
        if final is not None:
            final.close()
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
        audio.close()


if __name__ == "__main__":
    main()
