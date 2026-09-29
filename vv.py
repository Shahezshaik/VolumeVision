import cv2
import mediapipe as mp
import math
import numpy as np
import time
from pycaw.pycaw import AudioUtilities


# =========================
# AUDIO SETUP
# =========================

devices = AudioUtilities.GetSpeakers()
volume = devices.EndpointVolume

vRange = volume.GetVolumeRange()
minv, maxv = vRange[0], vRange[1]


# =========================
# MEDIAPIPE SETUP
# =========================

mp_hands = mp.solutions.hands
draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)


# =========================
# CAMERA
# =========================

capture = cv2.VideoCapture(0)

capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not capture.isOpened():
    print("Unable to open camera")
    exit()

print("VolumeVision Started")


# =========================
# VARIABLES
# =========================

previous_volume = None
display_volume = 0

previous_time = 0
fps = 0


# =========================
# MAIN LOOP
# =========================

while True:

    success, image = capture.read()

    if not success:
        print("Failed to read camera")
        break


    # =========================
    # MIRROR CAMERA
    # =========================

    image = cv2.flip(image, 1)


    # =========================
    # CROP
    # =========================

    height, width, _ = image.shape

    target_ratio = 8 / 4
    current_ratio = width / height

    if current_ratio > target_ratio:

        new_width = int(height * target_ratio)

        start_x = (width - new_width) // 2

        image = image[
            :,
            start_x:start_x + new_width
        ]

    else:

        new_height = int(width / target_ratio)

        start_y = (height - new_height) // 2

        image = image[
            start_y:start_y + new_height
        ]


    height, width, _ = image.shape


    # =========================
    # FPS
    # =========================

    current_time = time.time()

    if previous_time != 0:
        fps = 1 / (current_time - previous_time)

    previous_time = current_time


    # =========================
    # MEDIAPIPE
    # =========================

    rgbimage = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    processed_image = hands.process(
        rgbimage
    )

    hand_detected = False
    distance = 0


    # =========================
    # HAND DETECTION
    # =========================

    if processed_image.multi_hand_landmarks:

        hand_detected = True

        handLandmarks = (
            processed_image.multi_hand_landmarks[0]
        )


        # =========================
        # THUMB & INDEX
        # =========================

        thumb = handLandmarks.landmark[4]
        index = handLandmarks.landmark[8]

        tpx = int(thumb.x * width)
        tpy = int(thumb.y * height)

        ipx = int(index.x * width)
        ipy = int(index.y * height)


        # =========================
        # HAND LANDMARKS
        # =========================

        draw.draw_landmarks(
            image,
            handLandmarks,
            mp_hands.HAND_CONNECTIONS,
            mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
            mp.solutions.drawing_styles.get_default_hand_connections_style()
        )


        # =========================
        # FINGER POINTS
        # =========================

        cv2.circle(
            image,
            (tpx, tpy),
            14,
            (255, 0, 255),
            cv2.FILLED
        )

        cv2.circle(
            image,
            (ipx, ipy),
            14,
            (255, 0, 255),
            cv2.FILLED
        )


        # =========================
        # LINE
        # =========================

        cv2.line(
            image,
            (tpx, tpy),
            (ipx, ipy),
            (0, 255, 255),
            5
        )


        # =========================
        # DISTANCE
        # =========================

        distance = math.hypot(
            ipx - tpx,
            ipy - tpy
        )


        # =========================
        # VOLUME
        # =========================

        current_volume = np.interp(
            distance,
            [30, 250],
            [minv, maxv]
        )

        display_volume = np.interp(
            distance,
            [30, 250],
            [0, 100]
        )


        # =========================
        # UPDATE VOLUME
        # =========================

        if (
            previous_volume is None
            or abs(
                current_volume - previous_volume
            ) > 0.5
        ):

            volume.SetMasterVolumeLevel(
                float(current_volume),
                None
            )

            previous_volume = current_volume


    # =========================
    # TOP HEADER
    # =========================

    overlay = image.copy()

    cv2.rectangle(
        overlay,
        (0, 0),
        (width, 85),
        (20, 20, 20),
        -1
    )

    image = cv2.addWeighted(
        overlay,
        0.9,
        image,
        0.1,
        0
    )


    # =========================
    # TITLE
    # =========================

    cv2.putText(
        image,
        "VOLUMEVISION",
        (25, 38),
        cv2.FONT_HERSHEY_DUPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.putText(
        image,
        "GESTURE CONTROL",
        (25, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (170, 170, 170),
        1
    )


    # =========================
    # SMALL VOLUME CARD
    # =========================

    card_x = 25
    card_y = 78
    card_w = width - 50
    card_h = 75

    cv2.rectangle(
        image,
        (card_x, card_y),
        (
            card_x + card_w,
            card_y + card_h
        ),
        (25, 25, 25),
        -1
    )

    cv2.rectangle(
        image,
        (card_x, card_y),
        (
            card_x + card_w,
            card_y + card_h
        ),
        (80, 80, 80),
        2
    )


    # =========================
    # VOLUME %
    # =========================

    volume_text = f"{int(display_volume)}%"

    text_size = cv2.getTextSize(
        volume_text,
        cv2.FONT_HERSHEY_DUPLEX,
        0.8,
        2
    )[0]

    text_x = (
        card_x
        + (card_w - text_size[0]) // 2
    )

    cv2.putText(
        image,
        volume_text,
        (
            text_x,
            card_y + 30
        ),
        cv2.FONT_HERSHEY_DUPLEX,
        0.8,
        (0, 255, 100),
        2
    )


    # =========================
    # VOLUME BAR
    # =========================

    bar_x = card_x + 100
    bar_y = card_y + 47
    bar_w = card_w - 200
    bar_h = 8

    cv2.rectangle(
        image,
        (bar_x, bar_y),
        (
            bar_x + bar_w,
            bar_y + bar_h
        ),
        (60, 60, 60),
        -1
    )

    filled_width = int(
        bar_w
        * display_volume
        / 100
    )

    if filled_width > 0:

        cv2.rectangle(
            image,
            (bar_x, bar_y),
            (
                bar_x + filled_width,
                bar_y + bar_h
            ),
            (0, 220, 120),
            -1
        )


    # =========================
    # STATUS
    # =========================

    if hand_detected:

        status = "HAND DETECTED"
        status_color = (0, 255, 120)

        # Success circle
        cv2.circle(
            image,
            (38, height - 92),
            13,
            (0, 200, 100),
            2
        )

        # Check mark - first line
        cv2.line(
            image,
            (31, height - 92),
            (36, height - 87),
            (0, 255, 120),
            2
        )

        # Check mark - second line
        cv2.line(
            image,
            (36, height - 87),
            (45, height - 99),
            (0, 255, 120),
            2
        )

    else:

        status = "SHOW YOUR HAND"
        status_color = (0, 180, 255)

        # Warning circle
        cv2.circle(
            image,
            (38, height - 92),
            13,
            (0, 180, 255),
            2
        )

        # Exclamation mark
        cv2.line(
            image,
            (38, height - 99),
            (38, height - 90),
            (0, 180, 255),
            2
        )

        cv2.circle(
            image,
            (38, height - 85),
            1,
            (0, 180, 255),
            cv2.FILLED
        )


    # =========================
    # STATUS TEXT
    # =========================

    cv2.putText(
        image,
        status,
        (60, height - 85),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        status_color,
        2
    )


    # =========================
    # DISTANCE
    # =========================

    cv2.putText(
        image,
        f"Finger Distance: {int(distance)} px",
        (25, height - 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (210, 210, 210),
        1
    )


    # =========================
    # FPS
    # =========================

    cv2.putText(
        image,
        f"FPS: {int(fps)}",
        (25, height - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (150, 150, 150),
        1
    )


    # =========================
    # DISPLAY
    # =========================

    cv2.imshow(
        "VolumeVision",
        image
    )


    # =========================
    # EXIT
    # =========================

    if cv2.waitKey(1) & 0xFF == 27:
        break


# =========================
# CLEANUP
# =========================

capture.release()
cv2.destroyAllWindows()

print("VolumeVision Closed")