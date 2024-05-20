import sys
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLabel, QLCDNumber
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import QTimer, QSize, Qt

class MyButton(QPushButton):
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            event.ignore()
        else:
            super().keyPressEvent(event)

class VideoStreamWidget(QWidget):
    def __init__(self, video_source, parent=None):
        super().__init__(parent)
        self.video_source = video_source
        self.video_capture = cv2.VideoCapture(self.video_source)
        
        if not self.video_capture.isOpened():
            print(f"Error: Unable to open video source {self.video_source}")
            return

        self.image_label = QLabel(self)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.image_label)
        self.setLayout(self.layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.video_capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(image))

    def closeEvent(self, event):
        self.video_capture.release()

    def stop(self):
        self.timer.stop()
    
    def start(self):
        self.timer.start(30)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Car Control")
        self.resize(500, 500)

        self.car_running = False  # Car status
        self.speed = 0  # Default speed
        self.is_brake_pressed = False
        self.is_hard_braking = False

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        self.cameras_layout = QHBoxLayout()
        self.front_camera_widget = VideoStreamWidget(video_source=r'C:\FPT\DLP302m\Project\Otosaigon - Test camera hành trình Polaroid S205W chế độ 4K 24 fps ban ngày.mp4')
        self.rear_camera_widget = VideoStreamWidget(video_source=r'C:\FPT\DLP302m\Project\Video hành trình Full HD ban ngày Camera sau UTOUR.mp4')
        self.cameras_layout.addWidget(self.front_camera_widget)
        self.cameras_layout.addWidget(self.rear_camera_widget)

        self.main_layout.addLayout(self.cameras_layout)

        self.speed_lcd = QLCDNumber()
        self.speed_lcd.setDigitCount(3)
        self.speed_lcd.display(self.speed)
        self.speed_lcd.setStyleSheet("background-color: black; color: red;")
        self.main_layout.addWidget(self.speed_lcd)

        self.control_layout = QHBoxLayout()
        self.main_layout.addLayout(self.control_layout)

        self.turn_left_button = MyButton()
        left_icon = QIcon(QPixmap(r'C:\FPT\DLP302m\Project\Left_button.png'))
        self.turn_left_button.setIcon(left_icon)
        self.turn_left_button.setIconSize(QSize(100, 100))
        self.turn_left_button.clicked.connect(self.turn_left)
        self.control_layout.addWidget(self.turn_left_button)

        self.turn_right_button = MyButton()
        right_icon = QIcon(QPixmap(r'C:\FPT\DLP302m\Project\Right_button.png'))
        self.turn_right_button.setIcon(right_icon)
        self.turn_right_button.setIconSize(QSize(100, 100))
        self.turn_right_button.clicked.connect(self.turn_right)
        self.control_layout.addWidget(self.turn_right_button)

        self.brake_button = MyButton()
        brake_icon = QIcon(QPixmap(r'C:\FPT\DLP302m\Project\Brake_button.png'))
        self.brake_button.setIcon(brake_icon)
        self.brake_button.setIconSize(QSize(100, 100))
        self.brake_button.pressed.connect(self.brake_pressed)
        self.brake_button.released.connect(self.brake_released)
        self.main_layout.addWidget(self.brake_button, alignment=Qt.AlignCenter)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_buttons)
        self.timer.start(500)

        self.left_blinking = False
        self.right_blinking = False
        self.blink_state = False
        self.brake_blinking = False
        self.brake_just_clicked = False

        # Adding Start and Stop buttons
        self.start_button = QPushButton("Start")
        self.start_button.setIcon(QIcon(QPixmap(r'C:\FPT\DLP302m\Project\Start_button.png')))
        self.start_button.setIconSize(QSize(100, 100))
        self.start_button.clicked.connect(self.start_car)
        self.main_layout.addWidget(self.start_button, alignment=Qt.AlignCenter)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setIcon(QIcon(QPixmap(r'C:\FPT\DLP302m\Project\Stop_button.png')))
        self.stop_button.setIconSize(QSize(100, 100))
        self.stop_button.clicked.connect(self.stop_car)
        self.main_layout.addWidget(self.stop_button, alignment=Qt.AlignCenter)

        self.acceleration_timer = QTimer()
        self.acceleration_timer.timeout.connect(self.accelerate)
        self.deceleration_timer = QTimer()
        self.deceleration_timer.timeout.connect(self.decelerate)

    def accelerate(self):
        if self.speed < 50:
            self.speed += 1
            self.speed_lcd.display(self.speed)
        else:
            self.acceleration_timer.stop()

    def decelerate(self):
        if self.speed > 0:
            self.speed -= 1
            self.speed_lcd.display(self.speed)
        else:
            self.deceleration_timer.stop()

    def turn_left(self):
        if self.car_running:
            self.left_blinking = not self.left_blinking

    def turn_right(self):
        if self.car_running:
            self.right_blinking = not self.right_blinking

    def brake_pressed(self):
        if self.car_running:
            self.is_brake_pressed = True
            self.is_hard_braking = True

    def brake_released(self):
        if self.car_running:
            self.is_brake_pressed = False
            self.is_hard_braking = False
            self.brake_blinking = False
            self.brake_just_clicked = True

    def update_buttons(self):
        if self.car_running:
            self.blink_state = not self.blink_state

            if self.left_blinking:
                color = "lightgreen" if self.blink_state else ""
                self.turn_left_button.setStyleSheet(f"background-color: {color}")
            else:
                self.turn_left_button.setStyleSheet("")

            if self.right_blinking:
                color = "lightgreen" if self.blink_state else ""
                self.turn_right_button.setStyleSheet(f"background-color: {color}")
            else:
                self.turn_right_button.setStyleSheet("")

            if self.is_brake_pressed:
                self.brake_button.setStyleSheet("background-color: red")
            else:
                if self.brake_just_clicked:
                    self.brake_button.setStyleSheet("background-color: red")
                    self.brake_just_clicked = False
                else:
                    self.brake_button.setStyleSheet("")
        else:
            self.turn_left_button.setStyleSheet("")
            self.turn_right_button.setStyleSheet("")
            self.brake_button.setStyleSheet("")
            self.stop_car()

    def keyPressEvent(self, event):
        if self.car_running:
            if event.key() == Qt.Key_A:
                self.turn_left()
            elif event.key() == Qt.Key_D:
                self.turn_right()
            elif event.key() == Qt.Key_S:
                self.brake_pressed()

    def keyReleaseEvent(self, event):
        if self.car_running:
            if event.key() == Qt.Key_S:
                self.brake_released()

    def start_car(self):
        self.car_running = True
        self.acceleration_timer.start(100)
        self.front_camera_widget.start()
        self.rear_camera_widget.start()
        print("Car started")

    def stop_car(self):
        self.car_running = False
        self.deceleration_timer.start(100)
        self.front_camera_widget.stop()
        self.rear_camera_widget.stop()
        print("Car stopped")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())