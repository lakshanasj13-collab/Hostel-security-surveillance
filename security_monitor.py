import cv2
import os
import json
import csv
import time
from datetime import datetime
import numpy as np
import tkinter as tk
from tkinter import messagebox

# ----------------- CONFIGURATION & PATHS -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
STUDENTS_FILE = os.path.join(BASE_DIR, "students.json")
TRAINER_FILE = os.path.join(BASE_DIR, "trainer.yml")
SERVER_LOG_FILE = os.path.join(BASE_DIR, "server_logs.csv")

os.makedirs(DATASET_DIR, exist_ok=True)

# Initialize CSV log file with header if it doesn't exist
if not os.path.exists(SERVER_LOG_FILE):
    with open(SERVER_LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Student_ID", "Name", "Department", "Room_No", "Status"])

# ----------------- DATA HELPERS -----------------
def load_students():
    """Load registered student profiles from JSON."""
    if os.path.exists(STUDENTS_FILE):
        try:
            with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_students(students_dict):
    """Save student profiles to JSON."""
    with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(students_dict, f, indent=4)

def append_server_log(student_id, name, dept, room, status):
    """Record an entry update in the server database/log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SERVER_LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, student_id, name, dept, room, status])
    print(f"\n[SERVER UPDATED] Time: {timestamp} | Student: {name} | Dept: {dept} | Room: {room} | Status: {status}")
    return timestamp

# ----------------- FACE RECOGNITION HELPERS -----------------
def augment_face_samples(gray_face):
    """Generate multiple variations of the face for high LBPH accuracy."""
    face_resized = cv2.resize(gray_face, (200, 200))
    face_eq = cv2.equalizeHist(face_resized)
    samples = [face_eq, cv2.flip(face_eq, 1)]
    (h, w) = face_eq.shape
    center = (w // 2, h // 2)

    # Slight rotations
    for angle in [-8, 8]:
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        samples.append(cv2.warpAffine(face_eq, M, (w, h), borderMode=cv2.BORDER_REPLICATE))

    # Brightness shifts
    for gamma in [0.85, 1.15]:
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
        samples.append(cv2.LUT(face_eq, table))

    return samples

def retrain_model():
    """Train LBPH recognizer on all faces in the dataset directory."""
    faces = []
    labels = []

    for user_folder in os.listdir(DATASET_DIR):
        user_path = os.path.join(DATASET_DIR, user_folder)
        if os.path.isdir(user_path) and user_folder.startswith("user_"):
            try:
                user_id = int(user_folder.split("_")[1])
            except ValueError:
                continue

            for img_name in os.listdir(user_path):
                img_path = os.path.join(user_path, img_name)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    faces.append(img)
                    labels.append(user_id)

    if faces and labels:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(faces, np.array(labels))
        recognizer.write(TRAINER_FILE)
        return recognizer
    return None

def load_recognizer():
    """Load existing model or return None."""
    if os.path.exists(TRAINER_FILE):
        try:
            r = cv2.face.LBPHFaceRecognizer_create()
            r.read(TRAINER_FILE)
            return r
        except Exception:
            return None
    return None

# ----------------- POPUP DIALOGS -----------------
def popup_registration(gray_face):
    """
    Popup dialog for a newly detected person:
    Asks for Name, Dept, Room No.
    Entry time is automatically filled.
    """
    result = {"saved": False, "id": None, "name": "", "dept": "", "room": ""}
    auto_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    root = tk.Tk()
    root.title("Hostel Security — New Person Registration")
    root.geometry("420x350")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    # Center window
    root.eval('tk::PlaceWindow . center')

    # Styling
    bg_color = "#f4f6f9"
    root.configure(bg=bg_color)

    title_lbl = tk.Label(root, text="New Person Detected — Registration", font=("Segoe UI", 12, "bold"), bg=bg_color, fg="#1a202c")
    title_lbl.pack(pady=(15, 10))

    frame = tk.Frame(root, bg=bg_color)
    frame.pack(padx=20, pady=5, fill="x")

    # Auto Entry Time
    tk.Label(frame, text="Entry Time (Auto):", font=("Segoe UI", 9, "bold"), bg=bg_color, fg="#4a5568").grid(row=0, column=0, sticky="w", pady=4)
    time_entry = tk.Entry(frame, font=("Segoe UI", 9), width=28)
    time_entry.insert(0, auto_time)
    time_entry.config(state="readonly")
    time_entry.grid(row=0, column=1, pady=4, padx=5)

    # Name
    tk.Label(frame, text="Full Name:", font=("Segoe UI", 9, "bold"), bg=bg_color, fg="#4a5568").grid(row=1, column=0, sticky="w", pady=6)
    name_entry = tk.Entry(frame, font=("Segoe UI", 10), width=28)
    name_entry.grid(row=1, column=1, pady=6, padx=5)
    name_entry.focus_set()

    # Department
    tk.Label(frame, text="Department:", font=("Segoe UI", 9, "bold"), bg=bg_color, fg="#4a5568").grid(row=2, column=0, sticky="w", pady=6)
    dept_entry = tk.Entry(frame, font=("Segoe UI", 10), width=28)
    dept_entry.grid(row=2, column=1, pady=6, padx=5)

    # Room No
    tk.Label(frame, text="Room No:", font=("Segoe UI", 9, "bold"), bg=bg_color, fg="#4a5568").grid(row=3, column=0, sticky="w", pady=6)
    room_entry = tk.Entry(frame, font=("Segoe UI", 10), width=28)
    room_entry.grid(row=3, column=1, pady=6, padx=5)

    status_lbl = tk.Label(root, text="", font=("Segoe UI", 9), bg=bg_color, fg="#e53e3e")
    status_lbl.pack(pady=4)

    def on_submit():
        name = name_entry.get().strip()
        dept = dept_entry.get().strip()
        room = room_entry.get().strip()

        if not name or not dept or not room:
            status_lbl.config(text="Please fill in all fields (Name, Dept, Room No)!")
            return

        students = load_students()
        # Create a new unique integer ID
        existing_ids = [int(k) for k in students.keys() if k.isdigit()]
        new_id = (max(existing_ids) + 1) if existing_ids else 1

        students[str(new_id)] = {
            "name": name,
            "dept": dept,
            "room": room,
            "registered_at": auto_time
        }
        save_students(students)

        # Save face image samples
        user_folder = os.path.join(DATASET_DIR, f"user_{new_id}")
        os.makedirs(user_folder, exist_ok=True)
        augmented = augment_face_samples(gray_face)
        for idx, sample in enumerate(augmented):
            cv2.imwrite(os.path.join(user_folder, f"sample_{idx}.jpg"), sample)

        # Update Server Log with the initial registration & entry time
        append_server_log(new_id, name, dept, room, "First-Time Registration & Entry")

        result["saved"] = True
        result["id"] = new_id
        result["name"] = name
        result["dept"] = dept
        result["room"] = room
        root.destroy()

    def on_cancel():
        root.destroy()

    btn_frame = tk.Frame(root, bg=bg_color)
    btn_frame.pack(pady=10)

    submit_btn = tk.Button(btn_frame, text="Register & Save", bg="#2b6cb0", fg="white", font=("Segoe UI", 9, "bold"), padx=12, pady=5, command=on_submit, relief="flat", cursor="hand2")
    submit_btn.pack(side="left", padx=8)

    cancel_btn = tk.Button(btn_frame, text="Cancel", bg="#718096", fg="white", font=("Segoe UI", 9), padx=12, pady=5, command=on_cancel, relief="flat", cursor="hand2")
    cancel_btn.pack(side="left", padx=8)

    root.mainloop()
    return result

def popup_verification(student_id, student_info):
    """
    Popup dialog when an existing person is recognized:
    Shows their saved details and asks if they are correct.
    Server is updated ONLY if 'Yes' is clicked.
    """
    confirmed = {"status": False, "time": ""}
    auto_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    root = tk.Tk()
    root.title("Hostel Security — Verify Identity")
    root.geometry("420x330")
    root.resizable(False, False)
    root.attributes("-topmost", True)
    root.eval('tk::PlaceWindow . center')

    bg_color = "#f7fafc"
    root.configure(bg=bg_color)

    title_lbl = tk.Label(root, text="Recognized Person — Verify Details", font=("Segoe UI", 12, "bold"), bg=bg_color, fg="#2b6cb0")
    title_lbl.pack(pady=(15, 8))

    box_frame = tk.Frame(root, bg="white", highlightbackground="#cbd5e0", highlightthickness=1, padx=15, pady=10)
    box_frame.pack(padx=25, pady=8, fill="x")

    def make_row(parent, label, value, row_idx):
        tk.Label(parent, text=label, font=("Segoe UI", 9, "bold"), bg="white", fg="#4a5568", anchor="w").grid(row=row_idx, column=0, sticky="w", pady=3)
        tk.Label(parent, text=value, font=("Segoe UI", 9), bg="white", fg="#1a202c", anchor="w").grid(row=row_idx, column=1, sticky="w", padx=10, pady=3)

    make_row(box_frame, "Name:", student_info.get("name", "Unknown"), 0)
    make_row(box_frame, "Department:", student_info.get("dept", "Unknown"), 1)
    make_row(box_frame, "Room No:", student_info.get("room", "Unknown"), 2)
    make_row(box_frame, "Entry Time (Now):", auto_time, 3)

    prompt_lbl = tk.Label(root, text="Are these details correct for this person?", font=("Segoe UI", 10, "bold"), bg=bg_color, fg="#2d3748")
    prompt_lbl.pack(pady=(10, 5))

    def on_yes():
        # ONLY update server if confirmed
        append_server_log(
            student_id,
            student_info.get("name"),
            student_info.get("dept"),
            student_info.get("room"),
            "Verified Entry (Server Updated)"
        )
        confirmed["status"] = True
        confirmed["time"] = auto_time
        root.destroy()

    def on_no():
        print(f"\n[ALERT] Verification DECLINED by user for {student_info.get('name')}. Server was NOT updated.")
        root.destroy()

    btn_frame = tk.Frame(root, bg=bg_color)
    btn_frame.pack(pady=10)

    yes_btn = tk.Button(btn_frame, text="✔ Yes, Details Correct", bg="#38a169", fg="white", font=("Segoe UI", 9, "bold"), padx=12, pady=5, command=on_yes, relief="flat", cursor="hand2")
    yes_btn.pack(side="left", padx=8)

    no_btn = tk.Button(btn_frame, text="✖ No, Incorrect", bg="#e53e3e", fg="white", font=("Segoe UI", 9, "bold"), padx=12, pady=5, command=on_no, relief="flat", cursor="hand2")
    no_btn.pack(side="left", padx=8)

    root.mainloop()
    return confirmed

# ----------------- MAIN MONITORING LOOP -----------------
def main():
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    recognizer = load_recognizer()
    students = load_students()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot access webcam (cv2.VideoCapture(0)). Check camera connection.")
        return

    print("=" * 65)
    print("       HOSTEL SECURITY MONITORING SYSTEM STARTED")
    print("=" * 65)
    print(f"Registered Students : {len(students)}")
    print("Controls:")
    print(" - Look into camera to register or verify identity")
    print(" - Press 'q' on video window to quit")
    print(" - Press 'r' to manually register current face")
    print("=" * 65)

    cooldown_until = 0.0
    status_message = "Monitoring active..."
    status_color = (0, 255, 0)
    status_expire = 0.0

    # Face stability detection counter
    consecutive_detection = 0
    candidate_id = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Flip horizontally for natural mirror display
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(90, 90))

        current_time_sec = time.time()
        in_cooldown = current_time_sec < cooldown_until

        detected_candidate = None
        detected_crop = None
        box_coords = None

        for (x, y, w, h) in faces:
            face_roi_gray = gray[y:y+h, x:x+w]
            label_text = "Person Detected"
            color = (0, 165, 255) # Orange default

            if recognizer is not None and len(students) > 0:
                face_resized = cv2.resize(face_roi_gray, (200, 200))
                user_id, confidence = recognizer.predict(cv2.equalizeHist(face_resized))

                # LBPH: confidence < 60 indicates recognized match (strict threshold prevents strangers from matching)
                if confidence < 60 and str(user_id) in students:
                    student_info = students[str(user_id)]
                    label_text = f"{student_info['name']} ({student_info['room']})"
                    color = (0, 255, 0) # Green for recognized
                    detected_candidate = ("known", user_id, student_info)
                else:
                    label_text = "Unknown Person (New)"
                    color = (0, 0, 255) # Red for unknown
                    detected_candidate = ("unknown", None, None)
            else:
                label_text = "New Student (Unregistered)"
                color = (0, 215, 255) # Gold
                detected_candidate = ("unknown", None, None)

            # Draw bounding box and label
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.rectangle(frame, (x, y - 28), (x + w, y), color, cv2.FILLED)
            cv2.putText(frame, label_text, (x + 6, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

            detected_crop = face_roi_gray
            box_coords = (x, y, w, h)
            break # Focus on primary face

        # Top Information Banner
        header = f"Hostel Security | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        cv2.putText(frame, header, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        # Status Notification Banner
        if current_time_sec < status_expire:
            cv2.putText(frame, status_message, (15, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        else:
            cv2.putText(frame, "Press 'q' to quit | 'r' to register manually", (15, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        # Trigger logic with stability counter
        if detected_candidate and not in_cooldown and detected_crop is not None:
            c_type, c_id, c_info = detected_candidate
            candidate_key = (c_type, c_id)
            if candidate_key == candidate_id:
                consecutive_detection += 1
            else:
                candidate_id = candidate_key
                consecutive_detection = 1

            # Require face to be steady for ~6 frames before opening popup
            if consecutive_detection >= 6:
                consecutive_detection = 0
                cv2.imshow("Hostel Security Monitoring", frame)
                cv2.waitKey(1)

                if c_type == "known":
                    # Prompt identity verification
                    result = popup_verification(c_id, c_info)
                    if result["status"]:
                        status_message = f"SERVER UPDATED: {c_info['name']} logged in at {result['time']}!"
                        status_color = (0, 255, 0)
                    else:
                        status_message = "VERIFICATION CANCELLED: Server NOT updated."
                        status_color = (0, 0, 255)
                    status_expire = time.time() + 4.0
                    cooldown_until = time.time() + 5.0

                elif c_type == "unknown":
                    # Prompt new registration
                    reg_result = popup_registration(detected_crop)
                    if reg_result["saved"]:
                        status_message = f"REGISTERED & UPDATED: {reg_result['name']} saved to server!"
                        status_color = (0, 255, 0)
                        # Retrain model with new person added
                        recognizer = retrain_model()
                        students = load_students()
                    else:
                        status_message = "Registration cancelled."
                        status_color = (0, 165, 255)
                    status_expire = time.time() + 4.0
                    cooldown_until = time.time() + 5.0
        else:
            if not detected_candidate:
                consecutive_detection = 0
                candidate_id = None

        cv2.imshow("Hostel Security Monitoring", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r') and detected_crop is not None:
            # Manual registration trigger
            reg_result = popup_registration(detected_crop)
            if reg_result["saved"]:
                status_message = f"REGISTERED: {reg_result['name']} saved to server!"
                status_color = (0, 255, 0)
                recognizer = retrain_model()
                students = load_students()
            status_expire = time.time() + 4.0
            cooldown_until = time.time() + 5.0

    cap.release()
    cv2.destroyAllWindows()
    print("\n[INFO] Monitoring stopped cleanly.")

if __name__ == "__main__":
    main()
