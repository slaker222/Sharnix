import os
import sys
import time
import subprocess
import threading
import json
import math
import requests
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser
import base64
import urllib.parse
import shutil
try:
    from pynput import keyboard
except ImportError:
    keyboard = None
    print('Warning: pynput not installed. Global hotkeys disabled.')
try:
    import pyscreenshot as ImageGrab
except ImportError:
    print('Warning: pyscreenshot is not installed. Screenshot functionality may not work.')
    ImageGrab = None
from PIL import Image, ImageTk, ImageDraw, ImageOps, ImageFilter
try:
    from PIL import ImageFont
except ImportError:
    ImageFont = None
COLOR_BG_DARK = '#2e3436'
COLOR_FG_LIGHT = '#eeeeec'
COLOR_ACCENT = '#3465a4'
COLOR_DANGER = '#cc0000'
COLOR_CONTROL_BG = '#3d4547'
COLOR_BORDER = '#555753'
FONT_MAIN = ('Cantarell', 10)
FONT_HEADER = ('Cantarell', 14, 'bold')
FONT_SMALL = ('Cantarell', 9)
BORDER_RADIUS_LARGE = 12
BORDER_RADIUS_SMALL = 6
THUMB_SIZE = 200
THUMB_COLUMNS = 3
ICON_BRUSH = '✍'
ICON_ARROW = '➡'
ICON_SELECT = '🔳'
ICON_UNDO = '↩️'
ICON_CLOSE = '❌'
ICON_SAVE = '💾'
ICON_COPY = '📋'
ICON_FOLDER = '📁'
ICON_SETTINGS = '⚙'
ICON_EXIT = '👋'
ICON_TEXT = 'Aa'
ICON_BLUR = '🌫'
ICON_MOVE = '↔️'
ICON_FULLSCREEN = '🖼'

class Sharnix_Linux:

    def __init__(self):
        self.config_dir = Path.home() / '.config' / 'sharnix'
        self.config_file = self.config_dir / 'config.json'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.load_config()
        self.root = None
        self.gallery_canvas = None
        self.gallery_frame = None
        self.thumbnails = []
        self.viewer_window = None
        self.listener = None
        self.screenshot_in_progress = False
        self.screenshot_lock = threading.Lock()
        self.pending_screenshot = False
        self.pending_gui_calls = []

    def load_config(self):
        default_config = {'screenshot_dir': str(Path.home() / 'Pictures' / 'Screenshots' / 'sharnix'), 'upload_service': '', 'imgur_client_id': '', 'auto_copy': False, 'sound_enabled': True, 'hotkeys': {'fullscreen': 'alt+z', 'region': 'alt+s'}, 'hidden_files': [], 'warnings_shown': {'cloud_upload': False, 'ocr': False, 'ocr_translate': False}, 'first_launch': True, 'max_visible_screenshots': 25}
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    loaded_config.pop('_comment', None)
                    self.config = {**default_config, **loaded_config}
            except Exception:
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()
        self.config['hotkeys'] = {**default_config['hotkeys'], **self.config.get('hotkeys', {})}
        self.config['hidden_files'] = self.config.get('hidden_files', [])
        self.config['warnings_shown'] = {**default_config['warnings_shown'], **self.config.get('warnings_shown', {})}
        self.config['first_launch'] = self.config.get('first_launch', True)
        Path(self.config['screenshot_dir']).mkdir(parents=True, exist_ok=True)

    def show_first_launch_dialog(self):
        if not self.config.get('first_launch', True):
            return
        dialog = tk.Toplevel(self.root)
        dialog.title('Sharnix — information')
        dialog.configure(bg=COLOR_BG_DARK)
        dialog.geometry('650x720')
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)
        dialog.grab_set()
        main_frame = ttk.Frame(dialog, style='DarkFrame.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        title_label = ttk.Label(main_frame, text='⚠️ Sharnix is in development', font=('Cantarell', 17, 'bold'), foreground=COLOR_ACCENT, background=COLOR_BG_DARK)
        title_label.pack(pady=(0, 15))
        warning_text = 'Sharnix is in active development. Most bugs and issues will be fixed in future versions.\n\nTo correctly copy images to the clipboard, you need to install the xclip system utility.\n\nRun one of the commands below in the terminal, depending on your distribution.'
        warning_frame = ttk.Frame(main_frame, style='DarkFrame.TFrame')
        warning_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        warning_label = tk.Text(warning_frame, wrap=tk.WORD, font=('Cantarell', 15), bg=COLOR_BG_DARK, fg=COLOR_FG_LIGHT, relief=tk.FLAT, height=9, cursor='arrow')
        warning_label.pack(fill=tk.BOTH, expand=True)
        warning_label.insert('1.0', warning_text)
        warning_label.config(state='disabled')
        commands_label = ttk.Label(main_frame, text='🐧 Installation commands for different Linux distributions', font=('Cantarell', 12, 'bold'), foreground=COLOR_FG_LIGHT, background=COLOR_BG_DARK)
        commands_label.pack(pady=(10, 10), anchor='w')
        commands_frame = ttk.Frame(main_frame, style='DarkFrame.TFrame')
        commands_frame.pack(fill=tk.BOTH, expand=True)
        commands = [('Arch / Cashyos:', 'sudo pacman -S xclip'), ('Ubuntu / Debian / Mint:', 'sudo apt install xclip'), ('Fedora:', 'sudo dnf install xclip'), ('OpenSUSE:', 'sudo zypper install xclip')]
        for distro, cmd in commands:
            distro_label = ttk.Label(commands_frame, text=distro, font=('Cantarell', 10, 'bold'), foreground=COLOR_ACCENT, background=COLOR_BG_DARK)
            distro_label.pack(anchor='w', pady=(5, 2))
            cmd_frame = tk.Frame(commands_frame, bg=COLOR_CONTROL_BG, relief=tk.FLAT, bd=1)
            cmd_frame.pack(fill=tk.X, pady=(0, 10))
            cmd_label = tk.Label(cmd_frame, text=cmd, font=('Monospace', 10), bg=COLOR_CONTROL_BG, fg=COLOR_FG_LIGHT, anchor='w', padx=10, pady=5)
            cmd_label.pack(fill=tk.X)

            def copy_command(command=cmd):
                try:
                    process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    process.communicate(command.encode('utf-8'))
                except:
                    pass
            cmd_label.bind('<Button-1>', lambda e, cmd=cmd: copy_command(cmd))
            cmd_label.config(cursor='hand2')
        button_frame = ttk.Frame(main_frame, style='DarkFrame.TFrame')
        button_frame.pack(fill=tk.X, pady=(15, 0))

        def on_close():
            self.config['first_launch'] = False
            self.save_config()
            dialog.destroy()
        ttk.Button(button_frame, text="Got it, don't show this again", command=on_close, style='Accent.TButton').pack(side=tk.RIGHT)
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = dialog.winfo_screenwidth() // 2 - width // 2
        y = dialog.winfo_screenheight() // 2 - height // 2
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        dialog.wait_window()

    def safe_show_dialog(self, dialog_func, *args, **kwargs):
        try:
            self.root.after(0, lambda: dialog_func(*args, **kwargs))
        except:
            print(f'[DEBUG] Mainloop busy, queuing dialog for later')
            self.pending_gui_calls.append((dialog_func, args, kwargs))

    def _on_scroll_event(self, event):
        if not self.gallery_canvas:
            return
        if event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            self.gallery_canvas.yview_scroll(1, 'units')
        elif event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            self.gallery_canvas.yview_scroll(-1, 'units')
        return 'break'

    def save_config(self):
        try:
            config_with_comment = {'_comment': 'To apply the changes, save the file and restart Sharnix.'}
            config_with_comment.update(self.config)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_with_comment, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror('Save error', f'Failed to save settings: {e}')

    def upload_thread():
        try:
            if not os.path.exists(filepath):
                self.root.after(0, lambda: messagebox.showerror('Ошибка', f'File not found: {filepath}'))
                return
            upload_url = 'https://freeimage.host/json'
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 'Referer': 'https://freeimage.host/'}
            data = {'type': 'file', 'action': 'upload', 'source': 'file', 'key': 'freeimagehost', 'format': 'json'}
            with open(filepath, 'rb') as file:
                files = {'source': (os.path.basename(filepath), file, 'image/jpeg' if str(filepath).lower().endswith('.jpg') else 'image/png')}
                response = requests.post(upload_url, headers=headers, data=data, files=files, timeout=30)
                response.raise_for_status()
                result = response.json()
                if result.get('status_code') == 200 and result.get('status_txt') == 'OK':
                    image_link = result['image']['url']
                    try:
                        process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        process.communicate(image_link.encode('utf-8'))
                    except Exception as e:
                        print(f'Error copying to buffer: {e}')
                    self.root.after(0, lambda: self.show_upload_success_dialog(image_link))
                else:
                    error_message = result.get('error', 'Unknown loading error.')
                    self.root.after(0, lambda msg=error_message: messagebox.showerror('error', f'Loading error: {msg}'))
        except requests.exceptions.RequestException as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror('error', f'Network error: {err}'))
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror('error', f'Unexpected error: {err}'))
        threading.Thread(target=upload_thread, daemon=True).start()

    def show_upload_success_dialog(self, image_link):
        dialog = tk.Toplevel(self.root)
        dialog.title('Success')
        dialog.configure(bg=COLOR_BG_DARK)
        dialog.geometry('400x150')
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(dialog, text='Image uploaded!\nThe link has been copied to the clipboard:', font=FONT_MAIN, foreground=COLOR_FG_LIGHT, background=COLOR_BG_DARK).pack(pady=10)
        link_label = ttk.Label(dialog, text=image_link, font=FONT_SMALL, foreground=COLOR_ACCENT, background=COLOR_BG_DARK)
        link_label.pack(pady=5)
        button_frame = ttk.Frame(dialog, style='DarkFrame.TFrame')
        button_frame.pack(pady=10, fill=tk.X)

        def open_in_browser():
            try:
                webbrowser.open(image_link)
            except Exception as e:
                messagebox.showerror('Error', f'Could not open browser: {e}')
            dialog.destroy()
        ttk.Button(button_frame, text='Open in browser', command=open_in_browser, style='Accent.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='OK', command=dialog.destroy, style='Toolbar.TButton').pack(side=tk.RIGHT, padx=10)
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = dialog.winfo_screenwidth() // 2 - width // 2
        y = dialog.winfo_screenheight() // 2 - height // 2
        dialog.geometry(f'{width}x{height}+{x}+{y}')
        dialog.wait_window()

        def open_in_browser():
            try:
                webbrowser.open(image_link)
            except Exception as e:
                messagebox.showerror('Error', f'Could not open browser: {e}')
            dialog.destroy()
        ttk.Button(button_frame, text='Open in browser', command=open_in_browser, style='Accent.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text='OK', command=dialog.destroy, style='Toolbar.TButton').pack(side=tk.RIGHT, padx=10)
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = dialog.winfo_screenwidth() // 2 - width // 2
        y = dialog.winfo_screenheight() // 2 - height // 2
        dialog.geometry(f'{width}x{height}+{x}+{y}')

    def hide_screenshot(self, filepath):
        filepath_str = str(filepath)
        if filepath_str not in self.config['hidden_files']:
            self.config['hidden_files'].append(filepath_str)
            self.save_config()
            self.load_screenshot_list()

    def copy_screenshot(self, filepath):
        try:
            img = Image.open(filepath)
            self.copy_to_clipboard(img)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to copy screenshot: {e}')

    def copy_coordinates(self, filepath):
        try:
            filename = filepath.name
            import re
            match = re.search('_X(\\d+)Y(\\d+)_X(\\d+)Y(\\d+)', filename)
            if match:
                x1 = match.group(1)
                y1 = match.group(2)
                x2 = match.group(3)
                y2 = match.group(4)
                coord_text = f'({x1} , {y1}) | ({x2} , {y2})'
                coord_text_print = f'X: {x1}, Y: {y1} | X: {x2}, Y: {y2}'
                try:
                    process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    process.communicate(coord_text.encode('utf-8'))
                    messagebox.showinfo('Success', f'Coordinates copied:\n{coord_text_print}')
                except Exception as e:
                    messagebox.showerror('Error', f'Failed to copy to clipboard \n You need to install xclip for your distribution, for example for Ubuntu it is - sudo apt install xclip \n : {e}')
            else:
                messagebox.showwarning('Warning', 'No coordinates found in file name')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to extract coordinates: {e}')

    def show_warning_dialog(self, warning_type, title, message, callback, filepath=None):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=COLOR_BG_DARK)
        dialog.geometry('500x250')
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)
        dialog.grab_set()
        message_frame = ttk.Frame(dialog, style='DarkFrame.TFrame')
        message_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        message_label = tk.Text(message_frame, wrap=tk.WORD, font=FONT_MAIN, bg=COLOR_BG_DARK, fg=COLOR_FG_LIGHT, relief=tk.FLAT, height=8, cursor='arrow')
        message_label.pack(fill=tk.BOTH, expand=True)
        message_label.insert('1.0', message)
        message_label.config(state='disabled')
        button_frame = ttk.Frame(dialog, style='DarkFrame.TFrame')
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        def on_later():
            dialog.destroy()

        def on_proceed():
            self.config['warnings_shown'][warning_type] = True
            self.save_config()
            dialog.destroy()
            if filepath:
                callback(filepath)
            else:
                callback()
        ttk.Button(button_frame, text='Maybe later', command=on_later, style='Toolbar.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Download and don't show again", command=on_proceed, style='Accent.TButton').pack(side=tk.RIGHT, padx=5)
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = dialog.winfo_screenwidth() // 2 - width // 2
        y = dialog.winfo_screenheight() // 2 - height // 2
        dialog.geometry(f'{width}x{height}+{x}+{y}')

    def ocr_screenshot(self, filepath):
        if not self.config['warnings_shown'].get('ocr', False):
            warning_message = 'Once the text is recognized, your image will be sent to https://ocr.space/. The service will extract text from the image and return it to you..\n\nIf for any reason this recognition service does not suit you, You can cancel the action with the button «Maybe later».'
            self.show_warning_dialog('ocr', 'about OCR', warning_message, self._ocr_screenshot_impl, filepath)
            return
        self._ocr_screenshot_impl(filepath)

    def _ocr_screenshot_impl(self, filepath):
        try:
            result_container = {'text': None, 'done': False}

            def run_ocr():
                print(f'[DEBUG] Starting OCR for: {filepath}')
                recognized_text = ocr_space_image(str(filepath), language='eng')
                print(f'[DEBUG] OCR result: {recognized_text[:100]}...')
                result_container['text'] = recognized_text
                result_container['done'] = True
            ocr_thread = threading.Thread(target=run_ocr, daemon=True)
            ocr_thread.start()
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title('OCR')
            progress_dialog.configure(bg=COLOR_BG_DARK)
            progress_dialog.geometry('300x100')
            progress_dialog.resizable(False, False)
            progress_dialog.attributes('-topmost', True)
            progress_dialog.transient(self.root)
            ttk.Label(progress_dialog, text='recognize text...', font=FONT_MAIN, foreground=COLOR_FG_LIGHT, background=COLOR_BG_DARK).pack(pady=20)
            progress_dialog.update_idletasks()
            width = progress_dialog.winfo_width()
            height = progress_dialog.winfo_height()
            x = progress_dialog.winfo_screenwidth() // 2 - width // 2
            y = progress_dialog.winfo_screenheight() // 2 - height // 2
            progress_dialog.geometry(f'{width}x{height}+{x}+{y}')

            def check_result():
                if result_container['done']:
                    try:
                        progress_dialog.destroy()
                    except:
                        pass
                    text = result_container['text']
                    if text.startswith('Error:') or text == 'Text not recognized':
                        messagebox.showerror('Error OCR', text)
                        return
                    result_dialog = tk.Toplevel(self.root)
                    result_dialog.title('Recognized text')
                    result_dialog.configure(bg=COLOR_BG_DARK)
                    result_dialog.geometry('500x400')
                    result_dialog.attributes('-topmost', True)
                    result_dialog.transient(self.root)
                    result_dialog.grab_set()
                    text_frame = ttk.Frame(result_dialog, style='DarkFrame.TFrame')
                    text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                    text_widget = tk.Text(text_frame, wrap=tk.WORD, font=FONT_MAIN, bg=COLOR_CONTROL_BG, fg=COLOR_FG_LIGHT, insertbackground=COLOR_FG_LIGHT)
                    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                    scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
                    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                    text_widget.config(yscrollcommand=scrollbar.set)
                    text_widget.insert('1.0', text)
                    text_widget.config(state='normal')
                    button_frame = ttk.Frame(result_dialog, style='DarkFrame.TFrame')
                    button_frame.pack(fill=tk.X, padx=10, pady=10)

                    def copy_text():
                        try:
                            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            process.communicate(text_widget.get('1.0', 'end-1c').encode('utf-8'))
                            messagebox.showinfo('Success', 'The text has been copied to the clipboard')
                        except Exception as e:
                            messagebox.showerror('Error', f'Failed to copy: {e}')
                    ttk.Button(button_frame, text=f'{ICON_COPY} Copy', command=copy_text, style='Toolbar.TButton').pack(side=tk.LEFT, padx=5)
                    ttk.Button(button_frame, text='Close', command=result_dialog.destroy, style='Toolbar.TButton').pack(side=tk.RIGHT, padx=5)
                    result_dialog.update_idletasks()
                    width = result_dialog.winfo_width()
                    height = result_dialog.winfo_height()
                    x = result_dialog.winfo_screenwidth() // 2 - width // 2
                    y = result_dialog.winfo_screenheight() // 2 - height // 2
                    result_dialog.geometry(f'{width}x{height}+{x}+{y}')
                else:
                    progress_dialog.after(100, check_result)
            progress_dialog.after(100, check_result)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to perform OCR: {e}')

    def ocr_and_translate_screenshot(self, filepath):
        if not self.config['warnings_shown'].get('ocr_translate', False):
            warning_message = 'This action will send your image to https://ocr.space/ for text recognition. After this, the received text will be sent to https://translate.google.com for translation.\n\nYou will receive the translated text from the image.\n\nIf for any reason these services are not suitable for you, You can cancel the action with the button «Maybe later».'
            self.show_warning_dialog('ocr_translate', 'about OCR + Translation', warning_message, self._ocr_and_translate_screenshot_impl, filepath)
            return
        self._ocr_and_translate_screenshot_impl(filepath)

    def _ocr_and_translate_screenshot_impl(self, filepath):
        try:
            result_container = {'text': None, 'done': False}

            def run_ocr_and_translate():
                print(f'[DEBUG] Starting OCR+Translate for: {filepath}')
                recognized_text = ocr_space_image(str(filepath), language='eng')
                print(f'[DEBUG] OCR result: {recognized_text[:100]}...')
                result_container['text'] = recognized_text
                result_container['done'] = True
            ocr_thread = threading.Thread(target=run_ocr_and_translate, daemon=True)
            ocr_thread.start()
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title('OCR + Translation')
            progress_dialog.configure(bg=COLOR_BG_DARK)
            progress_dialog.geometry('300x100')
            progress_dialog.resizable(False, False)
            progress_dialog.attributes('-topmost', True)
            progress_dialog.transient(self.root)
            ttk.Label(progress_dialog, text='I recognize text for translation...', font=FONT_MAIN, foreground=COLOR_FG_LIGHT, background=COLOR_BG_DARK).pack(pady=20)
            progress_dialog.update_idletasks()
            width = progress_dialog.winfo_width()
            height = progress_dialog.winfo_height()
            x = progress_dialog.winfo_screenwidth() // 2 - width // 2
            y = progress_dialog.winfo_screenheight() // 2 - height // 2
            progress_dialog.geometry(f'{width}x{height}+{x}+{y}')

            def check_result():
                if result_container['done']:
                    try:
                        progress_dialog.destroy()
                    except:
                        pass
                    text = result_container['text']
                    if text.startswith('Error:') or text == 'Text not recognized':
                        messagebox.showerror('Error OCR', text)
                        return
                    open_google_translate(text, source_lang='auto', target_lang='en')
                    messagebox.showinfo('Success', 'The text has been recognized and sent to Google Translate')
                else:
                    progress_dialog.after(100, check_result)
            progress_dialog.after(100, check_result)
        except Exception as e:
            messagebox.showerror('Error', f'Failed to perform OCR + translation: {e}')

    def take_screenshot(self, im, region=None):
        if im is None:
            return None
        try:
            timestamp = int(time.time())
            coord_suffix = f'_X{region[0]}Y{region[1]}_X{region[2]}Y{region[3]}' if region else ''
            filename = f'screenshot_{timestamp}{coord_suffix}.png'
            filepath = Path(self.config['screenshot_dir']) / filename
            im.save(filepath, 'PNG')
            if self.config['auto_copy']:
                self.copy_to_clipboard(im)
            if self.config['sound_enabled']:
                self.play_sound()
            threading.Thread(target=self.upload_image, args=(filepath,)).start()
            if self.root and self.root.winfo_exists():
                self.root.after(100, self.load_screenshot_list)
            return filepath
        except Exception as e:
            messagebox.showerror('Error', f'Failed to take screenshot: {e}')
            return None

    def take_region_screenshot(self):
        with self.screenshot_lock:
            if self.screenshot_in_progress:
                print('Screenshot already in progress, ignoring request')
                return
            self.screenshot_in_progress = True
        try:
            if not ImageGrab:
                if self.root:
                    self.root.after(0, lambda: messagebox.showerror('Error', 'The pyscreenshot module is not installed. Install it.'))
                return
            if self.root:
                for widget in self.root.winfo_children():
                    if isinstance(widget, tk.Toplevel) and 'annotations' in widget.title().lower():
                        print('Region Selector is already running.')
                        return
            try:
                full_screen_im = ImageGrab.grab()
                time.sleep(0.2)
            except Exception as e:
                if self.root:
                    self.root.after(0, lambda e=e: messagebox.showerror('Error', f'Failed to take screenshot: {e}'))
                return
            if self.root and self.root.winfo_exists():
                self.root.after(0, lambda: self._create_region_selector(full_screen_im))
            else:
                print('Root window not available')
        except Exception as e:
            print(f'Error in take_region_screenshot: {e}')
        finally:
            with self.screenshot_lock:
                self.screenshot_in_progress = False
            print('Screenshot process completed, ready for next capture')

    def take_fullscreen_screenshot(self):
        try:
            if not ImageGrab:
                if self.root:
                    self.root.after(0, lambda: messagebox.showerror('Error', 'The pyscreenshot module is not installed.'))
                return
            try:
                full_screen_im = ImageGrab.grab()
                self.take_screenshot(im=full_screen_im, region=None)
            except Exception as e:
                if self.root:
                    self.root.after(0, lambda e=e: messagebox.showerror('Error', f'Failed to take screenshot: {e}'))
        except Exception as e:
            print(f'Error in take_fullscreen_screenshot: {e}')

    def _create_region_selector(self, full_screen_im):
        try:
            window_geometry = None
            if self.root and self.root.winfo_exists():
                self.root.update_idletasks()
                window_geometry = self.root.geometry()
                self.root.attributes('-alpha', 0.0)
                self.root.update_idletasks()
            region_selector = RegionSelector(self, full_screen_im)
            region = region_selector.get_region()
            annotated_im = region_selector.drawable_image
            if self.root and self.root.winfo_exists():
                if window_geometry:
                    self.root.geometry(window_geometry)
                self.root.attributes('-alpha', 1.0)
                self.root.update_idletasks()
                if self.pending_gui_calls:
                    print(f'[DEBUG] Processing {len(self.pending_gui_calls)} pending GUI calls')
                    for dialog_func, args, kwargs in self.pending_gui_calls:
                        try:
                            self.root.after(0, lambda f=dialog_func, a=args, k=kwargs: f(*a, **k))
                        except Exception as e:
                            print(f'[ERROR] Failed to execute pending call: {e}')
                    self.pending_gui_calls.clear()
            if region:
                x1, y1, x2, y2 = region
                cropped_im = annotated_im.crop((x1, y1, x2, y2))
                self.take_screenshot(im=cropped_im, region=(x1, y1, x2, y2))
            elif region_selector.drawing_history:
                self.take_screenshot(im=annotated_im, region=None)
        except Exception as e:
            print(f'Error in _create_region_selector: {e}')
            if self.root and self.root.winfo_exists():
                if window_geometry:
                    self.root.geometry(window_geometry)
                self.root.attributes('-alpha', 1.0)

    def copy_to_clipboard(self, image):
        try:
            output = subprocess.Popen(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-i'], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            image.save(output.stdin, 'PNG')
            output.stdin.close()
            output.wait()
        except:
            pass

    def play_sound(self):
        try:
            subprocess.Popen(['paplay', '/usr/share/sounds/freedesktop/stereo/screen-capture.ogg'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

    def upload_image(self, filepath):
        pass

    def load_screenshot_list(self):
        if not self.gallery_frame:
            return
        for widget in self.gallery_frame.winfo_children():
            widget.destroy()
        self.thumbnails = []
        screenshot_dir = Path(self.config['screenshot_dir'])
        files = sorted([f for f in screenshot_dir.glob('*.png') if f.is_file() and str(f) not in self.config['hidden_files']], key=os.path.getctime, reverse=True)
        if not files:
            ttk.Label(self.gallery_frame, text=' No screenshots found \n Area screenshot - alt+s \n Fullscreen - alt+z \n \n You can change keybindings in the config (button on the left)', font=FONT_MAIN, foreground='gray').grid(row=0, column=0, padx=20, pady=50, columnspan=THUMB_COLUMNS)
            self.root.update_idletasks()
            self.gallery_canvas.config(scrollregion=self.gallery_canvas.bbox('all'))
            return
        max_visible = self.config.get('max_visible_screenshots', 25)
        visible_files = files[:max_visible]
        total_count = len(files)
        if total_count > max_visible:
            info_label = ttk.Label(self.gallery_frame, text=f'📊 Showing {max_visible} out of {total_count} screenshots (setting: max_visible_screenshots)', font=FONT_SMALL, foreground=COLOR_ACCENT, background=COLOR_BG_DARK)
            info_label.grid(row=0, column=0, columnspan=THUMB_COLUMNS, pady=10, sticky='ew')
        for i in range(THUMB_COLUMNS):
            self.gallery_frame.grid_columnconfigure(i, weight=1)
        start_row = 1 if total_count > max_visible else 0
        for index, f in enumerate(visible_files):
            row = index // THUMB_COLUMNS + start_row
            col = index % THUMB_COLUMNS
            try:
                img = Image.open(f)
                resized_img = ImageOps.fit(img, (THUMB_SIZE, THUMB_SIZE), method=Image.Resampling.LANCZOS)
                thumb_with_border = Image.new('RGBA', (THUMB_SIZE + 10, THUMB_SIZE + 10), (0, 0, 0, 0))
                mask = Image.new('L', (THUMB_SIZE, THUMB_SIZE), 0)
                ImageDraw.Draw(mask).rounded_rectangle((0, 0, THUMB_SIZE, THUMB_SIZE), radius=BORDER_RADIUS_SMALL, fill=255)
                shadow_offset = 3
                shadow_mask = mask.copy().filter(ImageFilter.GaussianBlur(5))
                thumb_with_border.paste((0, 0, 0, 100), (shadow_offset, shadow_offset), shadow_mask)
                thumb_with_border.paste(resized_img, (0, 0), mask)
                from PIL import ImageEnhance
                brightened_img = ImageEnhance.Brightness(resized_img).enhance(1.2)
                thumb_with_border_bright = Image.new('RGBA', (THUMB_SIZE + 10, THUMB_SIZE + 10), (0, 0, 0, 0))
                thumb_with_border_bright.paste((0, 0, 0, 100), (shadow_offset, shadow_offset), shadow_mask)
                thumb_with_border_bright.paste(brightened_img, (0, 0), mask)
                photo = ImageTk.PhotoImage(thumb_with_border)
                photo_bright = ImageTk.PhotoImage(thumb_with_border_bright)
                self.thumbnails.append(photo)
                self.thumbnails.append(photo_bright)
                thumb_container = ttk.Frame(self.gallery_frame, style='DarkFrame.TFrame')
                thumb_container.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
                thumb_container.grid_rowconfigure(0, weight=0)
                thumb_container.grid_rowconfigure(1, weight=0)
                thumb_container.grid_columnconfigure(0, weight=1)
                image_frame = ttk.Frame(thumb_container, style='Card.TFrame')
                image_frame.grid(row=0, column=0, pady=(0, 5))
                thumb_label = tk.Label(image_frame, image=photo, width=THUMB_SIZE + 10, height=THUMB_SIZE + 10, relief=tk.FLAT, bg=COLOR_BG_DARK)
                thumb_label.pack(padx=0, pady=0)
                display_name = f.name
                name_label = ttk.Label(thumb_container, text=display_name, anchor=tk.CENTER, font=FONT_SMALL, foreground=COLOR_FG_LIGHT, background=COLOR_BG_DARK, wraplength=THUMB_SIZE)
                name_label.grid(row=1, column=0, sticky='ew')

                def make_context_menu(filepath):
                    menu = tk.Menu(self.root, tearoff=0, font=FONT_SMALL, bg=COLOR_CONTROL_BG, fg=COLOR_FG_LIGHT)

                    def copy_and_close():
                        menu.unpost()
                        self.copy_screenshot(filepath)

                    def copy_coords_and_close():
                        menu.unpost()
                        self.copy_coordinates(filepath)

                    def upload_and_close():
                        menu.unpost()
                        self.upload_image_to_cloud(filepath)

                    def ocr_and_close():
                        menu.unpost()
                        self.ocr_screenshot(filepath)

                    def ocr_translate_and_close():
                        menu.unpost()
                        self.ocr_and_translate_screenshot(filepath)

                    def hide_and_close():
                        menu.unpost()
                        self.hide_screenshot(filepath)
                    menu.add_command(label='📋 Copy', command=copy_and_close)
                    menu.add_command(label='🎞 Copy coordinates', command=copy_coords_and_close)
                    menu.add_separator()
                    menu.add_command(label='📝 OCR (Optical Character Recognition)', command=ocr_and_close)
                    menu.add_command(label='🌐 OCR + Translation', command=ocr_translate_and_close)
                    menu.add_separator()
                    menu.add_command(label='☁ Upload to cloud', command=upload_and_close)
                    menu.add_command(label='✂ Hide', command=hide_and_close)
                    return menu
                context_menu = make_context_menu(f)

                def show_context_menu(event, menu=context_menu):

                    def close_on_click(e):
                        try:
                            if menu.winfo_exists():
                                menu_x = menu.winfo_rootx()
                                menu_y = menu.winfo_rooty()
                                menu_width = menu.winfo_width()
                                menu_height = menu.winfo_height()
                                if not (menu_x <= e.x_root <= menu_x + menu_width and menu_y <= e.y_root <= menu_y + menu_height):
                                    menu.unpost()
                                    cleanup_bindings()
                        except:
                            cleanup_bindings()

                    def cleanup_bindings():
                        try:
                            self.root.unbind('<Button-1>', bind_id_1)
                            self.root.unbind('<Button-3>', bind_id_3)
                        except:
                            pass
                    menu.post(event.x_root, event.y_root)
                    bind_id_1 = self.root.bind('<Button-1>', close_on_click, add='+')
                    bind_id_3 = self.root.bind('<Button-3>', close_on_click, add='+')
                    menu.bind('<FocusOut>', lambda e: (menu.unpost(), cleanup_bindings()))

                def on_enter(event, frame=image_frame, label=thumb_label, bright_photo=photo_bright):
                    frame.config(style='CardHover.TFrame')
                    label.config(image=bright_photo)

                def on_leave(event, frame=image_frame, label=thumb_label, normal_photo=photo):
                    frame.config(style='Card.TFrame')
                    label.config(image=normal_photo)
                image_frame.bind('<Enter>', on_enter)
                image_frame.bind('<Leave>', on_leave)
                thumb_label.bind('<Enter>', on_enter)
                thumb_label.bind('<Leave>', on_leave)
                image_frame.bind('<Button-3>', show_context_menu)
                thumb_label.bind('<Button-3>', show_context_menu)
                name_label.bind('<Button-3>', show_context_menu)
                thumb_label.bind('<Button-1>', lambda e, path=f: self.open_screenshot_viewer(path))
                image_frame.bind('<Button-1>', lambda e, path=f: self.open_screenshot_viewer(path))
                name_label.bind('<Button-1>', lambda e, path=f: self.open_screenshot_viewer(path))

                def bind_scroll(w):
                    w.bind('<MouseWheel>', self._on_scroll_event)
                    w.bind('<Button-4>', self._on_scroll_event)
                    w.bind('<Button-5>', self._on_scroll_event)
                for widget in [thumb_container, image_frame, thumb_label, name_label]:
                    bind_scroll(widget)
            except Exception as e:
                print(f'Error creating thumbnail for {f}: {e}')
        self.root.update_idletasks()
        self.gallery_canvas.config(scrollregion=self.gallery_canvas.bbox('all'))

    def open_screenshot_viewer(self, filepath):
        if self.viewer_window and self.viewer_window.winfo_exists():
            self.viewer_window.destroy()
        if self.root:
            new_viewer = ScreenshotViewer(self.root, filepath, self)
            self.viewer_window = new_viewer.window
            self.viewer_window.focus_force()
            self.viewer_window.lift()

    def get_screenshot_files_list(self):
        screenshot_dir = Path(self.config['screenshot_dir'])
        files = sorted([f for f in screenshot_dir.glob('*.png') if f.is_file() and str(f) not in self.config['hidden_files']], key=os.path.getctime, reverse=True)
        return files

    def _start_dnd(self, widget, filepath):
        try:
            dnd_window = tk.Toplevel(self.root)
            dnd_window.overrideredirect(True)
            dnd_window.attributes('-alpha', 0.7)
            dnd_window.attributes('-topmost', True)
            try:
                img = Image.open(filepath)
                img.thumbnail((100, 100), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(dnd_window, image=photo, bg=COLOR_CONTROL_BG, bd=2, relief=tk.RAISED)
                label.image = photo
                label.pack()
            except:
                label = tk.Label(dnd_window, text='📷', font=('Arial', 48), bg=COLOR_CONTROL_BG)
                label.pack(padx=10, pady=10)
            x = self.root.winfo_pointerx() + 10
            y = self.root.winfo_pointery() + 10
            dnd_window.geometry(f'+{x}+{y}')
            is_dragging = {'active': True}

            def update_position():
                if is_dragging['active'] and dnd_window.winfo_exists():
                    try:
                        x = self.root.winfo_pointerx() + 10
                        y = self.root.winfo_pointery() + 10
                        dnd_window.geometry(f'+{x}+{y}')
                        self.root.after(10, update_position)
                    except:
                        pass
            update_position()
            try:
                file_uri = f'file://{filepath}\n'
                process = subprocess.Popen(['xclip', '-selection', 'clipboard', '-t', 'text/uri-list'], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process.communicate(file_uri.encode('utf-8'))
                process2 = subprocess.Popen(['xclip', '-selection', 'primary', '-t', 'text/uri-list'], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                process2.communicate(file_uri.encode('utf-8'))
            except:
                pass

            def end_dnd(event=None):
                is_dragging['active'] = False
                try:
                    if dnd_window.winfo_exists():
                        dnd_window.destroy()
                except:
                    pass
                hint_window = tk.Toplevel(self.root)
                hint_window.overrideredirect(True)
                hint_window.attributes('-topmost', True)
                hint_window.configure(bg=COLOR_CONTROL_BG)
                hint_label = tk.Label(hint_window, text='💡 File path copied to clipboard.\n Use Ctrl+V to paste', font=FONT_MAIN, bg=COLOR_CONTROL_BG, fg=COLOR_FG_LIGHT, padx=15, pady=10)
                hint_label.pack()
                hint_window.update_idletasks()
                x = self.root.winfo_pointerx() - hint_window.winfo_width() // 2
                y = self.root.winfo_pointery() + 20
                hint_window.geometry(f'+{x}+{y}')
                self.root.after(2000, lambda: hint_window.destroy() if hint_window.winfo_exists() else None)
            self.root.bind('<ButtonRelease-1>', end_dnd, add='+')
            dnd_window.bind('<ButtonRelease-1>', end_dnd)
        except Exception as e:
            print(f'DND error: {e}')

    def open_screenshot_folder(self):
        try:
            path = Path(self.config['screenshot_dir'])
            subprocess.Popen(['xdg-open', str(path)])
        except Exception as e:
            messagebox.showwarning('Warning', f'Failed to open folder: {e}')

    def open_config_file(self):
        config_path = str(self.config_file)
        gui_editors = ['gedit', 'kate', 'mousepad', 'pluma', 'leafpad']
        terminals = ['alacritty', 'kitty', 'konsole', 'gnome-terminal', 'xfce4-terminal', 'xterm']
        cli_editors = ['nano', 'vim', 'nvim']
        for editor in gui_editors:
            if shutil.which(editor):
                try:
                    subprocess.Popen([editor, config_path])
                    return
                except Exception:
                    continue
        chosen_cli = next((e for e in cli_editors if shutil.which(e)), None)
        if chosen_cli:
            for term in terminals:
                if shutil.which(term):
                    try:
                        subprocess.Popen([term, '-e', chosen_cli, config_path])
                        return
                    except Exception:
                        continue
        try:
            subprocess.Popen(['xdg-open', config_path])
        except FileNotFoundError:
            print('Unable to find a suitable editor in the system.')
            subprocess.Popen(['xdg-open', str(self.config_file)])
        except Exception as e:
            messagebox.showwarning('Warning', f'Failed to open config: {e}')

    def upload_image_to_cloud(self, filepath):
        if not self.config['warnings_shown'].get('cloud_upload', False):
            warning_message = "Uploading to the cloud means that your image will be sent to https://freeimage.host/. Once uploaded, anyone with a link to the image can view it.\n\nDo not upload personal data, documents or images containing private information. Only upload images that you knowingly want to share.\n\nIf you don't want to upload the image now, click «Maybe later»."
            self.show_warning_dialog('cloud_upload', 'about uploading to the cloud', warning_message, self._upload_image_to_cloud_impl, filepath)
            return
        self._upload_image_to_cloud_impl(filepath)

    def _upload_image_to_cloud_impl(self, filepath):
        print(f'[DEBUG] Starting upload for: {filepath}')
        result_container = {'link': None, 'error': None, 'done': False}

        def upload_thread():
            try:
                print(f'[DEBUG] Checking file existence...')
                if not os.path.exists(filepath):
                    print(f'[ERROR] File not found: {filepath}')
                    result_container['error'] = f'File not found: {filepath}'
                    result_container['done'] = True
                    return
                print(f'[DEBUG] File exists, preparing upload...')
                upload_url = 'https://freeimage.host/json'
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 'Referer': 'https://freeimage.host/'}
                data = {'type': 'file', 'action': 'upload', 'source': 'file', 'key': 'freeimagehost', 'format': 'json'}
                with open(filepath, 'rb') as file:
                    files = {'source': (os.path.basename(filepath), file, 'image/jpeg' if str(filepath).lower().endswith('.jpg') else 'image/png')}
                    print(f'[DEBUG] Sending request to {upload_url}...')
                    response = requests.post(upload_url, headers=headers, data=data, files=files, timeout=30)
                    response.raise_for_status()
                    print(f'[DEBUG] Response status: {response.status_code}')
                    result = response.json()
                    print(f'[DEBUG] Response data: {result}')
                    if result.get('status_code') == 200 and result.get('status_txt') == 'OK':
                        image_link = result['image']['url']
                        print(f'[SUCCESS] Upload successful: {image_link}')
                        try:
                            print(f'[DEBUG] Copying to clipboard...')
                            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            process.communicate(image_link.encode('utf-8'))
                            print(f'[DEBUG] Clipboard copy successful')
                        except Exception as e:
                            print(f'[ERROR] Clipboard copy failed: {e}')
                        result_container['link'] = image_link
                        result_container['done'] = True
                    else:
                        error_message = result.get('error', 'Unknown loading error.')
                        print(f'[ERROR] Upload failed: {error_message}')
                        result_container['error'] = f'Loading error: {error_message}'
                        result_container['done'] = True
            except requests.exceptions.RequestException as e:
                print(f'[ERROR] Network error: {e}')
                result_container['error'] = f'Network error: {e}'
                result_container['done'] = True
            except Exception as e:
                print(f'[ERROR] Unexpected error: {e}')
                import traceback
                traceback.print_exc()
                result_container['error'] = f'Unexpected error: {e}'
                result_container['done'] = True
        print(f'[DEBUG] Starting upload thread...')
        threading.Thread(target=upload_thread, daemon=True).start()
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title('Loading')
        progress_dialog.configure(bg=COLOR_BG_DARK)
        progress_dialog.geometry('300x100')
        progress_dialog.resizable(False, False)
        progress_dialog.attributes('-topmost', True)
        progress_dialog.transient(self.root)
        ttk.Label(progress_dialog, text='Uploading an image...', font=FONT_MAIN, foreground=COLOR_FG_LIGHT, background=COLOR_BG_DARK).pack(pady=20)
        progress_dialog.update_idletasks()
        width = progress_dialog.winfo_width()
        height = progress_dialog.winfo_height()
        x = progress_dialog.winfo_screenwidth() // 2 - width // 2
        y = progress_dialog.winfo_screenheight() // 2 - height // 2
        progress_dialog.geometry(f'{width}x{height}+{x}+{y}')

        def check_result():
            if result_container['done']:
                try:
                    progress_dialog.destroy()
                except:
                    pass
                if result_container['error']:
                    messagebox.showerror('Error', result_container['error'])
                elif result_container['link']:
                    self.show_upload_success_dialog(result_container['link'])
            else:
                progress_dialog.after(100, check_result)
        progress_dialog.after(100, check_result)

    def start_global_listener(self):
        if not keyboard or self.listener:
            return
        key_mapping = {'print_screen': keyboard.Key.print_screen, 'end': keyboard.Key.end, 'home': keyboard.Key.home, 'insert': keyboard.Key.insert, 'delete': keyboard.Key.delete, 'page_up': keyboard.Key.page_up, 'page_down': keyboard.Key.page_down, 'space': keyboard.Key.space, 'shift': keyboard.Key.shift, 'ctrl': keyboard.Key.ctrl, 'control': keyboard.Key.ctrl, 'alt': keyboard.Key.alt, 'cmd': keyboard.Key.cmd, 'super': keyboard.Key.cmd, 'f1': keyboard.Key.f1, 'f2': keyboard.Key.f2, 'f3': keyboard.Key.f3, 'f4': keyboard.Key.f4, 'f5': keyboard.Key.f5, 'f6': keyboard.Key.f6, 'f7': keyboard.Key.f7, 'f8': keyboard.Key.f8, 'f9': keyboard.Key.f9, 'f10': keyboard.Key.f10, 'f11': keyboard.Key.f11, 'f12': keyboard.Key.f12}
        region_key_str = self.config['hotkeys'].get('region', 'end').lower()
        fullscreen_key_str = self.config['hotkeys'].get('fullscreen', 'print_screen').lower()

        def parse_hotkey(hotkey_str):
            parts = [p.strip().lower() for p in hotkey_str.split('+')]
            modifiers = set()
            main_key = None
            for part in parts:
                if part in ['shift', 'ctrl', 'control', 'alt', 'super', 'cmd']:
                    if part == 'control':
                        part = 'ctrl'
                    modifiers.add(key_mapping.get(part))
                elif part in key_mapping:
                    main_key = key_mapping[part]
                else:
                    try:
                        main_key = keyboard.KeyCode.from_char(part)
                    except:
                        main_key = None
            return (modifiers, main_key)
        region_modifiers, region_main = parse_hotkey(region_key_str)
        fullscreen_modifiers, fullscreen_main = parse_hotkey(fullscreen_key_str)
        pressed_modifiers = set()

        def on_press(key):
            try:
                if key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]:
                    pressed_modifiers.add(keyboard.Key.shift)
                elif key in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                    pressed_modifiers.add(keyboard.Key.ctrl)
                elif key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r]:
                    pressed_modifiers.add(keyboard.Key.alt)
                elif key in [keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r]:
                    pressed_modifiers.add(keyboard.Key.cmd)
                if region_main and key == region_main:
                    if region_modifiers.issubset(pressed_modifiers):
                        print(f'{region_key_str} combination pressed, triggering region screenshot')
                        self.pending_screenshot = True
                if fullscreen_main and key == fullscreen_main:
                    if fullscreen_modifiers.issubset(pressed_modifiers):
                        print(f'{fullscreen_key_str} combination pressed, triggering fullscreen screenshot')
                        if self.root and self.root.winfo_exists():
                            self.root.after(0, self.take_fullscreen_screenshot)
            except AttributeError:
                pass

        def on_release(key):
            try:
                if key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]:
                    pressed_modifiers.discard(keyboard.Key.shift)
                elif key in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                    pressed_modifiers.discard(keyboard.Key.ctrl)
                elif key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r]:
                    pressed_modifiers.discard(keyboard.Key.alt)
                elif key in [keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r]:
                    pressed_modifiers.discard(keyboard.Key.cmd)
            except AttributeError:
                pass
        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.daemon = True
        self.listener.start()
        print(f'Global hotkey listener started ({region_key_str} for region, {fullscreen_key_str} for fullscreen)')

    def stop_global_listener(self):
        if self.listener:
            try:
                self.listener.stop()
                print('Global hotkey listener stopped')
            except Exception as e:
                print(f'Listener stop error: {e}')
            finally:
                self.listener = None

def ocr_space_image(image_path, api_key='helloworld', language='eng'):
    if not Path(image_path).exists():
        return f'Error: File {image_path} not found'
    with open(image_path, 'rb') as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    payload = {'base64Image': f'data:image/png;base64,{image_base64}', 'language': language, 'isOverlayRequired': False, 'OCREngine': 2}
    headers = {'apikey': api_key, 'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        response = requests.post('https://api.ocr.space/parse/image', data=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        if result['IsErroredOnProcessing']:
            return f"OCR error: {result.get('ErrorMessage', 'Unknown error')}"
        parsed_results = result.get('ParsedResults', [])
        if parsed_results:
            text = parsed_results[0].get('ParsedText', '').strip()
            return text if text else 'Text not recognized'
        else:
            return 'No recognition results'
    except requests.exceptions.RequestException as e:
        return f'You’re offline or sending too many requests. Please try again in 5 minutes: \n \n {e}'
    except json.JSONDecodeError as e:
        return f'JSON parsing error: {e}'
    except Exception as e:
        return f'Unexpected error: {e}'

def open_google_translate(text_to_translate, source_lang='auto', target_lang='en'):
    encoded_text = urllib.parse.quote_plus(text_to_translate)
    url = f'https://translate.google.com/?sl={source_lang}&tl={target_lang}&text={encoded_text}&op=translate'
    print(f'Open Google Translate in your browser...')
    webbrowser.open_new_tab(url)
    print(f'Link for translation: {url}')

class ScreenshotViewer:

    def __init__(self, master, filepath, app_instance):
        self.filepath = filepath
        self.app = app_instance
        self.window = tk.Toplevel(master)
        self.window.title(f'View - {filepath.name}')
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        self.window.overrideredirect(True)
        self.window.geometry(f'{screen_width}x{screen_height}+0+0')
        self.window.configure(bg='black')
        self.pil_image = None
        self.tk_image = None
        self.image_id = None
        self.zoom_factor = 1.0
        self.original_width = 0
        self.original_height = 0
        self._zoom_scheduled = False
        self.screenshot_files = self.app.get_screenshot_files_list()
        self.current_index = 0
        try:
            self.current_index = self.screenshot_files.index(filepath)
        except ValueError:
            pass
        self.setup_ui()
        self.load_image()

        def navigate_prev(self):
            if self.current_index > 0:
                self.current_index -= 1
                self.filepath = self.screenshot_files[self.current_index]
                self.load_image()
                self.window.title(f'View - {self.filepath.name}')
                self.window.focus_force()
                self.canvas.focus_set()

        def navigate_next(self):
            if self.current_index < len(self.screenshot_files) - 1:
                self.current_index += 1
                self.filepath = self.screenshot_files[self.current_index]
                self.load_image()
                self.window.title(f'View - {self.filepath.name}')
                self.window.focus_force()
                self.canvas.focus_set()
        self.window.protocol('WM_DELETE_WINDOW', self.on_close)
        self.window.bind('<Escape>', lambda e: self.on_close())
        self.window.bind('<a>', lambda e: self.navigate_prev())
        self.window.bind('<d>', lambda e: self.navigate_next())

    def navigate_prev(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.filepath = self.screenshot_files[self.current_index]
            self.load_image()
            self.window.title(f'View - {self.filepath.name}')

    def navigate_next(self):
        if self.current_index < len(self.screenshot_files) - 1:
            self.current_index += 1
            self.filepath = self.screenshot_files[self.current_index]
            self.load_image()
            self.window.title(f'View - {self.filepath.name}')

    def on_mouse_wheel(self, event, direction=None):
        if not self.pil_image:
            return
        if event.delta:
            zoom_in = event.delta > 0
        elif direction is not None:
            zoom_in = direction > 0
        else:
            return
        scale_amount = 1.1
        if zoom_in:
            new_zoom = self.zoom_factor * scale_amount
        else:
            new_zoom = self.zoom_factor / scale_amount
        new_zoom = max(0.1, min(8.0, new_zoom))
        self.zoom_factor = new_zoom
        if hasattr(self, '_zoom_scheduled') and self._zoom_scheduled:
            return 'break'
        self._zoom_scheduled = True
        self.window.after(10, self._apply_zoom)
        return 'break'

    def _apply_zoom(self):
        self._zoom_scheduled = False
        self.rescale_image()

    def rescale_image(self):
        if not self.pil_image:
            return
        new_w = int(self.original_width * self.zoom_factor)
        new_h = int(self.original_height * self.zoom_factor)
        if new_w <= 0 or new_h <= 0:
            return
        if self.zoom_factor < 1.0:
            resampling = Image.Resampling.LANCZOS
        elif new_w * new_h > 4000000:
            resampling = Image.Resampling.BILINEAR
        else:
            resampling = Image.Resampling.LANCZOS
        resized_im = self.pil_image.resize((new_w, new_h), resampling)
        self.tk_image = ImageTk.PhotoImage(resized_im)
        self.canvas.itemconfig(self.image_id, image=self.tk_image)
        self.canvas.config(scrollregion=(0, 0, new_w, new_h))
        self.center_image()
        self.canvas.update()

    def on_close(self):
        if self.app.viewer_window is self.window:
            self.app.viewer_window = None
        self.window.destroy()

    def setup_ui(self):
        image_area_frame = ttk.Frame(self.window, style='BlackCanvas.TFrame')
        image_area_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(image_area_frame, bg='black', highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.window.update_idletasks()
        v_scroll = ttk.Scrollbar(image_area_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll = ttk.Scrollbar(self.window, orient=tk.HORIZONTAL, command=self.canvas.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.config(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        self.canvas.bind('<Configure>', self.center_image)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        self.canvas.bind('<Button-4>', lambda e: self.on_mouse_wheel(e, direction=1))
        self.canvas.bind('<Button-5>', lambda e: self.on_mouse_wheel(e, direction=-1))
        control_frame = ttk.Frame(self.window, padding='5', style='FloatingToolbar.TFrame')
        control_frame.place(relx=0.5, rely=0.02, anchor=tk.N)
        ttk.Button(control_frame, text=f'{ICON_SAVE} Save as', command=self.save_as, style='Toolbar.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text=f'{ICON_COPY} Copy', command=lambda: self.app.copy_to_clipboard(self.pil_image), style='Toolbar.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text=f'{ICON_FOLDER} Open in folder', command=self.app.open_screenshot_folder, style='Toolbar.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text='(A)◀', command=self.navigate_prev, style='Toolbar.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text='▶(D) ', command=self.navigate_next, style='Toolbar.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text=f'{ICON_CLOSE} Close (Esc)', command=self.on_close, style='ToolbarDanger.TButton').pack(side=tk.LEFT, padx=5)
        self.window.focus_force()
        self.canvas.focus_set()

    def load_image(self):
        try:
            self.pil_image = Image.open(self.filepath)
            self.original_width, self.original_height = self.pil_image.size
            self.zoom_factor = 1.0
            self.tk_image = ImageTk.PhotoImage(self.pil_image)
            if self.image_id is not None:
                self.canvas.itemconfig(self.image_id, image=self.tk_image)
            else:
                self.image_id = self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
            self.canvas.config(scrollregion=(0, 0, self.pil_image.width, self.pil_image.height))
            self.center_image()
        except Exception as e:
            messagebox.showerror('Loading error', f'Failed to load image: {e}')
            self.window.destroy()

    def center_image(self, event=None):
        if not hasattr(self, 'pil_image') or self.original_width == 0:
            return
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width = int(self.original_width * self.zoom_factor)
        img_height = int(self.original_height * self.zoom_factor)
        x_offset = max(0, (canvas_width - img_width) // 2)
        y_offset = max(0, (canvas_height - img_height) // 2)
        self.canvas.coords(self.image_id, x_offset, y_offset)
        scroll_width = max(canvas_width, img_width)
        scroll_height = max(canvas_height, img_height)
        self.canvas.config(scrollregion=(0, 0, scroll_width, scroll_height))

    def save_as(self):
        if not self.pil_image:
            return
        default_name = self.filepath.name
        new_filepath = filedialog.asksaveasfilename(defaultextension='.png', initialfile=default_name, filetypes=[('PNG files', '*.png'), ('All files', '*.*')])
        if new_filepath:
            try:
                self.pil_image.save(new_filepath)
                messagebox.showinfo('Saved', f'Image saved as:\n{new_filepath}', parent=self.window)
            except Exception as e:
                messagebox.showerror('Save error', f'Failed to save file: {e}', parent=self.window)

class RegionSelector:

    def __init__(self, app, background_image):
        self.app = app
        self.root = tk.Toplevel()
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.rect = None
        self.result_region = None
        self.original_image = background_image
        self.drawable_image = background_image.copy()
        self.draw = ImageDraw.Draw(self.drawable_image)
        self.tk_image = ImageTk.PhotoImage(background_image)
        self.bg_image_id = None
        self.size_label = None
        self.drawing_history = []
        self.current_stroke_points = []
        self.current_canvas_item = None
        self.mode = 'SELECT'
        self.mode_before_move = 'DRAW_LINE'
        self.brush_size = 8
        self.draw_color = 'red'
        self.arrow_head_length = 30
        self.arrow_head_angle_deg = 30
        self.toolbar_frame = None
        self.text_mode_font_size = 20
        self.active_text_box = None
        self.move_origin_x = None
        self.move_origin_y = None
        self.moving_item_index = None
        self.moving_item_original_coords = None
        self.blur_radius = 10
        self.coord_text = None
        self.setup_ui()

    def setup_ui(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.overrideredirect(True)
        self.root.geometry(f'{screen_width}x{screen_height}+0+0')
        self.root.configure(bg='black')
        self.root.attributes('-topmost', True)
        self.root.title('Annotation and Highlighting Tool')
        self.root.update_idletasks()
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.root.update()
        self.bg_image_id = self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
        self.toolbar_frame = ttk.Frame(self.root, padding='5', style='FloatingToolbar.TFrame')
        self.toolbar_frame.place(relx=0.5, rely=0.02, anchor=tk.N)
        self._setup_toolbar()
        self._bind_events()
        self.root.protocol('WM_DELETE_WINDOW', self.on_escape)
        self.root.grab_set()
        self.set_mode(self.mode)

    def _setup_toolbar(self):
        self.btn_brush = ttk.Button(self.toolbar_frame, text=f'{ICON_BRUSH} Line', command=lambda: self.set_mode('DRAW_LINE'), style='Toolbar.TButton')
        self.btn_brush.pack(side=tk.LEFT, padx=3)
        self.btn_arrow = ttk.Button(self.toolbar_frame, text=f'{ICON_ARROW} Arrow', command=lambda: self.set_mode('DRAW_ARROW'), style='Toolbar.TButton')
        self.btn_arrow.pack(side=tk.LEFT, padx=3)
        self.btn_select = ttk.Button(self.toolbar_frame, text=f'{ICON_SELECT} Selection', command=lambda: self.set_mode('SELECT'), style='Toolbar.TButton')
        self.btn_select.pack(side=tk.LEFT, padx=3)
        self.btn_text = ttk.Button(self.toolbar_frame, text=f'{ICON_TEXT} Text', command=lambda: self.set_mode('DRAW_TEXT'), style='Toolbar.TButton')
        self.btn_text.pack(side=tk.LEFT, padx=3)
        self.btn_blur = ttk.Button(self.toolbar_frame, text=f'{ICON_BLUR} Blur', command=lambda: self.set_mode('DRAW_BLUR'), style='Toolbar.TButton')
        self.btn_blur.pack(side=tk.LEFT, padx=3)
        self.btn_move = ttk.Button(self.toolbar_frame, text=f'{ICON_MOVE} Move', command=lambda: self.set_mode('MOVE_ITEM'), style='Toolbar.TButton')
        self.btn_move.pack(side=tk.LEFT, padx=3)
        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(self.toolbar_frame, text='Color:', foreground=COLOR_FG_LIGHT, background=COLOR_CONTROL_BG).pack(side=tk.LEFT)
        self.color_button = tk.Label(self.toolbar_frame, bg=self.draw_color, width=2, height=1, relief=tk.RIDGE, bd=1, cursor='hand2')
        self.color_button.bind('<Button-1>', self.show_color_palette)
        self.color_button.pack(side=tk.LEFT, padx=5)
        ttk.Label(self.toolbar_frame, text='Size:', foreground=COLOR_FG_LIGHT, background=COLOR_CONTROL_BG).pack(side=tk.LEFT)
        self.size_scale = ttk.Scale(self.toolbar_frame, from_=2, to=40, orient=tk.HORIZONTAL, length=100, command=self.update_tool_size_from_scale, style='TScale')
        self.size_scale.set(self.brush_size)
        self.size_scale.pack(side=tk.LEFT, padx=5)
        self.size_label = ttk.Label(self.toolbar_frame, text=str(self.brush_size), foreground=COLOR_FG_LIGHT, background=COLOR_CONTROL_BG, width=2)
        self.size_label.pack(side=tk.LEFT)
        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Button(self.toolbar_frame, text=f'{ICON_UNDO} Cancel (Ctrl+Z)', command=self.undo_last_action, style='Toolbar.TButton').pack(side=tk.LEFT, padx=3)
        ttk.Button(self.toolbar_frame, text=f'{ICON_CLOSE} Finish (Esc)', command=self.on_escape, style='ToolbarDanger.TButton').pack(side=tk.LEFT, padx=3)

    def show_color_palette(self, event):
        if hasattr(self, 'palette_window') and self.palette_window.winfo_exists():
            self.palette_window.destroy()
            return
        self.palette_window = tk.Toplevel(self.root)
        self.palette_window.attributes('-topmost', True)
        self.palette_window.overrideredirect(True)
        self.palette_window.configure(bg=COLOR_BG_DARK, bd=2, relief=tk.RAISED)
        x = self.color_button.winfo_rootx() - 100
        y = self.color_button.winfo_rooty() + self.color_button.winfo_height()
        palette_width = 320
        palette_height = 120
        self.palette_window.geometry(f'{palette_width}x{palette_height}+{x}+{y}')
        colors = ['red', 'orange', 'yellow', 'lime', 'green', 'cyan', 'blue', 'purple', 'magenta', 'pink', 'white', 'black', 'gray', 'brown']
        colors_frame = tk.Frame(self.palette_window, bg=COLOR_BG_DARK)
        colors_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        for i, color in enumerate(colors):
            row = i // 7
            col = i % 7
            color_btn = tk.Label(colors_frame, bg=color, width=4, height=2, relief=tk.RAISED, bd=2, cursor='hand2')
            color_btn.grid(row=row, column=col, padx=2, pady=2)
            color_btn.bind('<Button-1>', lambda e, c=color: self.select_color(c))
            if color == self.draw_color:
                color_btn.config(relief=tk.SUNKEN, bd=3)
        self.palette_window.bind('<FocusOut>', lambda e: self.palette_window.destroy())
        self.palette_window.focus_set()

    def select_color(self, color):
        self.draw_color = color
        self.color_button.config(bg=self.draw_color)
        if hasattr(self, 'palette_window') and self.palette_window.winfo_exists():
            self.palette_window.destroy()

    def update_tool_size_from_scale(self, value):
        new_size = int(float(value))
        if self.size_label:
            self.size_label.config(text=str(new_size))
        if self.mode == 'DRAW_TEXT':
            self.text_mode_font_size = new_size
        elif self.mode == 'DRAW_BLUR':
            self.blur_radius = new_size // 2
        else:
            self.brush_size = new_size

    def set_mode(self, new_mode):
        if self.mode == 'MOVE_ITEM':
            self.moving_item_index = None
            self._unbind_move_item_events()
        if hasattr(self, 'palette_window') and self.palette_window and self.palette_window.winfo_exists():
            self.palette_window.destroy()
        self.start_x = None
        self.start_y = None
        if self.coord_text:
            self.canvas.delete(self.coord_text)
            self.coord_text = None
        self.mode = new_mode
        if self.active_text_box and self.active_text_box.winfo_exists():
            self._finalize_text(None, force=True)
        self._unbind_all()
        self.root.title(f"Annotation Tool - Mode: {new_mode.replace('_', ' ')}")
        if new_mode == 'DRAW_LINE':
            self.canvas.config(cursor='crosshair')
            self._bind_draw_line()
            self.size_scale.set(self.brush_size)
        elif new_mode == 'DRAW_ARROW':
            self.canvas.config(cursor='tcross')
            self._bind_draw_arrow()
            self.size_scale.set(self.brush_size)
        elif new_mode == 'SELECT':
            self.canvas.config(cursor='tcross')
            self._bind_select_mode()
            self.size_scale.set(self.brush_size)
        elif new_mode == 'DRAW_TEXT':
            self.canvas.config(cursor='tcross')
            self._bind_draw_text()
            self.size_scale.set(self.text_mode_font_size)
        elif new_mode == 'DRAW_BLUR':
            self.canvas.config(cursor='tcross')
            self._bind_draw_blur()
            self.size_scale.set(self.blur_radius * 2)
        elif new_mode == 'MOVE_ITEM':
            self.canvas.config(cursor='fleur')
            self._bind_move_item_events()
            self.size_scale.set(self.brush_size)
        self._update_toolbar_styles()

    def _update_toolbar_styles(self):
        for btn in [self.btn_brush, self.btn_arrow, self.btn_select, self.btn_text, self.btn_blur, self.btn_move]:
            btn.config(style='Toolbar.TButton')
        if self.mode == 'DRAW_LINE':
            self.btn_brush.config(style='ToolbarActive.TButton')
        elif self.mode == 'DRAW_ARROW':
            self.btn_arrow.config(style='ToolbarActive.TButton')
        elif self.mode == 'SELECT':
            self.btn_select.config(style='ToolbarActive.TButton')
        elif self.mode == 'DRAW_TEXT':
            self.btn_text.config(style='ToolbarActive.TButton')
        elif self.mode == 'DRAW_BLUR':
            self.btn_blur.config(style='ToolbarActive.TButton')
        elif self.mode == 'MOVE_ITEM':
            self.btn_move.config(style='ToolbarActive.TButton')

    def _bind_events(self):
        self.root.bind('<Control-z>', self.undo_last_action)
        self.root.bind('<Escape>', self.on_escape)

    def _unbind_all(self):
        for event_name in ['<Button-1>', '<B1-Motion>', '<ButtonRelease-1>']:
            self.canvas.unbind(event_name)

    def _bind_draw_line(self):
        self.canvas.bind('<Button-1>', self.on_line_press)
        self.canvas.bind('<B1-Motion>', self.on_line_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_line_release)

    def _bind_draw_arrow(self):
        self.canvas.bind('<Button-1>', self.on_arrow_press)
        self.canvas.bind('<B1-Motion>', self.on_arrow_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_arrow_release)

    def _bind_draw_text(self):
        self.canvas.bind('<Button-1>', self.on_text_click)

    def _bind_select_mode(self):
        self.canvas.bind('<Button-1>', self.on_select_press)
        self.canvas.bind('<B1-Motion>', self.on_select_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_select_release)
        self.canvas.bind('<Motion>', self.on_select_hover)

    def _bind_draw_blur(self):
        self.canvas.bind('<Button-1>', self.on_blur_press)
        self.canvas.bind('<B1-Motion>', self.on_blur_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_blur_release)

    def _bind_move_item_events(self):
        self.canvas.bind('<Button-1>', self.on_move_press)
        self.canvas.bind('<B1-Motion>', self.on_move_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_move_release)
        self.canvas.config(cursor='fleur')

    def _unbind_move_item_events(self):
        for event_name in ['<Button-1>', '<B1-Motion>', '<ButtonRelease-1>']:
            self.canvas.unbind(event_name)

    def _reconstruct_canvas_state(self):
        self.drawable_image = self.original_image.copy()
        self.draw = ImageDraw.Draw(self.drawable_image)
        self.canvas.delete(tk.ALL)
        self.tk_image = ImageTk.PhotoImage(self.drawable_image)
        self.bg_image_id = self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
        for index, item in enumerate(self.drawing_history):
            fill = item.get('color')
            width = item.get('size')
            canvas_ids = []
            if 'bbox_id' in item and item['bbox_id'] is not None:
                try:
                    self.canvas.delete(item['bbox_id'])
                except:
                    pass
                item['bbox_id'] = None
            if item['type'] == 'line':
                points = item['points']
                self.draw.line(points, fill=fill, width=width, joint='curve')
                line_id = self.canvas.create_line(points, fill=fill, width=width, capstyle=tk.ROUND, smooth=tk.TRUE, splinesteps=12, tags=(f'item_{index}', 'movable_item'))
                canvas_ids.append(line_id)
            elif item['type'] == 'arrow':
                x1, y1, x2, y2 = item['coords']
                self._draw_arrow_on_pil(x1, y1, x2, y2, fill, width)
                ids = self._draw_arrow_on_canvas(x1, y1, x2, y2, fill, width)
                for item_id in ids:
                    self.canvas.addtag_withtag(f'item_{index}', item_id)
                    self.canvas.addtag_withtag('movable_item', item_id)
                canvas_ids.extend(ids)
            elif item['type'] == 'text':
                x, y, text_content, size = (item['coords'][0], item['coords'][1], item['text'], item['size'])
                font = None
                if ImageFont:
                    try:
                        font = ImageFont.truetype('DejaVuSans.ttf', size)
                    except Exception:
                        font = self.draw.font
                outline_width = 1
                for dx, dy in [(outline_width, 0), (-outline_width, 0), (0, outline_width), (0, -outline_width), (outline_width, outline_width), (-outline_width, -outline_width), (outline_width, -outline_width), (-outline_width, -outline_width)]:
                    self.draw.text((x + dx, y + dy), text_content, font=font, fill='black')
                self.draw.text((x, y), text_content, font=font, fill='white')
                if font and text_content:
                    try:
                        bbox = self.draw.textbbox((x, y), text_content, font=font)
                        x1_bbox, y1_bbox, x2_bbox, y2_bbox = bbox
                        bbox_id = self.canvas.create_rectangle(x1_bbox - 5, y1_bbox - 5, x2_bbox + 5, y2_bbox + 5, fill='', outline='', tags=(f'item_{index}', 'movable_item'))
                        item['bbox_id'] = bbox_id
                        canvas_ids.append(bbox_id)
                    except Exception as e:
                        print(f'Error creating hitbox: {e}')
                        pass
            elif item['type'] == 'blur':
                x1, y1, x2, y2, radius = (item['coords'][0], item['coords'][1], item['coords'][2], item['coords'][3], item['radius'])
                x1, y1, x2, y2 = (int(x1), int(y1), int(x2), int(y2))
                region = self.drawable_image.crop((x1, y1, x2, y2))
                blurred_region = region.filter(ImageFilter.GaussianBlur(radius=radius))
                self.drawable_image.paste(blurred_region, (x1, y1))
                rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline='', fill='', tags=(f'item_{index}', 'movable_item'))
                canvas_ids.append(rect_id)
            item['canvas_ids'] = canvas_ids
        self.tk_image = ImageTk.PhotoImage(self.drawable_image)
        self.canvas.itemconfig(self.bg_image_id, image=self.tk_image)
        for item in self.drawing_history:
            for item_id in item.get('canvas_ids', []):
                self.canvas.tag_raise(item_id)
        if self.mode == 'SELECT' and self.rect:
            self.canvas.tag_raise(self.rect)
        self.canvas.update_idletasks()

    def undo_last_action(self, event=None):
        if self.drawing_history:
            if self.active_text_box and self.active_text_box.winfo_exists():
                self.active_text_box.destroy()
                self.active_text_box = None
            self.drawing_history.pop()
            self._reconstruct_canvas_state()
        else:
            print('Drawing history is empty')

    def on_escape(self, event=None):
        if self.active_text_box and self.active_text_box.winfo_exists():
            self._finalize_text(None, force=True)
        self.result_region = None
        self.root.quit()

    def get_region(self):
        self.root.mainloop()
        if self.rect:
            self.canvas.delete(self.rect)
        if self.active_text_box and self.active_text_box.winfo_exists():
            self.active_text_box.destroy()
        self.root.destroy()
        return self.result_region

    def _calculate_arrowhead(self, x1, y1, x2, y2):
        angle = math.atan2(y2 - y1, x2 - x1)
        x3 = x2 - self.arrow_head_length * math.cos(angle - math.radians(self.arrow_head_angle_deg))
        y3 = y2 - self.arrow_head_length * math.sin(angle - math.radians(self.arrow_head_angle_deg))
        x4 = x2 - self.arrow_head_length * math.cos(angle + math.radians(self.arrow_head_angle_deg))
        y4 = y2 - self.arrow_head_length * math.sin(angle + math.radians(self.arrow_head_angle_deg))
        return [x2, y2, x3, y3, x4, y4]

    def _draw_arrow_on_pil(self, x1, y1, x2, y2, fill, width):
        length = math.hypot(x2 - x1, y2 - y1)
        if length < self.arrow_head_length * 1.5:
            if length > 0:
                self.draw.line([(x1, y1), (x2, y2)], fill=fill, width=width)
            return
        dx = x2 - x1
        dy = y2 - y1
        ndx = dx / length
        ndy = dy / length
        line_adjustment = self.arrow_head_length * 0.85
        new_line_end_x = x2 - ndx * line_adjustment
        new_line_end_y = y2 - ndy * line_adjustment
        self.draw.line([(x1, y1), (new_line_end_x, new_line_end_y)], fill=fill, width=width, joint='curve')
        arrowhead_coords = self._calculate_arrowhead(x1, y1, x2, y2)
        if arrowhead_coords:
            arrowhead_points = [(arrowhead_coords[0], arrowhead_coords[1]), (arrowhead_coords[2], arrowhead_coords[3]), (arrowhead_coords[4], arrowhead_coords[5])]
            arrowhead_points_int = [(int(x), int(y)) for x, y in arrowhead_points]
            self.draw.polygon(arrowhead_points_int, fill=fill)

    def _draw_arrow_on_canvas(self, x1, y1, x2, y2, fill, width):
        ids = []
        length = math.hypot(x2 - x1, y2 - y1)
        if length < self.arrow_head_length * 1.5:
            if length > 0:
                line_id = self.canvas.create_line(x1, y1, x2, y2, fill=fill, width=width, capstyle=tk.ROUND)
                ids.append(line_id)
            return ids
        dx = x2 - x1
        dy = y2 - y1
        ndx = dx / length
        ndy = dy / length
        line_adjustment = self.arrow_head_length * 0.85
        new_line_end_x = x2 - ndx * line_adjustment
        new_line_end_y = y2 - ndy * line_adjustment
        line_id = self.canvas.create_line(x1, y1, new_line_end_x, new_line_end_y, fill=fill, width=width, capstyle=tk.ROUND)
        ids.append(line_id)
        arrowhead_coords = self._calculate_arrowhead(x1, y1, x2, y2)
        if arrowhead_coords:
            arrowhead_id = self.canvas.create_polygon(arrowhead_coords, fill=fill, outline=fill)
            ids.append(arrowhead_id)
        return ids

    def on_line_press(self, event):
        if self.mode != 'DRAW_LINE':
            return
        self.current_stroke_points = [(event.x, event.y)]
        self.current_canvas_item = self.canvas.create_line(event.x, event.y, event.x, event.y, fill=self.draw_color, width=self.brush_size, capstyle=tk.ROUND, smooth=tk.TRUE, splinesteps=12)

    def on_line_drag(self, event):
        if self.mode != 'DRAW_LINE' or not self.current_stroke_points:
            return
        self.current_stroke_points.append((event.x, event.y))
        new_coords = [coord for point in self.current_stroke_points for coord in point]
        self.canvas.coords(self.current_canvas_item, *new_coords)

    def on_line_release(self, event):
        if self.mode != 'DRAW_LINE' or len(self.current_stroke_points) < 2:
            if self.current_canvas_item:
                self.canvas.delete(self.current_canvas_item)
            self.current_stroke_points = []
            self.current_canvas_item = None
            return
        self.draw.line(self.current_stroke_points, fill=self.draw_color, width=self.brush_size, joint='curve')
        self.drawing_history.append({'type': 'line', 'points': self.current_stroke_points, 'color': self.draw_color, 'size': self.brush_size})
        self._reconstruct_canvas_state()
        self.current_stroke_points = []
        self.current_canvas_item = None

    def on_arrow_press(self, event):
        if self.mode != 'DRAW_ARROW':
            return
        self.start_x, self.start_y = (event.x, event.y)
        if self.current_canvas_item:
            for item_id in self.current_canvas_item:
                self.canvas.delete(item_id)
            self.current_canvas_item = None

    def on_arrow_drag(self, event):
        if self.mode != 'DRAW_ARROW':
            return
        if self.current_canvas_item:
            for item_id in self.current_canvas_item:
                self.canvas.delete(item_id)
            self.current_canvas_item = None
        self.current_canvas_item = self._draw_arrow_on_canvas(self.start_x, self.start_y, event.x, event.y, self.draw_color, self.brush_size)

    def on_arrow_release(self, event):
        if self.mode != 'DRAW_ARROW':
            return
        if self.current_canvas_item:
            for item_id in self.current_canvas_item:
                self.canvas.delete(item_id)
            self.current_canvas_item = None
        end_x, end_y = (event.x, event.y)
        if math.hypot(self.start_x - end_x, self.start_y - end_y) > 10:
            self._draw_arrow_on_pil(self.start_x, self.start_y, end_x, end_y, self.draw_color, self.brush_size)
            self.drawing_history.append({'type': 'arrow', 'coords': (self.start_x, self.start_y, end_x, end_y), 'color': self.draw_color, 'size': self.brush_size})
            self._reconstruct_canvas_state()

    def on_select_hover(self, event):
        if self.mode != 'SELECT':
            return
        if self.start_x is None:
            if self.coord_text:
                self.canvas.delete(self.coord_text)
            coord_str = f'X ({event.x}, {event.y})'
            self.coord_text = self.canvas.create_text(event.x, event.y - 20, text=coord_str, fill='orange', font=('Cantarell', 12, 'bold'), anchor=tk.S)

    def on_select_press(self, event):
        if self.mode != 'SELECT':
            return
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline=COLOR_ACCENT, width=2, fill='', dash=(6, 4))
        self.canvas.tag_raise(self.rect)
        if self.coord_text:
            self.canvas.delete(self.coord_text)
        coord_str = f'Start: ({self.start_x}, {self.start_y})'
        self.coord_text = self.canvas.create_text(self.start_x, self.start_y - 10, text=coord_str, fill='orange', font=('Cantarell', 12, 'bold'), anchor=tk.SW)
        self.canvas.tag_raise(self.rect)
        if self.coord_text:
            self.canvas.delete(self.coord_text)
        coord_str = f'Start: ({self.start_x}, {self.start_y})'
        self.coord_text = self.canvas.create_text(self.start_x, self.start_y - 10, text=coord_str, fill='orange', font=('Cantarell', 12, 'bold'), anchor=tk.SW)

    def on_select_drag(self, event):
        if self.mode != 'SELECT':
            return
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
        if self.coord_text:
            width = abs(event.x - self.start_x)
            height = abs(event.y - self.start_y)
            coord_str = f'X ({self.start_x}, {self.start_y}) | Y ({event.x}, {event.y})'
            text_x = min(self.start_x, event.x)
            text_y = min(self.start_y, event.y) - 10
            self.canvas.coords(self.coord_text, text_x, text_y)
            self.canvas.itemconfig(self.coord_text, text=coord_str)

    def on_select_release(self, event):
        if self.mode != 'SELECT':
            return
        self.end_x = event.x
        self.end_y = event.y
        x1 = min(self.start_x, self.end_x)
        y1 = min(self.start_y, self.end_y)
        x2 = max(self.start_x, self.end_x)
        y2 = max(self.start_y, self.end_y)
        if self.coord_text:
            self.canvas.delete(self.coord_text)
            self.coord_text = None
        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
            self.result_region = (x1, y1, x2, y2)
        else:
            self.result_region = None
        self.root.quit()

    def on_blur_press(self, event):
        if self.mode != 'DRAW_BLUR':
            return
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline=COLOR_ACCENT, width=2, fill='', dash=(6, 4))
        self.canvas.tag_raise(self.rect)

    def on_blur_drag(self, event):
        if self.mode != 'DRAW_BLUR':
            return
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_blur_release(self, event):
        if self.mode != 'DRAW_BLUR':
            return
        self.end_x = event.x
        self.end_y = event.y
        x1 = min(self.start_x, self.end_x)
        y1 = min(self.start_y, self.end_y)
        x2 = max(self.start_x, self.end_x)
        y2 = max(self.start_y, self.end_y)
        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
            region = self.drawable_image.crop((x1, y1, x2, y2))
            blurred_region = region.filter(ImageFilter.GaussianBlur(radius=self.blur_radius))
            self.drawable_image.paste(blurred_region, (x1, y1))
            self.drawing_history.append({'type': 'blur', 'coords': (x1, y1, x2, y2), 'radius': self.blur_radius})
            self._reconstruct_canvas_state()
        if self.rect:
            self.canvas.delete(self.rect)
            self.rect = None

    def on_text_click(self, event):
        if self.mode != 'DRAW_TEXT':
            return
        clicked_items = self.canvas.find_overlapping(event.x - 5, event.y - 5, event.x + 5, event.y + 5)
        is_movable = False
        for item in clicked_items:
            if 'movable_item' in self.canvas.gettags(item):
                is_movable = True
                break
        if is_movable:
            if self.active_text_box and self.active_text_box.winfo_exists():
                self._finalize_text(None, force=True)
            self.mode_before_move = 'DRAW_TEXT'
            self.mode = 'MOVE_ITEM'
            self._unbind_all()
            self._bind_move_item_events()
            self.on_move_press(event)
            return
        if self.active_text_box and self.active_text_box.winfo_exists():
            self._finalize_text(None, force=True)
        self.start_x, self.start_y = (event.x, event.y)
        font_name = FONT_MAIN[0]
        size = self.text_mode_font_size
        font_tuple = (font_name, size)
        entry = tk.Entry(self.root, font=font_tuple, fg='white', bg='black', insertbackground='white', bd=0, highlightthickness=1, highlightbackground=COLOR_ACCENT)
        entry.place(x=self.start_x, y=self.start_y, anchor=tk.NW)
        entry.focus_set()
        self.active_text_box = entry
        entry.bind('<Return>', lambda e: self._finalize_text(e, force=True))
        entry.bind('<FocusOut>', lambda e: self._handle_focus_out(e))

    def _handle_focus_out(self, event):
        if not self.active_text_box or not self.active_text_box.winfo_exists():
            return
        widget_with_focus = self.root.focus_get()
        if widget_with_focus is not None and self.toolbar_frame.winfo_contains(widget_with_focus):
            return
        self._finalize_text(None, force=True)

    def _finalize_text(self, event, force=False):
        if not self.active_text_box or not self.active_text_box.winfo_exists():
            return
        text_content = self.active_text_box.get()
        if not text_content:
            self.active_text_box.destroy()
            self.active_text_box = None
            return
        x, y = (self.active_text_box.winfo_x(), self.active_text_box.winfo_y())
        size = self.text_mode_font_size
        self.drawing_history.append({'type': 'text', 'text': text_content, 'coords': (x, y), 'size': size, 'font': FONT_MAIN[0]})
        self.active_text_box.destroy()
        self.active_text_box = None
        self._reconstruct_canvas_state()

    def on_move_press(self, event):
        if self.mode != 'MOVE_ITEM':
            return
        self.move_origin_x, self.move_origin_y = (event.x, event.y)
        clicked_items = self.canvas.find_overlapping(event.x - 5, event.y - 5, event.x + 5, event.y + 5)
        item_id = None
        for item in clicked_items:
            tags = self.canvas.gettags(item)
            if 'movable_item' in tags:
                item_id = item
                break
        if not item_id:
            self.moving_item_index = None
            return
        self.moving_item_index = None
        for tag in self.canvas.gettags(item_id):
            if tag.startswith('item_'):
                try:
                    self.moving_item_index = int(tag.split('_')[1])
                    break
                except ValueError:
                    continue
        if self.moving_item_index is not None and self.moving_item_index < len(self.drawing_history):
            moving_item = self.drawing_history[self.moving_item_index]
            if moving_item['type'] == 'text':
                self.moving_item_original_coords = list(moving_item['coords'])
            elif moving_item['type'] == 'line':
                self.moving_item_original_coords = [list(p) for p in moving_item.get('points', [])]
            elif moving_item['type'] == 'arrow':
                self.moving_item_original_coords = list(moving_item.get('coords', []))
            elif moving_item['type'] == 'blur':
                self.moving_item_original_coords = list(moving_item.get('coords', []))
        else:
            self.moving_item_index = None

    def on_move_drag(self, event):
        if self.mode != 'MOVE_ITEM' or self.moving_item_index is None:
            return
        dx = event.x - self.move_origin_x
        dy = event.y - self.move_origin_y
        moving_item = self.drawing_history[self.moving_item_index]
        original_coords = self.moving_item_original_coords
        if moving_item['type'] == 'text':
            new_x = original_coords[0] + dx
            new_y = original_coords[1] + dy
            moving_item['coords'] = (new_x, new_y)
        elif moving_item['type'] == 'line':
            new_points = []
            for x, y in original_coords:
                new_points.append((x + dx, y + dy))
            moving_item['points'] = new_points
        elif moving_item['type'] == 'arrow':
            new_coords = (original_coords[0] + dx, original_coords[1] + dy, original_coords[2] + dx, original_coords[3] + dy)
            moving_item['coords'] = new_coords
        elif moving_item['type'] == 'blur':
            new_coords = (original_coords[0] + dx, original_coords[1] + dy, original_coords[2] + dx, original_coords[3] + dy)
            moving_item['coords'] = new_coords
        self._reconstruct_canvas_state()

    def on_move_release(self, event):
        if self.mode != 'MOVE_ITEM':
            return
        self.moving_item_index = None
        self.moving_item_original_coords = None
        self.move_origin_x = None
        self.move_origin_y = None
        self.set_mode(self.mode_before_move)

class App(tk.Tk):

    def __init__(self, sharex_app):
        super().__init__()
        self.sharex_app = sharex_app
        self.sharex_app.root = self
        self.title('Sharnix')
        self.geometry('800x600')
        self.configure(bg=COLOR_BG_DARK)
        try:
            icon_path = Path(__file__).parent / 'ico.png'
            if icon_path.exists():
                icon_image = tk.PhotoImage(file=str(icon_path))
                self.iconphoto(True, icon_image)
        except Exception as e:
            print(f'Start: {e}')
        self.style = ttk.Style(self)
        self._setup_style()
        self._setup_main_ui()
        self._bind_hotkeys()
        self.sharex_app.start_global_listener()
        self.after(500, self.sharex_app.show_first_launch_dialog)
        self.protocol('WM_DELETE_WINDOW', self.on_closing)
        self.after(100, self.sharex_app.load_screenshot_list)

    def _setup_style(self):
        self.style.theme_create('dark_theme', parent='alt', settings={'TFrame': {'configure': {'background': COLOR_BG_DARK}}, 'DarkFrame.TFrame': {'configure': {'background': COLOR_BG_DARK}}, 'TButton': {'configure': {'background': COLOR_CONTROL_BG, 'foreground': COLOR_FG_LIGHT, 'relief': 'flat', 'font': FONT_MAIN, 'padding': [10, 5]}}, 'TLabel': {'configure': {'background': COLOR_BG_DARK, 'foreground': COLOR_FG_LIGHT, 'font': FONT_MAIN}}, 'DarkLabel.TLabel': {'configure': {'background': COLOR_BG_DARK, 'foreground': COLOR_FG_LIGHT, 'font': FONT_MAIN}}, 'TLabelframe': {'configure': {'background': COLOR_BG_DARK, 'foreground': COLOR_FG_LIGHT, 'font': FONT_HEADER, 'relief': 'groove', 'borderwidth': 2, 'bordercolor': COLOR_BORDER}}, 'DarkLabelFrame.TLabelframe': {'configure': {'background': COLOR_BG_DARK, 'foreground': COLOR_FG_LIGHT, 'font': FONT_HEADER}}, 'TEntry': {'configure': {'background': COLOR_CONTROL_BG, 'foreground': COLOR_FG_LIGHT, 'fieldbackground': COLOR_CONTROL_BG, 'borderwidth': 1, 'relief': 'flat', 'font': FONT_MAIN}}, 'TCheckbutton': {'configure': {'background': COLOR_BG_DARK, 'foreground': COLOR_FG_LIGHT, 'font': FONT_MAIN}}, 'TRadiobutton': {'configure': {'background': COLOR_BG_DARK, 'foreground': COLOR_FG_LIGHT, 'font': FONT_MAIN}}, 'TScale': {'configure': {'background': COLOR_BG_DARK, 'sliderrelief': 'flat', 'troughcolor': COLOR_CONTROL_BG, 'sliderthickness': 10}}, 'TScrollbar': {'configure': {'background': COLOR_CONTROL_BG, 'troughcolor': COLOR_BG_DARK, 'gripcount': 0, 'bordercolor': COLOR_BG_DARK, 'relief': 'flat'}}})
        self.style.theme_use('dark_theme')
        self.style.map('Accent.TButton', background=[('active', COLOR_ACCENT), ('!disabled', COLOR_ACCENT)], foreground=[('active', 'white'), ('!disabled', 'white')])
        self.style.map('Toolbar.TButton', background=[('active', COLOR_ACCENT)], foreground=[('active', 'white')])
        self.style.map('ToolbarDanger.TButton', background=[('active', COLOR_DANGER)], foreground=[('active', 'white')])
        self.style.configure('ToolbarActive.TButton', background=COLOR_ACCENT, foreground='white', borderwidth=2, relief='solid', bordercolor=COLOR_ACCENT)
        self.style.map('ToolbarActive.TButton', background=[('active', COLOR_ACCENT)])
        self.style.configure('Card.TFrame', background=COLOR_CONTROL_BG, borderwidth=1, relief='flat')
        self.style.configure('CardHover.TFrame', background=COLOR_BORDER)
        self.style.configure('FloatingToolbar.TFrame', background=COLOR_CONTROL_BG, borderwidth=1, relief='raised')
        self.style.configure('BlackCanvas.TFrame', background='black')

    def _setup_main_ui(self):
        main_padding_frame = ttk.Frame(self, padding='15', style='DarkFrame.TFrame')
        main_padding_frame.pack(fill=tk.BOTH, expand=True)
        side_bar = ttk.Frame(main_padding_frame, style='DarkFrame.TFrame')
        side_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        ttk.Label(side_bar, text='📀 Sharnix', font=FONT_HEADER, foreground=COLOR_ACCENT).pack(pady=(0, 15), anchor='n')
        ttk.Button(side_bar, text=f'{ICON_SELECT} Region Screenshot', command=lambda: self.sharex_app.root.after(0, self.sharex_app.take_region_screenshot), style='Accent.TButton').pack(fill=tk.X, pady=5)
        ttk.Button(side_bar, text=f'{ICON_FULLSCREEN} Fullscreen', command=lambda: self.sharex_app.take_fullscreen_screenshot(), style='Toolbar.TButton').pack(fill=tk.X, pady=5)
        ttk.Button(side_bar, text=f'{ICON_FOLDER} Folder', command=self.sharex_app.open_screenshot_folder, style='Toolbar.TButton').pack(fill=tk.X, pady=5)
        ttk.Button(side_bar, text=f'{ICON_SETTINGS} Config', command=self.sharex_app.open_config_file, style='Toolbar.TButton').pack(fill=tk.X, pady=5)
        gallery_area_frame = ttk.Frame(main_padding_frame, style='DarkFrame.TFrame')
        gallery_area_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sharex_app.gallery_canvas = tk.Canvas(gallery_area_frame, bg=COLOR_BG_DARK, highlightthickness=0)
        self.sharex_app.gallery_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll = ttk.Scrollbar(gallery_area_frame, orient=tk.VERTICAL, command=self.sharex_app.gallery_canvas.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.sharex_app.gallery_canvas.config(yscrollcommand=v_scroll.set)
        self.sharex_app.gallery_frame = ttk.Frame(self.sharex_app.gallery_canvas, style='DarkFrame.TFrame')
        self.sharex_app.gallery_canvas.create_window((0, 0), window=self.sharex_app.gallery_frame, anchor=tk.NW, tags='window')
        self.sharex_app.gallery_frame.bind('<Configure>', lambda e: self.sharex_app.gallery_canvas.config(scrollregion=self.sharex_app.gallery_canvas.bbox('all')))
        self.sharex_app.gallery_canvas.bind('<Configure>', self._on_canvas_configure)
        self.sharex_app.gallery_canvas.bind('<MouseWheel>', self.sharex_app._on_scroll_event)
        self.sharex_app.gallery_canvas.bind('<Button-4>', self.sharex_app._on_scroll_event)
        self.sharex_app.gallery_canvas.bind('<Button-5>', self.sharex_app._on_scroll_event)
        self.sharex_app.gallery_frame.bind('<MouseWheel>', self.sharex_app._on_scroll_event)
        self.sharex_app.gallery_frame.bind('<Button-4>', self.sharex_app._on_scroll_event)
        self.sharex_app.gallery_frame.bind('<Button-5>', self.sharex_app._on_scroll_event)
        self._check_pending_screenshot()

    def _on_canvas_configure(self, event):
        canvas_width = event.width
        window_items = self.sharex_app.gallery_canvas.find_withtag('window')
        if window_items:
            window_item_id = window_items[0]
            self.sharex_app.gallery_canvas.itemconfigure(window_item_id, width=canvas_width)

    def _check_pending_screenshot(self):
        if self.sharex_app.pending_screenshot:
            self.sharex_app.pending_screenshot = False
            self.sharex_app.take_region_screenshot()
        self.after(100, self._check_pending_screenshot)

    def _bind_hotkeys(self):
        try:
            region_key = self.sharex_app.config['hotkeys']['region']
            self.bind(region_key, lambda e: threading.Thread(target=self.sharex_app.take_region_screenshot, daemon=True).start())
        except tk.TclError as e:
            print(f'Warning: Hotkey binding failed for region screenshot. Check key format: {e}')

    def on_closing(self):
        self.sharex_app.stop_global_listener()
        self.destroy()

    def reload_hotkeys(self):
        print('Reloading hotkeys...')
        self.stop_global_listener()
        time.sleep(0.1)
        self.start_global_listener()
        print('Hotkeys reloaded')
if __name__ == '__main__':
    if ImageFont is None:
        print('Error: The Pillow library (PIL) with font support is required. Install it with the command: pip install Pillow')
        sys.exit(1)
    if len(sys.argv) > 1:
        app_logic = Sharnix_Linux()
        if sys.argv[1] == '--region':
            root = tk.Tk()
            root.withdraw()
            root.attributes('-alpha', 0.0)
            root.geometry('1x1+0+0')
            app_logic.root = root
            root.after(100, app_logic.take_region_screenshot)
            root.mainloop()
            sys.exit(0)
        elif sys.argv[1] == '--fullscreen':
            print('Fullscreen mode not implemented yet')
            sys.exit(0)
    app_logic = Sharnix_Linux()
    app_ui = App(app_logic)
    app_ui.mainloop()