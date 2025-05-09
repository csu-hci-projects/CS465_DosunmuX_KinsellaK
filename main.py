import sys
import threading
import queue
import time

# ---------- third‑party packages ----------
import cv2                      # webcam frames
import mediapipe as mp          # hand landmarks
import speech_recognition as sr # microphone
import pygame                   # display

# ---------- Configuration ----------
DEBUG = True                    # Set to True to show hand tracking debug window

# ---------- Shared Stop Signal ----------
stop_event = threading.Event()  # Event to signal all threads to stop

# ---------- messaging between threads ----------
cmd_queue = queue.Queue()       # holds strings: "grow" | "shrink" | "toggle"

# ---------- hand‑gesture worker ----------
def gesture_worker():
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False,
                           max_num_hands=1,
                           min_detection_confidence=0.6,
                           min_tracking_confidence=0.5)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Gesture] 🔴 No camera found ‑‑ gesture control disabled")
        return

    def count_extended_fingers(landmarks):
        """Rough finger‑count heuristic for one hand."""
        # Landmark indices for fingertips (thumb tip slightly different test)
        TIPS = [8, 12, 16, 20]  # index, middle, ring, pinky tips
        extended = 0
        for tip in TIPS:
            if landmarks[tip].y < landmarks[tip - 2].y:  # tip above its PIP
                extended += 1
        # Thumb: tip (4) right of joint (2) on a right hand → extended
        if landmarks[4].x > landmarks[3].x:
            extended += 1
        return extended

    last_state = None
    while not stop_event.is_set():
        ok, frame = cap.read()
        if not ok:
            print("[Gesture] 🔴 Failed to read frame from camera.")
            break

        if stop_event.is_set():
            break

        frame.flags.writeable = False
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        frame.flags.writeable = True

        debug_frame = None
        debug_frame_flipped = None
        if DEBUG:
            debug_frame = frame.copy()

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            lm = hand_landmarks.landmark
            fingers = count_extended_fingers(lm)
            state = "grow" if fingers >= 3 else "shrink"
            if state != last_state:          # only send on change
                cmd_queue.put(state)
                last_state = state

            if DEBUG and debug_frame is not None:
                mp_drawing.draw_landmarks(
                    debug_frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())

                debug_frame_flipped = cv2.flip(debug_frame, 1)
                cv2.putText(debug_frame_flipped, f'Fingers: {fingers}', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        else:
            last_state = None
            if DEBUG and debug_frame is not None:
                debug_frame_flipped = cv2.flip(debug_frame, 1)
                cv2.putText(debug_frame_flipped, 'No Hand Detected', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        if DEBUG:
            if debug_frame_flipped is not None:
                cv2.imshow('Hand Tracking Debug', debug_frame_flipped)
            elif debug_frame is not None:
                cv2.imshow('Hand Tracking Debug', cv2.flip(debug_frame, 1))

            key = cv2.waitKey(5) & 0xFF
            if key == 27:
                print("[Gesture] Esc pressed in debug window. Signaling stop.")
                stop_event.set()
                break
        else:
            time.sleep(0.01)

        if stop_event.is_set():
            break

    print("[Gesture] Releasing camera and closing windows...")
    cap.release()
    if DEBUG:
        try:
            cv2.destroyWindow('Hand Tracking Debug')
        except cv2.error:
            pass
    print("[Gesture] Worker finished.")

# ---------- voice‑command worker ----------
def voice_worker():
    r = sr.Recognizer()
    mic = None
    try:
        mic = sr.Microphone()
        print("[Voice] ✅ Microphone found, starting voice recognition...")
    except OSError:
        print("[Voice] 🔴 No microphone found ‑‑ voice control disabled")
        return

    GROW_WORDS = ["grow", "expand", "go", "enlarge", "big", "bigger"]
    SHRINK_WORDS = ["shrink", "drink", "small", "smaller", "reduce", "less"]

    with mic:
        print("[Voice] Adjusting for ambient noise...")
        r.adjust_for_ambient_noise(mic, duration=1)
        print("[Voice] Ready to listen.")

    while not stop_event.is_set():
        try:
            with mic:
                audio = r.listen(mic, timeout=1, phrase_time_limit=5)
            if stop_event.is_set():
                break

            if DEBUG: print("[Voice] Recognizing...")
            phrase = r.recognize_google(audio).lower()
            if DEBUG: print(f"[Voice] Heard: '{phrase}'")

            recognized_words = phrase.split()
            command_sent = False
            for word in recognized_words:
                if stop_event.is_set(): break
                if word in GROW_WORDS:
                    cmd_queue.put("grow")
                    if DEBUG: print("[Voice] Command: grow")
                    command_sent = True
                    break
                elif word in SHRINK_WORDS:
                    cmd_queue.put("shrink")
                    if DEBUG: print("[Voice] Command: shrink")
                    command_sent = True
                    break
            if stop_event.is_set(): break

        except sr.WaitTimeoutError:
            if stop_event.is_set():
                break
            pass
        except sr.UnknownValueError:
            if stop_event.is_set(): break
            if DEBUG: print("[Voice] ❓ Speech not understood.")
            pass
        except sr.RequestError as e:
            if stop_event.is_set(): break
            print(f"[Voice] ⚠️ API error: {e}")
            for _ in range(5):
                if stop_event.is_set(): break
                time.sleep(1)
            if stop_event.is_set(): break

    print("[Voice] Stop event received. Worker finished.")

# ---------- pygame main ----------
def main():
    gesture_thread = threading.Thread(target=gesture_worker, daemon=True)
    voice_thread = threading.Thread(target=voice_worker, daemon=True)
    gesture_thread.start()
    voice_thread.start()

    pygame.init()
    WIDTH, HEIGHT = 600, 400
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Gesture / Voice Controlled Dot")

    center = (WIDTH // 2, HEIGHT // 2)
    radius     = 20
    min_radius = 5
    max_radius = 200
    change_rate = 2
    is_growing  = True

    clock = pygame.time.Clock()
    running = True
    while running:
        if stop_event.is_set():
            running = False
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("[Main] Pygame QUIT event received. Signaling stop.")
                running = False
                stop_event.set()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    print("[Main] Pygame ESC key pressed. Signaling stop.")
                    running = False
                    stop_event.set()
                elif event.key == pygame.K_SPACE:
                    cmd_queue.put("toggle")

        if not running:
            break

        try:
            while True:
                cmd = cmd_queue.get_nowait()
                if cmd == "toggle":
                    is_growing = not is_growing
                elif cmd == "grow":
                    is_growing = True
                elif cmd == "shrink":
                    is_growing = False
        except queue.Empty:
            pass

        if is_growing:
            radius = min(radius + change_rate, max_radius)
        else:
            radius = max(radius - change_rate, min_radius)

        screen.fill((0, 0, 0))
        pygame.draw.circle(screen, (255, 0, 0), center, radius)
        pygame.display.flip()

        clock.tick(60)

    print("[Main] Main loop exited.")

    # --- Graceful Shutdown ---
    if not stop_event.is_set():
        print("[Main] Setting stop event before final exit.")
        stop_event.set()

    print("[Main] Exiting Pygame...")
    pygame.quit()

    print("[Main] Waiting for worker threads to finish...")
    gesture_thread.join(timeout=2.0)
    voice_thread.join(timeout=2.0)

    if gesture_thread.is_alive():
        print("[Main] Warning: Gesture thread did not finish cleanly.")
    if voice_thread.is_alive():
        print("[Main] Warning: Voice thread did not finish cleanly.")

    if DEBUG:
        print("[Main] Attempting final OpenCV window cleanup.")
        cv2.destroyAllWindows()

    print("[Main] Exiting application.")

if __name__ == "__main__":
    main()
