import os
import sys
import math
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

LEFT_EAR = 7
RIGHT_EAR = 8
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24


class PoseAnalyzer:
    def __init__(self, model_path=None):
        if model_path is None:
            if getattr(sys, "frozen", False):
                base_dir = sys._MEIPASS
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(base_dir, "pose_landmarker_lite.task")

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Не найден файл модели '{model_path}'. Положите pose_landmarker_lite.task в папку проекта."
            )

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            min_pose_detection_confidence=0.6,
            min_pose_presence_confidence=0.6
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)

    def _calculate_angle_from_vertical(self, p1, p2):
        dx = abs(p2[0] - p1[0])
        dy = abs(p2[1] - p1[1])
        if dy == 0:
            return 90.0
        angle_rad = math.atan2(dx, dy)
        return math.degrees(angle_rad)

    def process_frame(self, frame, max_torso, max_neck):
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        detection_result = self.detector.detect(mp_image)

        status = "Человек не найден"
        is_bad_posture = False

        if detection_result.pose_landmarks and len(detection_result.pose_landmarks) > 0:
            lm = detection_result.pose_landmarks[0]

            left_vis = lm[LEFT_SHOULDER].visibility
            right_vis = lm[RIGHT_SHOULDER].visibility

            if left_vis > right_vis:
                ear_lm = lm[LEFT_EAR]
                shoulder_lm = lm[LEFT_SHOULDER]
                hip_lm = lm[LEFT_HIP]
            else:
                ear_lm = lm[RIGHT_EAR]
                shoulder_lm = lm[RIGHT_SHOULDER]
                hip_lm = lm[RIGHT_HIP]

            if ear_lm.visibility > 0.5 and shoulder_lm.visibility > 0.5 and hip_lm.visibility > 0.5:
                ear = (int(ear_lm.x * w), int(ear_lm.y * h))
                shoulder = (int(shoulder_lm.x * w), int(shoulder_lm.y * h))
                hip = (int(hip_lm.x * w), int(hip_lm.y * h))

                torso_angle = int(self._calculate_angle_from_vertical(hip, shoulder))
                neck_angle = int(self._calculate_angle_from_vertical(shoulder, ear))

                if torso_angle > max_torso or neck_angle > max_neck:
                    is_bad_posture = True
                    status = "СУТУЛОСТЬ!"
                    color = (0, 0, 255)
                else:
                    status = "Осанка в норме"
                    color = (0, 255, 0)

                cv2.line(frame, hip, shoulder, color, 4)
                cv2.line(frame, shoulder, ear, color, 4)
                for pt in [hip, shoulder, ear]:
                    cv2.circle(frame, pt, 7, (255, 255, 255), -1)
                    cv2.circle(frame, pt, 5, color, -1)

                cv2.putText(frame, f"Torso: {torso_angle} deg (max {max_torso})", (15, 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                cv2.putText(frame, f"Neck:  {neck_angle} deg (max {max_neck})", (15, 65),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            else:
                status = "Сядьте боком, чтобы было видно ухо, плечо и бедро"

        return frame, is_bad_posture, status
