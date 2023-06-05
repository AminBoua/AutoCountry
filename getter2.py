import tkinter as tk
from PIL import ImageGrab, Image
import pytesseract
import threading
from pynput import mouse
from mss import mss
import time

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

root = tk.Tk()
root.geometry('200x200')

monitor = {"top": 161, "left": 200, "width": 540, "height": 80}

click_area_coords = tk.StringVar(value="")
click_area = None
listener = None
timer = tk.StringVar()
timer.set("Select a click area first")

# Create a lock for thread synchronization
lock = threading.Lock()

def select_area(color):
    global overlay
    overlay = tk.Toplevel(root)
    overlay.geometry("{0}x{1}+0+0".format(overlay.winfo_screenwidth(), overlay.winfo_screenheight()))
    overlay.attributes('-alpha', 0.3)
    overlay.attributes("-fullscreen", True)
    overlay.lift()
    overlay.attributes("-topmost", True)

    canvas = tk.Canvas(overlay, cursor="cross", bd=0, highlightthickness=0)
    canvas.pack(fill='both', expand=True)

    rect = None

    def on_mouse_down(event):
        nonlocal rect
        if rect:
            canvas.delete(rect)
        rect = canvas.create_rectangle(event.x, event.y, event.x+1010, event.y+580, outline=color)

    def overlay_key_down(event):
        nonlocal rect
        if event.keysym == 'Return' and rect:
            coords = canvas.coords(rect)
            overlay.destroy()
            click_area_coords.set((coords[0], coords[1], coords[2], coords[3]))
            root.after(0, enable_start_button)

    canvas.bind("<Button-1>", on_mouse_down)
    overlay.bind("<Key>", overlay_key_down)

def start_click_area_selection():
    select_area('green')

def enable_start_button():
    if click_area_coords.get():
        button1.configure(state='normal')
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
        print(f"Selected click area: {click_area}")
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
        click_x1, click_y1, click_x2, click_y2 = map(int, map(float, click_area.strip('()').split(',')))
        if click_x1 <= x <= click_x2 and click_y1 <= y <= click_y2:
            with lock:
                threading.Thread(target=read_and_print_text, args=(x, y)).start()

def on_close():
    global listener
    if listener:
        listener.stop()
    root.destroy()

button1 = tk.Button(root, text='Start Program', command=start_program, state='disabled')
button1.pack(fill='both', expand=True)

button2 = tk.Button(root, text='Select Click Area', command=start_click_area_selection)
button2.pack(fill='both', expand=True)

label = tk.Label(root, textvariable=timer)
label.pack(fill='both', expand=True)

results_text = tk.Text(root, height=5, width=40)
results_text.pack(fill='both', expand=True)

def read_and_print_text(x, y):
    with lock:
        text = read_text()
        results_text.insert(tk.END, f"'{text}' at ({x}, {y})\n")
        results_text.see(tk.END)  # Scroll to the bottom

        # Save the last 5 results
        lines = results_text.get("1.0", tk.END).splitlines()
        if len(lines) > 6:
            results_text.delete("1.0", "1.0 lineend+1c")

        with open('results.txt', 'a') as f:
            f.write(f"'{text}': ({x}, {y}),\n")

        print(f"'{text}' at ({x}, {y})")  # Print the result in the command prompt

root.protocol("WM_DELETE_WINDOW", on_close)
root.attributes('-topmost', 1)
root.mainloop()
