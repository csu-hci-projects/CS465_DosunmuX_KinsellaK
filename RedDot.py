import pygame
import sys

def main():
    pygame.init()
    
    # Window dimensions
    WIDTH, HEIGHT = 600, 400
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Growing/Shrinking Dot")
    
    # Center coordinates for the dot
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    
    # Initial dot radius
    radius = 20
    
    # Whether the dot is currently growing or shrinking
    is_growing = True
    
    # Speed of growth/shrinking
    change_rate = 3
    
    # Minimum and maximum radius
    min_radius = 5
    max_radius = 200
    
    clock = pygame.time.Clock()

    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # Toggle growing/shrinking on space bar press
                    is_growing = not is_growing
        
        # Grow or shrink the radius based on the is_growing toggle
        if is_growing:
            radius += change_rate
            if radius >= max_radius:
                radius = max_radius
        else:
            radius -= change_rate
            if radius <= min_radius:
                radius = min_radius
        
        # Fill the screen with black
        screen.fill((0, 0, 0))
        
        # Draw the red circle at the center
        pygame.draw.circle(screen, (255, 0, 0), (center_x, center_y), radius)
        
        # Update the display
        pygame.display.flip()
        
        # Control the frame rate
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()







# import sys
# import threading
# import queue
# import time

# # ---------- third‑party packages ----------
# import cv2                      # webcam frames
# import mediapipe as mp          # hand landmarks
# import speech_recognition as sr # microphone
# import pygame                   # display

# # ---------- messaging between threads ----------
# cmd_queue = queue.Queue()       # holds strings: "grow" | "shrink" | "toggle"

# # ---------- hand‑gesture worker ----------
# def gesture_worker():
#     mp_hands = mp.solutions.hands
#     hands = mp_hands.Hands(static_image_mode=False,
#                            max_num_hands=1,
#                            min_detection_confidence=0.6,
#                            min_tracking_confidence=0.5)
#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened():
#         print("[Gesture] 🔴 No camera found ‑‑ gesture control disabled")
#         return

#     def count_extended_fingers(landmarks):
#         """Rough finger‑count heuristic for one hand."""
#         # Landmark indices for fingertips (thumb tip slightly different test)
#         TIPS = [8, 12, 16, 20]  # index, middle, ring, pinky tips
#         extended = 0
#         for tip in TIPS:
#             if landmarks[tip].y < landmarks[tip - 2].y:  # tip above its PIP
#                 extended += 1
#         # Thumb: tip (4) right of joint (2) on a right hand → extended
#         if landmarks[4].x > landmarks[3].x:
#             extended += 1
#         return extended

#     last_state = None  # None | "grow" | "shrink"
#     while True:
#         ok, frame = cap.read()
#         if not ok:
#             break
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = hands.process(rgb)

#         if results.multi_hand_landmarks:
#             lm = results.multi_hand_landmarks[0].landmark
#             fingers = count_extended_fingers(lm)
#             state = "grow" if fingers >= 3 else "shrink"
#             if state != last_state:          # only send on change
#                 cmd_queue.put(state)
#                 last_state = state
#         else:
#             last_state = None                # hand disappeared

#         # small sleep keeps CPU usage in check
#         time.sleep(0.02)

#     cap.release()

# # ---------- voice‑command worker ----------
# def voice_worker():
#     r = sr.Recognizer()
#     mic = None
#     try:
#         mic = sr.Microphone()
#     except OSError:
#         print("[Voice] 🔴 No microphone found ‑‑ voice control disabled")
#         return

#     with mic:
#         r.adjust_for_ambient_noise(mic, duration=1)

#     while True:
#         try:
#             with mic:
#                 audio = r.listen(mic, timeout=5, phrase_time_limit=3)
#             phrase = r.recognize_google(audio).lower()
#             if "grow" in phrase:
#                 cmd_queue.put("grow")
#             elif "shrink" in phrase:
#                 cmd_queue.put("shrink")
#         except sr.WaitTimeoutError:
#             pass                      # no speech in the last 5 s
#         except sr.UnknownValueError:
#             pass                      # speech not understood
#         except sr.RequestError as e:
#             print(f"[Voice] API error: {e}")
#             time.sleep(5)             # back off a little

# # ---------- pygame main ----------
# def main():
#     # --- start helpers ---
#     threading.Thread(target=gesture_worker, daemon=True).start()
#     threading.Thread(target=voice_worker,    daemon=True).start()

#     pygame.init()
#     WIDTH, HEIGHT = 600, 400
#     screen = pygame.display.set_mode((WIDTH, HEIGHT))
#     pygame.display.set_caption("Gesture / Voice Controlled Dot")

#     center = (WIDTH // 2, HEIGHT // 2)
#     radius     = 20
#     min_radius = 5
#     max_radius = 200
#     change_rate = 2
#     is_growing  = True

#     clock = pygame.time.Clock()
#     running = True
#     while running:
#         # ---------- handle pygame events ----------
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 running = False
#             elif event.type == pygame.KEYDOWN:
#                 if event.key == pygame.K_ESCAPE:
#                     running = False
#                 elif event.key == pygame.K_SPACE:
#                     cmd_queue.put("toggle")

#         # ---------- handle commands from threads ----------
#         try:
#             while True:                       # drain the queue
#                 cmd = cmd_queue.get_nowait()
#                 if cmd == "toggle":
#                     is_growing = not is_growing
#                 elif cmd == "grow":
#                     is_growing = True
#                 elif cmd == "shrink":
#                     is_growing = False
#         except queue.Empty:
#             pass

#         # ---------- update physics ----------
#         if is_growing:
#             radius = min(radius + change_rate, max_radius)
#         else:
#             radius = max(radius - change_rate, min_radius)

#         # ---------- draw ----------
#         screen.fill((0, 0, 0))                # black background
#         pygame.draw.circle(screen, (255, 0, 0), center, radius)
#         pygame.display.flip()

#         clock.tick(60)

#     pygame.quit()
#     sys.exit()

# if __name__ == "__main__":
#     main()
