import os
import queue
import subprocess
import threading
import time
import vlc
import sys
import tkinter as tk
from tkinter import ttk


def get_active_window():
    window_name = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'], stdout=subprocess.PIPE)
    return window_name.stdout.decode('utf-8').strip('\n')


def get_mouse_location():
    window_name = subprocess.run(['xdotool', 'getmouselocation'], stdout=subprocess.PIPE)
    return window_name.stdout.decode('utf-8').strip('\n')


def ocr(region, name):
    file = f'/run/user/{os.getuid()}/rs3helper-{name}.bmp'
    subprocess.run(['maim', '-g', region, file])
    cmd = subprocess.run(['tesseract', file, 'stdout'], stdout=subprocess.PIPE)
    return cmd.stdout.decode('utf-8')


def get_item_level(ocr_text):
    s = ocr_text.rfind('Your Augmented crystal pickaxe')
    if s == -1:
        return -1

    line = ocr_text[s:s+70]
    segments = line.split(' ')
    level = ''.join(c for c in segments[len(segments) - 1] if c.isdigit())

    if level == '12':
        s = ocr_text.rfind('You drain the')
        if s != -1:
            return 1

    return int(level)


def get_screen_region():
    screen_region = subprocess.run(['slop'], stdout=subprocess.PIPE)
    screen_region = screen_region.stdout.decode('utf-8').strip('\n')

    with open('region.txt', 'w') as f:
        f.write(screen_region)

    return screen_region


def active_checker(thread_cmd_q: queue.Queue, output_q: queue.Queue):
    alert = vlc.MediaPlayer(f"file://{sys.path[0]}/alert.mp3")
    title = 'RuneScape'
    last_unix = time.time()
    mouse_pos = ''

    execute = True
    mute = False
    while True:
        try:
            cmd = thread_cmd_q.get(block=False)
            if cmd == 'pause':
                execute = not execute
            elif cmd == 'mute':
                mute = not mute
            else:
                return
        except queue.Empty:
            pass

        if not execute:
            last_unix = time.time()
            time.sleep(1)
            continue

        if get_active_window() == title:
            new_pos = get_mouse_location()
            if mouse_pos != new_pos:
                mouse_pos = new_pos
                last_unix = time.time()

        output_q.put(time.time() - last_unix)

        if time.time() - last_unix >= 840 and mute is False:
            alert.play()
            time.sleep(0.1)
            alert.stop()

        time.sleep(1)


def item_lvl_checker(region, thread_cmd_q: queue.Queue, region_q: queue.Queue, output_q: queue.Queue):
    alert = vlc.MediaPlayer(f"file://{sys.path[0]}/alert.mp3")
    execute = True
    item_lvl = 0
    while True:
        if not region_q.empty():
            region = region_q.get(block=False)

        if not thread_cmd_q.empty():
            cmd = thread_cmd_q.get(block=False)
            if cmd == 'pause':
                execute = False
            elif cmd == 'resume':
                execute = True
            else:
                return

        if not execute:
            time.sleep(10)
            continue

        text = ocr(region, 'item_lvl')
        new_lvl = get_item_level(text)

        if new_lvl > -1:
            item_lvl = new_lvl

        if item_lvl == 12:
            alert.play()
            time.sleep(0.1)
            alert.stop()

        output_q.put(item_lvl)
        time.sleep(10)


def health_checker(region, thread_cmd_q: queue.Queue, region_q: queue.Queue, output_q: queue.Queue):
    alert = vlc.MediaPlayer(f"file://{sys.path[0]}/alert.mp3")
    execute = True
    health = 1
    max_health = 100
    while True:
        if not region_q.empty():
            region = region_q.get(block=False)

        if not thread_cmd_q.empty():
            cmd = thread_cmd_q.get(block=False)
            if cmd == 'pause':
                execute = False
            elif cmd == 'resume':
                execute = True
            else:
                return

        if not execute:
            time.sleep(10)
            continue

        text = ocr(region, 'health')
        text = text.strip('\n')
        text = text.replace(',', '')
        text = text.replace(' ', '')
        text = text.replace('°', '')
        print(text)
        h = text.split('/')
        try:
            health = int(h[0])
            max_health = int(h[1])
        except ValueError:
            pass

        if health / max_health < 0.7:
            alert.play()
            time.sleep(0.1)
            alert.stop()

        output_q.put(health / max_health)
        print(health / max_health)
        print(health)
        print(max_health)
        time.sleep(2)



def on_region_selected_button_clicked():
    new_region = get_screen_region()
    region_selected['text'] = new_region
    health_region_queue.put(new_region)



def update_afk_progressbar():
    try:
        afk_progressbar['value'] = int(afk_queue.get(block=False))
    except queue.Empty:
        pass
    root.after(ms=1000, func=update_afk_progressbar)



def update_health_progressbar():
    try:
        val = health_queue.get(block=False)
        health_progressbar['value'] = val * 100
    except queue.Empty:
        pass
    root.after(ms=1000, func=update_health_progressbar)


if __name__ in {"__main__", "__mp_main__"}:
    # Load Previous Region
    with open(f'{sys.path[0]}/region.txt', 'r') as f:
        region_txt = f.readline()

    # Create Queues
    afk_queue = queue.Queue()
    afk_cmd_queue = queue.Queue()
    health_queue = queue.Queue()
    health_region_queue = queue.Queue()
    health_cmd_queue = queue.Queue()

    # Create Threads
    threading.Thread(target=active_checker, args=(afk_cmd_queue, afk_queue)).start()
    threading.Thread(target=health_checker,
                     args=(region_txt, health_cmd_queue, health_region_queue, health_queue)).start()

    # Start GUI
    root = tk.Tk()
    root.title('RS3Helper')

    # Labels
    afk_label = tk.Label(root, text="AFK:")
    health_label = tk.Label(root, text="Health:")
    region_selected = tk.Label(root, text=region_txt)

    # Progress Bars
    afk_progressbar = ttk.Progressbar(root, orient='horizontal', length=250, mode='determinate', maximum=840)
    health_progressbar = ttk.Progressbar(root, orient='horizontal', length=250, mode='determinate', maximum=100)

    # Button
    health_calibrate = tk.Button(root, text="Select Region", command=on_region_selected_button_clicked)

    # Grid
    afk_label.grid(row=0, column=0, sticky=tk.W, pady=2)
    afk_progressbar.grid(row=0, column=1, sticky=tk.W, pady=2)
    health_label.grid(row=1, column=0, sticky=tk.W, pady=2)
    health_progressbar.grid(row=1, column=1, sticky=tk.W, pady=2)
    health_calibrate.grid(row=2, column=0, sticky=tk.W, pady=2)
    region_selected.grid(row=2, column=1, sticky=tk.W, pady=2)

    # Run Events
    update_afk_progressbar()
    update_health_progressbar()

    root.mainloop()
    afk_cmd_queue.put('stop')
    health_cmd_queue.put('stop')
