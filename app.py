import os
import shutil
import cv2
import moviepy.editor as mp
import speech_recognition as sr
from translate import Translator
from gtts import gTTS
from flask import Flask, render_template, request, redirect, url_for, send_file

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/downloads'

def process_video(input_video_path, target_language='hi'):
    # Create a temporary directory to store audio files
    temp_dir = 'temp_audio_files'
    os.makedirs(temp_dir, exist_ok=True)

    # Initialize the speech recognition engine
    r = sr.Recognizer()

    # Initialize the translator
    translator = Translator(to_lang=target_language)

    # Process the video
    video_clip = mp.VideoFileClip(input_video_path)

    dubbed_audio = []

    # Extract audio from the video and save it as a temporary WAV file
    video_audio = video_clip.audio
    temp_audio_file = os.path.join(temp_dir, 'temp_audio.wav')
    video_audio.write_audiofile(temp_audio_file)

    with sr.AudioFile(temp_audio_file) as source:
        audio = r.record(source)
        try:
            # Transcribe English audio
            text = r.recognize_google(audio)

            # Translate to the target language
            translated_text = translator.translate(text)

            # Convert translated text to speech
            tts = gTTS(translated_text, lang=target_language)
            temp_audio_file = os.path.join(temp_dir, 'temp_audio.mp3')
            tts.save(temp_audio_file)

            # Append the dubbed audio segment
            dubbed_audio.append(mp.AudioFileClip(temp_audio_file))

        except sr.UnknownValueError:
            pass

    # Concatenate the dubbed audio segments
    final_dubbed_audio = mp.concatenate_audioclips(dubbed_audio)

    # Set the dubbed audio to the video
    video_clip = video_clip.set_audio(final_dubbed_audio)

    # Save the final dubbed video with a unique name
    output_video_path = os.path.join(app.config['OUTPUT_FOLDER'], 'output_dubbed_video.mp4')
    video_clip.write_videofile(output_video_path, codec='libx264')

    # Clean up temporary audio and frame files
    shutil.rmtree(temp_dir)

    return output_video_path

@app.route('/', methods=['GET', 'POST'])
def index():
    video_url = None  # Initialize video URL
    if request.method == 'POST':
        # Handle video upload
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        if file:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)

            # Process the video
            # output_video_path = process_video(filename)
            
            # Get the selected target language from the form
            target_language = request.form.get('target-language', 'hi')

            # Process the video with the selected target language
            output_video_path = process_video(filename, target_language)

            # Clean up the uploaded file
            os.remove(filename)

            # Provide the video URL without automatic download
            video_url = url_for('static', filename='downloads/output_dubbed_video.mp4')

    return render_template('index.html', video_url=video_url)

if __name__ == '__main__':
    app.run(debug=True)
