from dotenv import load_dotenv # type: ignore
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import time
import tkinter as tk
import cv2 # type: ignore
from deepface import DeepFace # type: ignore
import spotipy # type: ignore
from spotipy.oauth2 import SpotifyOAuth # type: ignore
import pygame

# Load the environment variables from .env file
load_dotenv()

on = True
mode = "Day"
volume = 1
fcolor = "black"
bcolor = "white"
narration = False

def mode_change():
    global mode
    global color_start
    global color_end
    global volume
    global fcolor
    global bcolor
    file_path=""
    
    if mode == "Day":
        mode = "Night"
        color_start = colors[2]
        color_end = colors[3]
        fcolor = "white"
        bcolor = "grey20"
        volume = 0.5
        file_path = os.path.join(os.path.dirname(__file__), "Voicelines", "activate_night.mp3")
    elif mode == "Night":
        mode="Day"
        color_start = colors[0]
        color_end = colors[1]
        fcolor="black"
        bcolor="white"
        volume = 1
        file_path = os.path.join(os.path.dirname(__file__), "Voicelines", "activate_day.mp3")

    
    play_button.config(background=f"{bcolor}",fg=f"{fcolor}")
    exit_button.config(background=f"{bcolor}",fg=f"{fcolor}")
    on_button.config(background=f"{bcolor}",fg=f"{fcolor}")
    narration_button.config(background=f"{bcolor}",fg=f"{fcolor}")
    mode_button.config(text=f"Mode: {mode}",background=f"{bcolor}",fg=f"{fcolor}")
    create_gradient(canvas, 500, 280, color_start, color_end)
    slider.set(volume*100)
    slider.config(bg=f"{bcolor}",fg=f"{fcolor}")
    canvas.itemconfig(text_canvas,fill=fcolor)
    canvas.tag_raise(text_canvas)

    
    if narration:
        play_audio(file_path)

# Spotify Credentials
CLIENT_ID = os.getenv("CLIENT_ID") 
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8888/callback"
SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=SCOPE))

def play_audio(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

def detect():
    if not on:
        print("Program is Disabled")
        if narration:
            file_path = os.path.join(os.path.dirname(__file__), "Voicelines", "program_disabled.mp3")
            play_audio(file_path)
        return
    if narration:
        file_path = os.path.join(os.path.dirname(__file__), "Voicelines", "detecting.mp3")
        play_audio(file_path)
    emotion = detect_emotion()
    if emotion:
        play(emotion)

def detect_emotion():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) # this is the magic!

    if not cap.isOpened():
        print("Error: Camera not accessible")
        return
    frames = []
    for _ in range(10):
        ret, frame = cap.read()
        if not ret:
            print("Error: Camera capture failed.")
            cap.release()
            return None
        frames.append(frame)

    cap.release()
    cv2.destroyAllWindows()

    emotions = []
    for frame in frames:
        try:
            analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=True)
            emotions.append(analysis[0]['dominant_emotion'])
        except:
            pass

    if emotions:
        most_common = max(set(emotions), key=emotions.count)
        print(f"Detected Emotion: {most_common}")
        return most_common
    else:
        print("No face detected.")
        if narration:
            file_path = os.path.join(os.path.dirname(__file__), "Voicelines", "no_face.mp3")
            play_audio(file_path)
        return None

def play(emotion):
    songs = {
        "happy": "Happy Pharrell Williams",
        "sad": "Summertime Sadness Lana Del Rey",
        "angry": "Angry The Rolling Stones",
        "neutral": "Imagine John Lennon",
        "fear": "Thriller Michael Jackson",
        "surprise": "Surprise Surprise Billy Talent",
        "disgust":"Disgusted Miley Cyrus"
    }
    
    files = {
        "happy": os.path.join(os.path.dirname(__file__), "Voicelines", "happy_song.mp3"),
        "sad": os.path.join(os.path.dirname(__file__), "Voicelines", "sad_song.mp3"),
        "angry": os.path.join(os.path.dirname(__file__), "Voicelines", "angry_song.mp3"),
        "neutral": os.path.join(os.path.dirname(__file__), "Voicelines", "neutral_song.mp3"),
        "fear": os.path.join(os.path.dirname(__file__), "Voicelines", "fear_song.mp3"),
        "surprise": os.path.join(os.path.dirname(__file__), "Voicelines", "surprise_song.mp3"),
        "disgust":os.path.join(os.path.dirname(__file__), "Voicelines", "disgust_song.mp3") 
    }

    if emotion not in songs:
        print("No song found for this emotion.")
        return

    if narration:
        play_audio(files[emotion])
    play_song(songs[emotion])

def get_active_device():
    devices = sp.devices()
    if not devices["devices"]:
        print("No active Spotify devices found!")
        if narration:
            file_path = os.path.join(os.path.dirname(__file__), "Voicelines", "no_device.mp3")
            play_audio(file_path)
        return None

    return devices

def play_song(song_name):
    global volume
    results = sp.search(q=song_name, type="track", limit=1)
    if not results["tracks"]["items"]:
        print("Song not found!")
        return

    track_uri = results["tracks"]["items"][0]["uri"]
    preferred_device_name="LIRON_LAPTOP"
    devices = get_active_device()
    device_id = None
    for device in devices["devices"]:
        if device["name"] == preferred_device_name:
            device_id = device["id"]
            break
    # If the preferred device isn't found, use the first available one
    if not device_id:
        print(f"Preferred device '{preferred_device_name}' not found. Using another available device.")
        device_id = devices["devices"][0]["id"]

    if device_id:
        # Set the volume (0 to 100)
        sp.volume(int(volume*100), device_id=device_id)

        sp.start_playback(device_id=device_id, uris=[track_uri])
        print(f"Playing: {song_name}")

def change_on():
    global on
    if on:
        on = False
        file_path = os.path.join(os.path.dirname(__file__), "Voicelines", "disable.mp3")
    else:
        on = True
        file_path = os.path.join(os.path.dirname(__file__), "Voicelines", "activate.mp3")

    on_button.config(text=f"Enabled: {on}")
    if narration:
        play_audio(file_path)

def switch_narration():    
    global narration
    if narration:
        narration = False
    else:
        narration = True
    narration_button.config(text=f"Narration: {narration}")

def create_gradient(canvas, width, height, color1, color2):
    """
    Creates a vertical gradient on a given canvas.
    """
    for i in range(height):
        r = int(color1[0] + (color2[0] - color1[0]) * (i / height))
        g = int(color1[1] + (color2[1] - color1[1]) * (i / height))
        b = int(color1[2] + (color2[2] - color1[2]) * (i / height))
        color = f"#{r:02x}{g:02x}{b:02x}"
        canvas.create_line(0, i, width, i, fill=color)


def chagne_volume(value):
    global volume
    volume = int(value)/100



# Create GUI
root = tk.Tk()
root.title("Spotify Emotion Player")
root.geometry("300x280")
# root.configure(background=f"#{color}")
root.resizable(False,False)

# Create Canvas
canvas = tk.Canvas(root, width=500, height=280, highlightthickness=0)
canvas.pack(fill="both", expand=True)

colors = [
    (220,220,220),
    (120,120,120),
    (80,80,80),
    (20,20,20),
]
# Define gradient colors (RGB)
color_start = colors[0] 
color_end = colors[1]    

# Apply gradient
create_gradient(canvas, 500, 280, color_start, color_end)

# Button Styles
button_width = 15
button_height = 1

# Create Buttons
buttons = [
    tk.Button(root, text="Detect & Play", width=button_width, height=button_height, command=detect),
    tk.Button(root, text=f"Mode: {mode}", width=button_width, height=button_height, command=mode_change),
    tk.Button(root, text="Exit", width=button_width, height=button_height, command=exit),
    tk.Button(root, text=f"Enabled: {on}", width=button_width, height=button_height, command=change_on),
    tk.Button(root, text=f"Narration: {narration}", width=button_width, height=button_height, command=switch_narration),
]

# Position Buttons in Two Rows
positions = [
    (0.5, 0.2),  # First group (3 buttons)
    (0.5, 0.35),
    (0.5, 0.5),
    (0.5, 0.65),  # Second group (2 buttons)
    (0.5, 0.8),
]

for btn, (x, y) in zip(buttons, positions):
    btn.place(relx=x, rely=y, anchor="center")

play_button = buttons[0]
mode_button = buttons[1]
exit_button = buttons[2]
on_button = buttons[3]
narration_button = buttons[4]

slider = tk.Scale(root,from_=100,to=0,command=chagne_volume)
slider.place(relx=0.1,rely=0.5,anchor="center")
slider.set(100)

text_canvas = canvas.create_text(10, 70, anchor = "nw")
canvas.itemconfig(text_canvas, text="Volume")

root.mainloop()
