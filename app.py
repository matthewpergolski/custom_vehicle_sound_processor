import streamlit as st
import os
from pydub import AudioSegment
import tempfile
from pathlib import Path
import shutil
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

OUTPUT_DIR = Path("./custom_sounds")
ALLOWED_TYPES = ["mp3", "wav", "mov", "mp4", "m4a"]

st.set_page_config(page_title="Vehicle Sound Processor", page_icon="🔊", layout="wide")

# Custom CSS remains necessary for specific styling overrides
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem; padding-bottom: 3rem; padding-left: 1rem; padding-right: 1rem;
            max-width: 900px; margin: auto;
        }
        .header-container {
            padding: 1rem 0 1.5rem 0; margin-bottom: 2rem; text-align: center;
            border-bottom: 1px solid #333;
        }
        .header-text { color: #fafafa; font-size: 1.8rem; font-weight: 600; margin-bottom: 0.3rem; }
        .subheader-text { color: #a0a0a0; font-size: 1rem; }
        .stFileUploader {
            background-color: rgba(40, 40, 40, 0.5); padding: 1.5rem; border-radius: 8px;
            border: 1px dashed #555; margin-bottom: 2rem;
        }
        .stFileUploader label { color: #fafafa; font-size: 1.1rem; font-weight: bold; }
        .stFileUploader small { color: #a0a0a0; }
        .processing-container {
            background-color: #1c1c1e; padding: 1.5rem 2rem 2rem 2rem; border-radius: 10px;
            border: 1px solid #333; margin-top: 1rem;
        }
        .processing-container .stSubheader {
            color: #e0e0e0; font-size: 1.2rem; font-weight: bold; border-bottom: 1px solid #444;
            padding-bottom: 0.5rem; margin-bottom: 1rem;
        }
        .processing-container .stMarkdown p, .processing-container .stWrite > div { color: #ccc; font-size: 0.95rem; }
        .processing-container .stAudio { margin-top: 0.5rem; }
        .stButton>button {
            background: linear-gradient(to right, #0062cc, #007bff); color: white; padding: 0.6rem 1.2rem;
            border-radius: 6px; border: none; font-size: 1rem; font-weight: 600;
            transition: all 0.2s ease-in-out; box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2); margin-top: 1rem;
        }
        .stButton>button:hover {
            background: linear-gradient(to right, #0056b3, #0069d9); box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
            transform: translateY(-1px);
        }
        .stButton>button:active { transform: translateY(0px); box-shadow: 0 1px 2px rgba(0, 123, 255, 0.2); }
        .success-message {
            background-color: rgba(40, 167, 69, 0.2); color: #a3e0b3; border: 1px solid rgba(40, 167, 69, 0.5);
            padding: 1rem; border-radius: 5px; margin-top: 1.5rem;
        }
        .success-message h3 { margin-top: 0; color: #c3e6cb; font-size: 1.1rem; }
        .success-message ul { margin-bottom: 0; padding-left: 20px; }
        .success-message code {
            background-color: rgba(200, 200, 200, 0.2); color: #d0d0d0; padding: 0.2em 0.4em;
            border-radius: 3px; font-size: 85%;
        }
        .stException {
             border: 1px solid rgba(220, 53, 69, 0.5); background-color: rgba(220, 53, 69, 0.15);
             padding: 1rem; border-radius: 5px; color: #f5c6cb;
        }
        .stException strong { color: #ffaaaa; }
        .stSlider [data-baseweb="slider"] { margin-top: 0.5rem; margin-bottom: 1rem; }
    </style>
""",
    unsafe_allow_html=True,
)


def load_audio_file(file_path: Path, file_type: str = None) -> AudioSegment | None:
    """Load audio from various file formats using pydub."""
    try:
        audio = AudioSegment.from_file(file_path, format=file_type)
        logging.info(f"Audio loaded: {file_path}, Duration: {len(audio) / 1000:.2f}s")
        return audio
    except Exception as e:
        st.error(f"Error loading audio file: {e}")
        st.error("Ensure ffmpeg is installed and in system PATH.")
        logging.error(f"Error loading audio file {file_path}: {e}", exc_info=True)
        return None


def save_audio(
    audio_segment: AudioSegment, output_path: Path, format: str = "wav"
) -> bool:
    """Save audio segment to the specified path and format."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        audio_segment.export(output_path, format=format)
        logging.info(f"Audio exported: {output_path}")
        return True
    except Exception as e:
        st.error(f"Error saving audio file: {e}")
        logging.error(f"Error saving audio file {output_path}: {e}", exc_info=True)
        return False


def create_unique_output_directory(base_name: str) -> Path | None:
    """Create a unique directory under OUTPUT_DIR for the output files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sanitized_base = "".join(
        c if c.isalnum() or c in ("_", "-") else "_"
        for c in base_name.replace(" ", "_")
    )
    if not sanitized_base:
        sanitized_base = "output"

    output_path = OUTPUT_DIR / sanitized_base
    counter = 1
    while output_path.exists():
        output_path = OUTPUT_DIR / f"{sanitized_base}_{counter}"
        counter += 1

    try:
        output_path.mkdir()
        logging.info(f"Created output directory: {output_path}")
        return output_path
    except Exception as e:
        st.error(f"Error creating output directory: {e}")
        logging.error(
            f"Error creating output directory {output_path}: {e}", exc_info=True
        )
        return None


def main():
    st.markdown(
        """
        <div class="header-container">
            <div class="header-text">Vehicle Sound Processor</div>
            <div class="subheader-text">Create custom lock sounds for your vehicle</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "1. Upload Audio or Video",
        type=ALLOWED_TYPES,
        help=f"Supported formats: {', '.join(ALLOWED_TYPES)}",
    )

    if uploaded_file:
        file_name = uploaded_file.name
        file_suffix = Path(file_name).suffix
        base_name = Path(file_name).stem
        logging.info(f"File uploaded: {file_name}")

        temp_path = None
        preview_temp_path = None
        try:
            # Handle uploaded file temporarily
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=file_suffix
            ) as tmp_file:
                shutil.copyfileobj(uploaded_file, tmp_file)
                temp_path = Path(tmp_file.name)
                logging.info(f"Uploaded file saved temporarily to: {temp_path}")

            with st.spinner("Analyzing audio..."):
                audio = load_audio_file(temp_path)

            if audio:
                st.markdown(
                    '<div class="processing-container">', unsafe_allow_html=True
                )
                st.subheader("2. Trim Audio")

                duration_sec = len(audio) / 1000
                st.write(f"📊 **Original Duration:** {duration_sec:.2f} seconds")

                start_time, end_time = st.slider(
                    "Select time range (seconds):",
                    min_value=0.0,
                    max_value=duration_sec,
                    value=(0.0, duration_sec),  # Default to full duration
                    step=0.1,
                    format="%.1fs",
                )

                selected_duration = end_time - start_time
                st.write(f"✂️ **Selected Duration:** {selected_duration:.2f} seconds")

                st.subheader("3. Preview Selection")
                start_ms = int(start_time * 1000)
                end_ms = int(end_time * 1000)
                trimmed_audio = audio[start_ms:end_ms]

                # Generate preview
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".wav"
                ) as tmp_preview_file:
                    preview_temp_path = Path(tmp_preview_file.name)
                    if save_audio(trimmed_audio, preview_temp_path, format="wav"):
                        try:
                            st.audio(str(preview_temp_path))
                        except Exception as e:
                            st.error(f"Could not play preview: {e}")
                            logging.error(
                                f"Error playing preview file {preview_temp_path}: {e}",
                                exc_info=True,
                            )
                            preview_temp_path = None
                    else:
                        st.error("Could not generate audio preview.")
                        preview_temp_path = None

                # Save functionality
                st.subheader("4. Save Output")
                if st.button("💾 Save as Lock Sound", use_container_width=True):
                    with st.spinner("Saving files..."):
                        output_dir = create_unique_output_directory(base_name)
                        if output_dir:
                            original_dest_path = output_dir / file_name
                            processed_lockchime_path = output_dir / "LockChime.wav"
                            processed_named_path = output_dir / f"{output_dir.name}.wav"

                            save_ok = True
                            try:
                                shutil.copy2(temp_path, original_dest_path)
                                logging.info(
                                    f"Original file copied to: {original_dest_path}"
                                )
                            except Exception as e:
                                st.error(f"Error copying original file: {e}")
                                logging.error(
                                    f"Error copying {temp_path} to {original_dest_path}: {e}",
                                    exc_info=True,
                                )
                                save_ok = False

                            if save_ok and not save_audio(
                                trimmed_audio, processed_lockchime_path
                            ):
                                save_ok = False
                            if save_ok and not save_audio(
                                trimmed_audio, processed_named_path
                            ):
                                save_ok = False

                            if save_ok:
                                st.markdown(
                                    f"""
                                    <div class="success-message">
                                        <h3>✅ Files saved successfully!</h3>
                                        <p>Output Location: <code>{output_dir}</code></p>
                                        <ul>
                                            <li>Original: <code>{original_dest_path.name}</code></li>
                                            <li>Lock Sound: <code>{processed_lockchime_path.name}</code></li>
                                            <li>Named WAV: <code>{processed_named_path.name}</code></li>
                                        </ul>
                                    </div>
                                """,
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.error(
                                    "An error occurred while saving one or more files."
                                )
                        else:
                            st.error(
                                "Could not create output directory. Saving failed."
                            )

                st.markdown(
                    "</div>", unsafe_allow_html=True
                )  # Close processing-container

        except Exception as e:
            st.error("An unexpected error occurred during processing.")
            logging.error(f"Unexpected error for file {file_name}: {e}", exc_info=True)
        finally:
            # Cleanup temporary files
            if temp_path and temp_path.exists():
                try:
                    os.unlink(temp_path)
                    logging.info(f"Cleaned up temp upload: {temp_path}")
                except Exception as e:
                    logging.warning(
                        f"Could not delete temp upload file {temp_path}: {e}"
                    )
            if preview_temp_path and preview_temp_path.exists():
                try:
                    os.unlink(preview_temp_path)
                    logging.info(f"Cleaned up temp preview: {preview_temp_path}")
                except Exception as e:
                    logging.warning(
                        f"Could not delete temp preview file {preview_temp_path}: {e}"
                    )


if __name__ == "__main__":
    main()
