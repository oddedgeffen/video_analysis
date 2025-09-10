
if __name__ == "__main__":
    # Load existing enriched transcript
    with open(r'media\uploads\videos\2025_09_08___21_50_08_video-1757357401352\images_text_transcript.json', 'r', encoding='utf-8') as f:
        images_text_transcript = json.load(f)
    audio_path = r"C:\video_analysis\code\video_analysis_saas\media\uploads\videos\2025_09_08___21_50_08_video-1757357401352\audio.wav"
    voice_images_text_transcript = process_voice_features(images_text_transcript, audio_path)