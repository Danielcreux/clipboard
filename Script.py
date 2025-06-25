import os
import re
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageGrab, ImageTk, ImageEnhance, ImageFilter
import pytesseract
import pyperclip
import numpy as np
import cv2
from datetime import datetime
import urllib.request
import tempfile
import threading
import webbrowser
from typing import Optional, Union, Dict, List  # Según necesites

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class OCRApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TextSnap - Capturador de Texto")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Configuración de estilo
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TButton', font=('Arial', 10), padding=6)
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        self.style.map('Accent.TButton', background=[('active', '#0052cc'), ('!disabled', '#0066ff')])
        
        self.setup_ui()
        self.check_dependencies()
        
    def setup_ui(self):
        """Configura la interfaz de usuario principal"""
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Logo/Header
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.logo_label = ttk.Label(
            self.header_frame, 
            text="📷 TextSnap", 
            font=('Arial', 16, 'bold'),
            foreground='#0066ff'
        )
        self.logo_label.pack(side=tk.LEFT)
        
        # Botón de configuración
        self.settings_btn = ttk.Button(
            self.header_frame,
            text="⚙️",
            command=self.show_settings,
            width=3,
            style='Toolbutton'
        )
        self.settings_btn.pack(side=tk.RIGHT)
        
        # Panel principal
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            self.content_frame,
            text="Captura texto de cualquier parte de tu pantalla",
            justify=tk.CENTER
        ).pack(pady=(0, 20))
        
        # Botón principal
        self.capture_btn = ttk.Button(
            self.content_frame,
            text="Iniciar Captura",
            command=self.start_capture,
            style='Accent.TButton',
            width=20
        )
        self.capture_btn.pack(pady=10)
        
        # Panel de estado
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="Listo",
            foreground='#666666'
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Variables de estado
        self.capture_window = None
        self.preview_window = None
        self.screenshot = None
        self.lang = 'spa'
        
    def is_tesseract_available(self):
        try:
            output = subprocess.check_output([pytesseract.pytesseract.tesseract_cmd, "--version"])
            return b"tesseract" in output.lower()
        except Exception:
            return False
            
    def check_dependencies(self):
        """Verifica e instala dependencias necesarias"""
        try:
            pytesseract.get_tesseract_version()
        except EnvironmentError:
            self.install_tesseract()
            return
            
        self.check_language_data()
        
    def check_language_data(self):
        """Verifica si los datos de lenguaje están instalados"""
        try:
            langs = pytesseract.get_languages(config='')
            if self.lang not in langs:
                self.install_language_data()
        except:
            self.install_language_data()
    
    def install_tesseract(self):
        """Guía al usuario para instalar Tesseract"""
        resp = messagebox.askyesno(
            "Tesseract no encontrado",
            "Se requiere Tesseract OCR para funcionar.\n\n"
            "¿Deseas abrir la página de descarga ahora?",
            parent=self.root
        )
        
        if resp:
            webbrowser.open("https://github.com/UB-Mannheim/tesseract/wiki")
        self.root.destroy()
    
    def install_language_data(self):
        """Descarga e instala los datos de lenguaje"""
        progress = tk.Toplevel(self.root)
        progress.title("Instalando idioma...")
        progress.geometry("300x150")
        progress.resizable(False, False)
        
        ttk.Label(
            progress,
            text="Instalando datos de lenguaje para español...",
            justify=tk.CENTER
        ).pack(pady=(20, 10))
        
        progress_bar = ttk.Progressbar(progress, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        progress_bar.start()
        
        def download_thread():
            try:
                # Descargar archivo
                url = "https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata"
                tessdata_path = os.path.join(os.path.dirname(pytesseract.pytesseract.tesseract_cmd), 'tessdata')
                
                if not os.path.exists(tessdata_path):
                    os.makedirs(tessdata_path)
                
                dest_file = os.path.join(tessdata_path, 'spa.traineddata')
                urllib.request.urlretrieve(url, dest_file)
                
                progress.destroy()
                messagebox.showinfo("Éxito", "Idioma español instalado correctamente", parent=self.root)
            except Exception as e:
                progress.destroy()
                messagebox.showerror("Error", f"No se pudo instalar: {str(e)}", parent=self.root)
                self.root.destroy()
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def start_capture(self):
        """Inicia el proceso de captura de pantalla"""
        self.root.withdraw()
        
        self.capture_window = tk.Toplevel()
        self.capture_window.attributes('-fullscreen', True)
        self.capture_window.attributes('-alpha', 0.3)
        self.capture_window.attributes('-topmost', True)
        self.capture_window.configure(bg='black')
        
        self.capture_canvas = tk.Canvas(self.capture_window, cursor="cross", bg='grey11')
        self.capture_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Instrucciones
        self.instructions = tk.Label(
            self.capture_window,
            text="Arrastra para seleccionar área (ESC para cancelar)",
            bg='black', fg='white', font=('Arial', 12)
        )
        self.instructions.place(relx=0.5, rely=0.1, anchor=tk.CENTER)
        
        # Variables de selección
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        # Bind eventos
        self.capture_canvas.bind("<ButtonPress-1>", self.on_press)
        self.capture_canvas.bind("<B1-Motion>", self.on_drag)
        self.capture_canvas.bind("<ButtonRelease-1>", self.on_release)
        self.capture_window.bind("<Escape>", lambda e: self.cancel_capture())
    
    def on_press(self, event):
        """Manejador de inicio de selección"""
        self.start_x = event.x
        self.start_y = event.y
        
        if not self.rect:
            self.rect = self.capture_canvas.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y,
                outline='red', width=2, fill='white')
    
    def on_drag(self, event):
        """Manejador de arrastre de selección"""
        self.capture_canvas.coords(
            self.rect,
            self.start_x, self.start_y,
            event.x, event.y)
    
    def on_release(self, event):
        """Manejador de fin de selección"""
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        
        # Validar tamaño mínimo
        if abs(x2 - x1) < 20 or abs(y2 - y1) < 20:
            messagebox.showwarning("Selección pequeña", "Por favor selecciona un área más grande", parent=self.capture_window)
            return
        
        self.capture_area(x1, y1, x2, y2)
        self.cancel_capture()
    
    def capture_area(self, x1, y1, x2, y2):
        """Captura el área seleccionada"""
        self.screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        self.show_preview()
    
    def show_preview(self):
        """Muestra la vista previa con opciones"""
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.title("Vista Previa - TextSnap")
        self.preview_window.geometry("600x500")
        self.preview_window.resizable(False, False)
        
        # Mostrar imagen
        img_tk = ImageTk.PhotoImage(self.screenshot)
        img_label = tk.Label(self.preview_window, image=img_tk)
        img_label.image = img_tk
        img_label.pack(pady=(20, 10), padx=20)
        
        # Panel de botones
        btn_frame = ttk.Frame(self.preview_window)
        btn_frame.pack(pady=10)
        
        ttk.Button(
            btn_frame,
            text="Copiar Texto",
            command=self.copy_text,
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Guardar Imagen",
            command=self.save_image
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cerrar",
            command=self.close_preview
        ).pack(side=tk.LEFT, padx=5)
        
        # Mostrar texto extraído
        self.text_frame = ttk.Frame(self.preview_window)
        self.text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        ttk.Label(
            self.text_frame,
            text="Texto Extraído:",
            font=('Arial', 10, 'bold')
        ).pack(anchor=tk.W)
        self.text_display = tk.Text(
            self.text_frame,
            wrap=tk.WORD,
            height=10,
            padx=5,
            pady=5,
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white'
        )

        self.text_display.pack(fill=tk.BOTH, expand=True)
        
        # Procesar imagen y extraer texto en segundo plano
        self.processing_label = ttk.Label(
            self.text_frame,
            text="Procesando imagen...",
            foreground='#666666'
        )
        self.processing_label.pack(pady=5)
        
        threading.Thread(target=self.process_image, daemon=True).start()
    
    def process_image(self):
        """Procesa la imagen y extrae texto con manejo robusto de errores"""
        try:
            # 1. Validación inicial de la imagen
            if not hasattr(self, 'screenshot') or self.screenshot is None:
                raise ValueError("No hay imagen para procesar")

            # 2. Preprocesamiento mejorado
            img = self.screenshot.convert('L')  # Escala de grises
            
            # Redimensionamiento óptimo (mejor que bajar resolución)
            base_width = 800
            wpercent = (base_width / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            img = img.resize((base_width, hsize), Image.LANCZOS)

            # 3. Mejorar contraste y nitidez
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            img = img.filter(ImageFilter.SHARPEN)

            # 4. Binarización adaptativa con OpenCV
            img_array = np.array(img)
            img_array = cv2.adaptiveThreshold(
                img_array, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 31, 2
            )

            # 5. Configuración Tesseract ultra-robusta
            lang = getattr(self, 'lang', 'eng')  # Default a inglés si no está definido
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_blacklist=|\\~<> -c preserve_interword_spaces=1 -l {}'.format(lang)

            # 6. Procesamiento OCR con validación
            text = pytesseract.image_to_string(
                Image.fromarray(img_array),
                config=custom_config,
                timeout=15  # Timeout para evitar bloqueos
            )

            # 7. Validación estricta del resultado
            if not text or text.strip() in ['|', '']:
                raise ValueError("OCR devolvió resultado vacío o inválido")

            # 8. Post-procesamiento inteligente
            text = self._clean_ocr_text(text)

            # 9. Mostrar resultados
            self._display_results(text)

        except pytesseract.TesseractError as te:
            self._handle_error(f"Error Tesseract: {str(te)}")
        except Exception as e:
            self._handle_error(f"Error: {str(e) if str(e) else 'Error desconocido'}")

    def _clean_ocr_text(self, text):
        """Limpia profundamente el texto OCR con múltiples capas de corrección"""
        if not text:
            return ""

        # Capa 1: Corrección de caracteres malinterpretados
        char_corrections = {
            '[': '(', ']': ')', '{': '(', '}': ')', '|': 'I', '\\': '/',
            '´': "'", '‘': "'", '“': '"', '”': '"', '¬': '-', '¦': 'I',
            'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬀ': 'ff', 'ﬃ': 'ffi', 'ﬄ': 'ffl'
        }
        for wrong, right in char_corrections.items():
            text = text.replace(wrong, right)

        # Capa 2: Normalización de espacios y puntuación
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)  # Espacios antes
        text = re.sub(r'([.,;:!?])([^\s])', r'\1 \2', text)  # Espacios después
        text = re.sub(r'\s+', ' ', text)  # Múltiples espacios

        # Capa 3: Corrección de patrones específicos (códigos, números)
        text = re.sub(r'(\d)\s*([.,])\s*(\d)', r'\1\2\3', text)  # Decimales
        text = re.sub(r'([a-zA-Z])\s*([.,])\s*([a-zA-Z])', r'\1\2 \3', text)  # Abreviaturas

        # Capa 4: Formateo de listas y secciones
        text = re.sub(r'^(\d+)\s', r'\1. ', text, flags=re.MULTILINE)  # Numeración
        text = re.sub(r'(?<=\n)([A-Z][a-z]+):', r'\n\1:', text)  # Encabezados

        # Capa 5: Correcciones específicas para español
        spanish_fixes = {
            ' q ': ' que ', ' x ': ' por ', ' dl ': ' del ', ' 1a ': ' la ',
            ' d ': ' de ', ' m ': ' más ', ' tb ': ' también '
        }
        for error, fix in spanish_fixes.items():
            text = text.replace(error, fix)

        # Capa 6: Normalización final de saltos
        text = re.sub(r'\n\s+\n', '\n\n', text)  # Múltiples saltos
        return text.strip()
    def _display_results(self, text):
        """Muestra los resultados en la UI"""
        self.text_display.after(0, lambda: [
            self.text_display.delete(1.0, tk.END),
            self.text_display.insert(tk.END, "\n" + text),
            self.processing_label.config(text="Procesado correctamente", foreground='green')
        ])

    def _handle_error(self, message):
        """Maneja errores en la UI"""
        self.text_display.after(0, lambda: [
            self.text_display.delete(1.0, tk.END),
            self.text_display.insert(tk.END, "ERROR:\n\n" + message),
            self.processing_label.config(text="Error en procesamiento", foreground='red')
        ])
            
        return text
    def copy_text(self):
        """Copia el texto extraído al portapapeles"""
        text = self.text_display.get(1.0, tk.END).strip()
        if text:
            pyperclip.copy(text)
            messagebox.showinfo("Éxito", "Texto copiado al portapapeles", parent=self.preview_window)
        else:
            messagebox.showwarning("Advertencia", "No hay texto para copiar", parent=self.preview_window)
    
    def save_image(self):
        """Guarda la imagen capturada"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            title="Guardar imagen como",
            initialfile=f"captura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        
        if filename:
            self.screenshot.save(filename)
            messagebox.showinfo("Éxito", f"Imagen guardada como:\n{filename}", parent=self.preview_window)
    
    def close_preview(self):
        """Cierra la ventana de vista previa"""
        if self.preview_window:
            self.preview_window.destroy()
            self.preview_window = None
        self.root.deiconify()
    
    def cancel_capture(self):
        """Cancela el proceso de captura"""
        if self.capture_window:
            self.capture_window.destroy()
            self.capture_window = None
        self.root.deiconify()
    
    def show_settings(self):
        """Muestra la ventana de configuración"""
        settings = tk.Toplevel(self.root)
        settings.title("Configuración - TextSnap")
        settings.geometry("300x200")
        settings.resizable(False, False)
        
        ttk.Label(settings, text="Configuración", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Selector de idioma
        lang_frame = ttk.Frame(settings)
        lang_frame.pack(pady=10, padx=20, fill=tk.X)
        
        ttk.Label(lang_frame, text="Idioma OCR:").pack(side=tk.LEFT)
        
        self.lang_var = tk.StringVar(value=self.lang)
        lang_dropdown = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=['spa', 'eng', 'fra', 'por'],
            state='readonly',
            width=5
        )
        lang_dropdown.pack(side=tk.RIGHT)
        
        # Botón de guardar
        ttk.Button(
            settings,
            text="Guardar Configuración",
            command=lambda: self.save_settings(settings),
            style='Accent.TButton'
        ).pack(pady=20)
    
    def save_settings(self, settings_window):
        """Guarda la configuración"""
        self.lang = self.lang_var.get()
        messagebox.showinfo("Éxito", "Configuración guardada", parent=settings_window)
        settings_window.destroy()
        self.check_language_data()
    
    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = OCRApp()
        app.run()
    except Exception as e:
        messagebox.showerror("Error fatal", f"La aplicación encontró un error:\n{str(e)}")
