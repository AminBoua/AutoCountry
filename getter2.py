import tkinter as tk
from PIL import ImageGrab, Image
import pytesseract
import threading
from pynput import mouse
from mss import mss
import time

# Define the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path

root = tk.Tk()
root.geometry('200x200')

monitor = {"top": 161, "left": 200, "width": 540, "height": 80}  # Define the area for screen capture

click_area_coords = tk.StringVar(value="")  # Initialize with an empty string
click_area = None
listener = None
timer = tk.StringVar()  # Add this line
timer.set("Select a click area first")

def select_area(color, area_var):
    global overlay
    overlay = tk.Toplevel(root)
    overlay.geometry("{0}x{1}+0+0".format(overlay.winfo_screenwidth(), overlay.winfo_screenheight()))
    overlay.attributes('-alpha', 0.3)
    overlay.attributes("-fullscreen", True)
    overlay.lift()
    overlay.attributes("-topmost", True)

    canvas = tk.Canvas(overlay, cursor="cross", bd=0, highlightthickness=0)
    canvas.pack(fill='both', expand=True)

    start_x, start_y, rect = None, None, None

    def on_mouse_down(event):
        nonlocal start_x, start_y
        start_x = event.x
        start_y = event.y

    def on_mouse_move(event):
        nonlocal rect
        if start_x and start_y:
            if rect:
                canvas.delete(rect)
            rect = canvas.create_rectangle(start_x, start_y, event.x, event.y, outline=color)

    def on_mouse_up(event):
        nonlocal start_x, start_y, rect
        if rect:
            canvas.delete(rect)
        end_x = event.x
        end_y = event.y
        overlay.destroy()
        area_var.set((start_x, start_y, end_x, end_y))
        root.after(0, enable_start_button)  # schedule 'enable_start_button' to run in the main thread

    canvas.bind("<Button-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_move)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)

    overlay.mainloop()

def start_click_area_selection():
    select_area('green', click_area_coords)

def enable_start_button():
    if click_area_coords.get():
        button1.configure(state='normal')  # Enable 'Start Program' button after selecting an area
        timer.set("Ready to start")

def countdown(seconds):
    for i in range(seconds, 0, -1):
        timer.set(f"Starting in {i} seconds...")
        time.sleep(1)
    timer.set("Started!")

def start_program():
    countdown_thread = threading.Thread(target=countdown, args=(5,))
    countdown_thread.start()

    global click_area, listener
    click_area = click_area_coords.get()

    if click_area:
        listener = mouse.Listener(on_click=on_mouse_click)
        listener.start()

def read_text():
    sct = mss()
    screenshot = sct.grab(monitor)
    img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
    text = pytesseract.image_to_string(img)
    return text.strip()

def on_mouse_click(x, y, button, pressed):
    global click_area
    if pressed and click_area:
        click_x1, click_y1, click_x2, click_y2 = map(int, click_area.strip('()').split(','))
        if click_x1 <= x <= click_x2 and click_y1 <= y <= click_y2:
            threading.Thread(target=read_and_print_text, args=(x, y)).start()

def read_and_print_text(x, y):
    text = read_text()
    print(f"'{text}' at ({x}, {y})")

    with open('results.txt', 'a') as f:
        f.write(f"'{text}': ({x}, {y}),\n")

def on_close():
    global listener
    if listener:
        listener.stop()
    root.destroy()

button1 = tk.Button(root, text='Start Program', command=start_program, state='disabled')
button1.pack()

button2 = tk.Button(root, text='Select Click Area', command=start_click_area_selection)
button2.pack()

label = tk.Label(root, textvariable=timer)
label.pack()

root.protocol("WM_DELETE_WINDOW", on_close)
root.attributes('-topmost', 1)
root.mainloop()
