# pyinstaller --onefile --windowed --icon=icon.ico --add-data "icon.ico;." --name "js8call-BBS" js8call-BBS-v1.py

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from datetime import datetime, timedelta
import threading
import time
import json
import os
import socket

class JS8CallClient:
    
    def __init__(self, host='127.0.0.1', port=2442):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
    
    def connect(self):
        """Tente de se connecter à JS8Call"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"✓ Connected to JS8Call on {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"✗ Unable to connect to JS8Call: {e}")
            self.connected = False
            return False

    
    def send_message(self, text, frequency=None):
        """Envoie un message via JS8Call"""
        if not self.connected:
            raise Exception("Not connected to JS8Call")
        
        try:
            # Commande JS8Call pour envoyer un message
            command = {
                "type": "TX.SEND_MESSAGE",
                "value": text,
                "params": {
                    "FREQ": frequency if frequency else 0,  # 0 = utilise la fréquence actuelle
                    "SPEED": 0   # Vitesse normale
                }
            }
            
            message = json.dumps(command) + '\n'
            self.socket.send(message.encode('utf-8'))
            return True
            
        except Exception as e:
            print(f"Error sending: {e}")
            self.connected = False
            return False
    
    def set_frequency(self, frequency):
        """Change la fréquence de JS8Call"""
        if not self.connected:
            raise Exception("Not connected to JS8Call")
        
        try:
            command = {
                "type": "RIG.SET_FREQ",
                "value": str(frequency),
                "params": {}
            }
            
            message = json.dumps(command) + '\n'
            self.socket.send(message.encode('utf-8'))
            return True
            
        except Exception as e:
            print(f"Frequency change error: {e}")
            return False
    

    def send_directed_message(self, call, text):
        """Envoie un message vers un indicatif"""
        directed_text = f"{call}: {text}"
        return self.send_message(directed_text)
    
    def disconnect(self):
        """Déconnection"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False

class JS8BulletinBoard:
    def __init__(self, root):
        self.root = root
        self.root.title("JS8Call Bulletin Board")
        self.root.geometry("800x660")

        # icone
        try:
            if os.path.exists('icon.ico'):
                self.root.iconbitmap('icon.ico')
            elif os.path.exists(os.path.join(os.path.dirname(__file__), 'icon.ico')):
                icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
                self.root.iconbitmap(icon_path)
        except Exception as e:
            pass
            #print(f"Impossible de charger l'icône: {e}")

        
        # Variables - LIMITE CONFIGURABLE
        self.max_chars_options = {
            "Short (70 car)": 70,
            "Medium (140 car)": 140,
            "Long (210 car)": 210,
            "Custom": 0
        }
        self.max_chars = 210
        
        # Paramètres JS8Call
        self.js8_host = '127.0.0.1'
        self.js8_port = 2442
        self.js8_frequency = 0  # 0 = utilise la fréquence actuelle de JS8Call
        
        self.autostart_enabled = False
        
        self.emission_active = False
        self.next_emission = None
        self.current_file = None
        self.text_modified_flag = False
        
        # Initialisation JS8Call avec détection automatique
        self.js8_client = None
        self.js8_connected = False
        
        self.setup_ui()
        
        self.load_last_config()
        
        self.detect_and_connect_js8call()
        
        if self.autostart_enabled:
            self.root.after(1000, self.try_autostart)
        
        # Thread surveillance
        self.check_thread = None
        self.running = False
    
    def try_autostart(self):
        """Tente de démarrer automatiquement les émissions"""
        text = self.text_area.get("1.0", tk.END).strip()
        
        if not text:
            self.log_message("Autostart cancelled: empty message", "WARNING")
            return
        
        if len(text) > self.max_chars:
            self.log_message(f"Autostart cancelled: message too long ({len(text)}/{self.max_chars})", "WARNING")
            return
        
        if not self.js8_connected:
            self.log_message("Autostart: Attempting to connect to JS8Call...", "INFO")
            self.reconnect_js8call()
            
            if not self.js8_connected:
                self.log_message("Autostart cancelled: JS8Call not connected", "WARNING")
                messagebox.showwarning(
                    "Autostart - Connection failed",
                    f"Unable to connect to JS8Call on {self.js8_host}:{self.js8_port}\n\n"
                    "Automatic emissions will not start.\n"
                    "Verify that JS8Call is running and the TCP API is enabled.."
                )
                return
        
        # Démarrage automatique
        self.log_message("🚀 AUTOSTART: Automatic start of emissions", "INFO")
        self.start_emissions()
    
    def detect_and_connect_js8call(self):
        """Détecte et se connecte automatiquement à JS8Call"""
        print("Searching for JS8Call...")
        print(f"  Test of {self.js8_host}:{self.js8_port}...")
        
        try:
            client = JS8CallClient(host=self.js8_host, port=self.js8_port)
            if client.connect():
                self.js8_client = client
                self.js8_connected = True
                print(f"✓ JS8Call detected on {self.js8_host}:{self.js8_port}")
                self.update_connection_status()
                return
        except Exception as e:
            print(f"Error: {e}")
        
        print(f"✗ JS8Call not connected on {self.js8_host}:{self.js8_port}")
        self.js8_connected = False
        self.update_connection_status()
    


    def update_connection_status(self):
        """Met à jour l'affichage du statut de connexion"""
        if hasattr(self, 'js8_status_label'):
            if self.js8_connected:
                self.js8_status_label.config(
                    text=f"JS8Call: ✓ Connected ({self.js8_host}:{self.js8_port})",
                    foreground="green"
                )
            else:
                self.js8_status_label.config(
                    text=f"JS8Call: ✗ Not connected ({self.js8_host}:{self.js8_port})",
                    foreground="#ff9900"
                )
    
        if hasattr(self, 'freq_status_label'):
            if self.js8_frequency == 0:
                freq_display = "Auto (uses the current frequency)"
            else:
                freq_mhz = self.js8_frequency / 1000000
                freq_display = f"{self.js8_frequency} Hz ({freq_mhz:.3f} MHz)"
        
            self.freq_status_label.config(text=f"Frequency: {freq_display}")



    
    def reconnect_js8call(self):
        """Tente de reconnecter JS8Call"""
        self.log_message("Attempting to reconnect to JS8Call...")
        
        if self.js8_client:
            self.js8_client.disconnect()
        
        # Utilise les paramètres configurés
        try:
            client = JS8CallClient(host=self.js8_host, port=self.js8_port)
            if client.connect():
                self.js8_client = client
                self.js8_connected = True
                self.log_message("Successful reconnection!")
            else:
                self.js8_connected = False
                self.log_message("Reconnection failed", "ERROR")
        except Exception as e:
            self.js8_connected = False
            self.log_message(f"Reconnection error: {e}", "ERROR")
        
        self.update_connection_status()
    




    def open_settings_window(self):
        """Ouvre la fenêtre de paramètres JS8Call"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("JS8Call settings")
        settings_window.geometry("500x520")  
        settings_window.resizable(False, False)
    
        # Centrer la fenêtre
        settings_window.transient(self.root)
        settings_window.grab_set()
    
        main_frame = ttk.Frame(settings_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
    
        # Connexion TCP
        conn_frame = ttk.LabelFrame(main_frame, text="TCP connection JS8Call", padding="10")
        conn_frame.pack(fill=tk.X, pady=(0, 10))
    
        # Adresse IP
        ttk.Label(conn_frame, text="IP address:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0,10))
        host_var = tk.StringVar(value=self.js8_host)
        host_entry = ttk.Entry(conn_frame, textvariable=host_var, width=20)
        host_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Label(conn_frame, text="(ex: 127.0.0.1 or 192.168.1.10)", foreground="gray", font=("TkDefaultFont", 8)).grid(row=0, column=2, sticky=tk.W, padx=5)
    
        # Port
        ttk.Label(conn_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0,10))
        port_var = tk.StringVar(value=str(self.js8_port))
        port_entry = ttk.Entry(conn_frame, textvariable=port_var, width=10)
        port_entry.grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Label(conn_frame, text="(By default: 2442)", foreground="gray", font=("TkDefaultFont", 8)).grid(row=1, column=2, sticky=tk.W, padx=5)
    
        # Info
        info_label = ttk.Label(
            conn_frame, 
            text="Configuration\n'TCP Server API' in JS8Call\n(File → Settings → Reporting → Enable TCP Server API)",
            foreground="#009999",
            font=("TkDefaultFont", 8),
            justify=tk.LEFT
        )
        info_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))
    
        # Fréquence
        freq_frame = ttk.LabelFrame(main_frame, text="Transmission frequency", padding="10")
        freq_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Checkbox auto AVANT le champ de saisie
        auto_freq_var = tk.BooleanVar(value=(self.js8_frequency == 0))
    
        auto_freq_check = ttk.Checkbutton(
            freq_frame,
            text="Use the current JS8Call frequency (Auto)",
            variable=auto_freq_var
        )
        auto_freq_check.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
    
        # Champ de fréquence
        ttk.Label(freq_frame, text="Fixed frequency (Hz):").grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0,10))
        freq_var = tk.StringVar(value=str(self.js8_frequency) if self.js8_frequency > 0 else "")
        freq_entry = ttk.Entry(freq_frame, textvariable=freq_var, width=15)
        freq_entry.grid(row=1, column=1, sticky=tk.W, padx=5)
        ttk.Label(freq_frame, text="Hz", foreground="gray").grid(row=1, column=2, sticky=tk.W, padx=5)
    
        # Fonction pour activer/désactiver le champ
        def toggle_freq_entry():
            if auto_freq_var.get():
                freq_entry.config(state=tk.DISABLED)
                freq_var.set("")  # Efface le champ
            else:
                freq_entry.config(state=tk.NORMAL)
                freq_entry.focus()
    
        # Configure le callback
        auto_freq_check.config(command=toggle_freq_entry)
    
        # Configure l'état initial
        if auto_freq_var.get():
            freq_entry.config(state=tk.DISABLED)
    
        freq_info_label = ttk.Label(
            freq_frame,
            text="Examples: 7.078 MHz = 7078000 Hz  |  14.078 MHz = 14078000 Hz",
            foreground="#009999",
            font=("TkDefaultFont", 8),
            justify=tk.LEFT
        )
        freq_info_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
    
        # NOUVEAU: Démarrage automatique
        autostart_frame = ttk.LabelFrame(main_frame, text="Automatic start", padding="10")
        autostart_frame.pack(fill=tk.X, pady=(0, 10))
        
        autostart_var = tk.BooleanVar(value=self.autostart_enabled)
        
        autostart_check = ttk.Checkbutton(
            autostart_frame,
            text="Automatically start broadcasts on launch",
            variable=autostart_var
        )
        autostart_check.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        autostart_info = ttk.Label(
            autostart_frame,
            text="If enabled, transmissions start automatically when the application is launched\n(if JS8Call is connected).",
            foreground="#009999",
            font=("TkDefaultFont", 8),
            justify=tk.LEFT
        )
        autostart_info.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
    
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0), side=tk.BOTTOM)
    
        def apply_settings():
            """Applique les nouveaux paramètres"""
            try:
                # Adresse IP
                new_host = host_var.get().strip()
                if not new_host:
                    messagebox.showerror("Error", "The IP address cannot be empty")
                    return
            
                # Port
                try:
                    new_port = int(port_var.get())
                    if new_port < 1 or new_port > 65535:
                        messagebox.showerror("Error", "The port must be between 1 and 65535")
                        return
                except ValueError:
                    messagebox.showerror("Error", "The port must be a number")
                    return
            
                # Fréquence
                if auto_freq_var.get():
                    # Mode Auto
                    new_freq = 0
                else:
                    # Mode fréquence fixe
                    freq_str = freq_var.get().strip()
                    if not freq_str:
                        messagebox.showerror("Error", "Please enter a frequency or check 'Auto'")
                        return
                
                    try:
                        new_freq = int(freq_str)
                        if new_freq <= 0:
                            messagebox.showerror("Error", "The frequency must be positive")
                            return
                        if new_freq < 1000000 or new_freq > 30000000:
                            if not messagebox.askyesno(
                                "Unusual frequency",
                                f"The frequency {new_freq} Hz appears to be outside the HF amateur radio bands (1-30 MHz). Should I continue anyway?"
                            ):
                                return
                    except ValueError:
                        messagebox.showerror("Error", "The frequency must be an integer")
                        return
            
                # Applique les changements
                connection_changed = (new_host != self.js8_host or new_port != self.js8_port)
                freq_changed = (new_freq != self.js8_frequency)
                autostart_changed = (autostart_var.get() != self.autostart_enabled)
            
                old_host = self.js8_host
                old_port = self.js8_port
                old_freq = self.js8_frequency
            
                self.js8_host = new_host
                self.js8_port = new_port
                self.js8_frequency = new_freq
                self.autostart_enabled = autostart_var.get()
            
                # Met à jour l'affichage
                self.update_connection_status()
            
                # Sauvegarde
                self.save_current_config()
            
                # Messages de confirmation
                changes = []
                if connection_changed:
                    changes.append(f"connection: {new_host}:{new_port}")
                if freq_changed:
                    if new_freq == 0:
                        changes.append("Frequency: Auto")
                    else:
                        changes.append(f"Frequency: {new_freq} Hz ({new_freq/1000000:.3f} MHz)")
                if autostart_changed:
                    changes.append(f"Autostart: {'Activated' if self.autostart_enabled else 'Disabled'}")
            
                if changes:
                    self.log_message("Settings updated:" + " | ".join(changes))
            
                # Reconnecte si les paramètres de connexion ont changé
                if connection_changed:
                    self.log_message(f"Reconnecting from {old_host}:{old_port} to {new_host}:{new_port}...")
                    self.reconnect_js8call()
            
                messagebox.showinfo(
                    "Settings applied",
                    "The new settings have been saved:\n\n" + "\n".join(changes) if changes else "No change"
                )
            
                settings_window.destroy()
            
            except Exception as e:
                messagebox.showerror("Error", f"Error applying settings:\n{e}")
                self.log_message(f"Error settings: {e}", "ERROR")
    
        def test_connection_from_settings():
            """Teste la connexion avec les paramètres actuels"""
            try:
                test_host = host_var.get().strip()
                test_port = int(port_var.get())
            
                result = f"Connection test on {test_host}:{test_port}...\n\n"
            
                try:
                    test_client = JS8CallClient(host=test_host, port=test_port)
                    if test_client.connect():
                        result += f"✓ Successful connection to {test_host}:{test_port}!\n\n"
                        result += "JS8Call responds correctly."
                        test_client.disconnect()
                    else:
                        result += f"✗ Unable to connect to {test_host}:{test_port}\n\n"
                        result += "Check that:\n"
                        result += "• JS8Call is started\n"
                        result += "• TCP Server API is enabled in the settings\n"
                        result += "• The port corresponds"
                except Exception as e:
                    result += f"✗ Error: {e}\n\n"
                    result += f"The address {test_host}:{test_port} is not accessible."
            
                messagebox.showinfo("Connection test", result)
            except ValueError:
                messagebox.showerror("Error", "Invalid port")
    
        # Boutons avec une disposition claire
        ttk.Button(
            button_frame,
            text="🔍 Test the connection",
            command=test_connection_from_settings,
            width=20
        ).pack(side=tk.LEFT, padx=5)
    
        ttk.Button(
            button_frame,
            text="❌ Abort",
            command=settings_window.destroy,
            width=15
        ).pack(side=tk.RIGHT, padx=5)
    
        ttk.Button(
            button_frame,
            text="✓ Apply",
            command=apply_settings,
            width=15
        ).pack(side=tk.RIGHT, padx=5)






    def setup_ui(self):
        """Configure l'interface utilisateur (thème sombre)"""

        # --- Thème sombre global ---
        self.root.configure(bg="#333333")  

        style = ttk.Style()
        style.theme_use("clam")  # thème ttk customisable

        # Style générique ttk
        style.configure(
                ".",
                background="#333333",
                foreground="#FFFFFF",
                fieldbackground="#333333",
        )

        # Frames
        style.configure("TFrame", background="#333333")
        style.configure("TLabelframe", background="#333333", foreground="#FFFFFF")
        style.configure("TLabelframe.Label", background="#333333", foreground="#FFFFFF")

        # Labels
        style.configure("TLabel", background="#333333", foreground="#FFFFFF")

        # Boutons
        style.configure(
                "TButton",
                background="#202020",
                foreground="#FFFFFF",
                relief="flat"
        )
        style.map(
                "TButton",
                background=[("active", "#303030"), ("disabled", "#404040")],
                foreground=[("disabled", "#888888")]
        )

        # Combobox / Entry
        style.configure(
                "TEntry",
                fieldbackground="#333333",
                foreground="#FFFFFF",
                insertcolor="#FFFFFF",
        )

        style.configure("TCombobox",
            fieldbackground="#333333",
            background="#333333",
            foreground="#FFFFFF",
            arrowcolor="#FFFFFF",
            selectbackground="#004000",
            selectforeground="#FFFFFF"
        )

        style.map("TCombobox",
            fieldbackground=[("readonly", "#333333"), ("disabled", "#303030")],
            background=[("readonly", "#333333"), ("active", "#202020"), ("focus", "#202020")],
            foreground=[("readonly", "#FFFFFF"), ("disabled", "#888888")],
            selectbackground=[("readonly", "#004000"), ("active", "#006600")],
            selectforeground=[("readonly", "#FFFFFF")]
        )

        # Liste déroulante du Combobox (popup Listbox)
        self.root.option_add("*TCombobox*Listbox.background", "#333333")
        self.root.option_add("*TCombobox*Listbox.foreground", "#FFFFFF")
        self.root.option_add("*TCombobox*Listbox.selectBackground", "#004000")
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
        self.root.option_add("*TCombobox*Listbox.selectBackground", "#004000")

        # Radio / Check
        style.configure(
                "TRadiobutton",
                background="#333333",
                foreground="#FFFFFF",
        )
        style.configure(
                "TCheckbutton",
                background="#333333",
                foreground="#FFFFFF",
        )

        # Barre de progression (vert)
        style.configure(
                "Horizontal.TProgressbar",
                troughcolor="#202020",
                background="#00AA00",
                bordercolor="#333333",
                lightcolor="#00CC00",
                darkcolor="#008800",
        )

        # Text / ScrolledText (non-ttk)
        self.root.option_add("*Text.background", "#333333")
        self.root.option_add("*Text.foreground", "#FFFFFF")
        self.root.option_add("*Text.insertBackground", "#FFFFFF")
        self.root.option_add("*Text.selectBackground", "#004000")

        self.root.option_add("*ScrolledText*background", "#333333")
        self.root.option_add("*ScrolledText*foreground", "#FFFFFF")
        self.root.option_add("*ScrolledText*insertBackground", "#FFFFFF")
        self.root.option_add("*ScrolledText*selectBackground", "#004000")

        # --- Menu bar ---
        #menubar = tk.Menu(self.root, bg="#333333", fg="#FFFFFF", activebackground="#303030", activeforeground="#FFFFFF")
        #self.root.config(menu=menubar)

        #file_menu = tk.Menu(menubar, tearoff=0, bg="#333333", fg="#FFFFFF",
                                                #activebackground="#303030", activeforeground="#FFFFFF")
        #menubar.add_cascade(label="Fichier", menu=file_menu)
        #file_menu.add_command(label="Nouveau", command=self.new_file, accelerator="Ctrl+N")
        #file_menu.add_command(label="Ouvrir...", command=self.open_file, accelerator="Ctrl+O")
        #file_menu.add_command(label="Enregistrer", command=self.save_file, accelerator="Ctrl+S")
        #file_menu.add_command(label="Enregistrer sous...", command=self.save_file_as, accelerator="Ctrl+Shift+S")
        #file_menu.add_separator()
        #file_menu.add_command(label="Quitter", command=self.quit_app, accelerator="Ctrl+Q")

        #tools_menu = tk.Menu(menubar, tearoff=0, bg="#333333", fg="#FFFFFF",
                                                 #activebackground="#303030", activeforeground="#FFFFFF")
        #menubar.add_cascade(label="Outils", menu=tools_menu)
        #tools_menu.add_command(label="Paramètres JS8Call...", command=self.open_settings_window)
        #tools_menu.add_separator()
        #tools_menu.add_command(label="Reconnecter JS8Call", command=self.reconnect_js8call)
        #tools_menu.add_command(label="Tester connexion", command=self.test_connection)

        # Raccourcis clavier
        #self.root.bind('<Control-n>', lambda e: self.new_file())
        #self.root.bind('<Control-o>', lambda e: self.open_file())
        #self.root.bind('<Control-s>', lambda e: self.save_file())
        #self.root.bind('<Control-Shift-S>', lambda e: self.save_file_as())
        #self.root.bind('<Control-q>', lambda e: self.quit_app())

        # --- Frame principal ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # --- Barre d'outils fichiers ---
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(
                toolbar_frame,
                text="📂 Open",
                command=self.open_file,
                width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
                toolbar_frame,
                text="💾 Save",
                command=self.save_file,
                width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
                toolbar_frame,
                text="💾 Save as...",
                command=self.save_file_as,
                width=18
        ).pack(side=tk.LEFT, padx=2)

        # Bouton paramètres
        ttk.Button(
                toolbar_frame,
                text="⚙️ Settings",
                command=self.open_settings_window,
                width=15
        ).pack(side=tk.RIGHT, padx=2)

        # Bouton reconnexion JS8Call
        self.reconnect_button = ttk.Button(
                toolbar_frame,
                text="🔄 Reconnect",
                command=self.reconnect_js8call,
                width=15
        )
        self.reconnect_button.pack(side=tk.RIGHT, padx=2)

        # Nom de fichier en vert doux
        self.file_label = ttk.Label(toolbar_frame, text="Untitled", foreground="#669900")
        self.file_label.pack(side=tk.LEFT, padx=10)

        # --- Zone de texte avec limite de caractères ---
        text_frame = ttk.LabelFrame(main_frame, text="Bulletin Message", padding="5")
        text_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Contrôles de longueur
        length_control_frame = ttk.Frame(text_frame)
        length_control_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(length_control_frame, text="Maximum length:").pack(side=tk.LEFT, padx=(0, 5))

        self.length_var = tk.StringVar(value="Long (210 char)")
        length_combo = ttk.Combobox(
                length_control_frame,
                textvariable=self.length_var,
                values=list(self.max_chars_options.keys()),
                state="readonly",
                width=15
        )
        length_combo.pack(side=tk.LEFT, padx=5)
        length_combo.bind('<<ComboboxSelected>>', self.on_length_changed)

        # Champ personnalisé
        self.custom_length_frame = ttk.Frame(length_control_frame)

        ttk.Label(self.custom_length_frame, text="Value:").pack(side=tk.LEFT, padx=(5, 2))
        self.custom_length_var = tk.StringVar(value="210")
        self.custom_length_entry = ttk.Entry(
                self.custom_length_frame,
                textvariable=self.custom_length_var,
                width=5
        )
        self.custom_length_entry.pack(side=tk.LEFT)
        self.custom_length_entry.bind('<Return>', lambda e: self.apply_custom_length())

        ttk.Button(
                self.custom_length_frame,
                text="OK",
                command=self.apply_custom_length,
                width=4
        ).pack(side=tk.LEFT, padx=2)

        # Info durée estimée en vert
        self.duration_label = ttk.Label(
                length_control_frame,
                text="",
                foreground="#669900"
        )
        self.duration_label.pack(side=tk.RIGHT, padx=5)

        # Durée initiale
        self.update_duration_estimate()

        # Zone de texte
        self.text_area = scrolledtext.ScrolledText(
                text_frame,
                width=70,
                height=5,
                wrap=tk.WORD,
                foreground="#999999",
                font=("Source Code Pro", 12, "bold")
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)

        # Binding pour validation stricte des caractères
        self.text_area.bind('<<Modified>>', self.on_text_modified)

        # Compteur de caractères + progress
        counter_frame = ttk.Frame(text_frame)
        counter_frame.pack(fill=tk.X, pady=(5, 0))

        self.char_label = ttk.Label(counter_frame, text=f"0 / {self.max_chars} characters")
        self.char_label.pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(
                counter_frame,
                length=200,
                mode='determinate',
                maximum=self.max_chars
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))

        # --- Sélection intervalle d'émission ---
        interval_frame = ttk.LabelFrame(main_frame, text="Transmission configuration", padding="5")
        interval_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.interval_var = tk.StringVar(value="15")

        intervals = [
                ("10 minutes", "10"),
                ("15 minutes", "15"),
                ("30 minutes", "30"),
                ("1 hour", "60"),
                ("2 hours", "120"),
                ("3 hours", "180"),
                ("4 hours", "240"),
                ("6 hours", "360"),
                ("12 hours", "720"),
                ("24 hours", "1440"),
                ("Even hours", "even"),
                ("Odd hours", "odd")
        ]

        for i, (text, value) in enumerate(intervals):
                ttk.Radiobutton(
                        interval_frame,
                        text=text,
                        variable=self.interval_var,
                        value=value,
                        command=self.update_schedule
                ).grid(row=i//6, column=i%6, sticky=tk.W, padx=10, pady=2)

        # --- Boutons de contrôle ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.start_button = ttk.Button(
                button_frame,
                text="▶ Start broadcasts",
                command=self.start_emissions,
                width=20
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(
                button_frame,
                text="⏹ Stop",
                command=self.stop_emissions,
                state=tk.DISABLED,
                width=15
        )
        self.stop_button.grid(row=0, column=1, padx=5)

        self.send_now_button = ttk.Button(
                button_frame,
                text="📡 Send now",
                command=self.send_now,
                width=20
        )
        self.send_now_button.grid(row=0, column=2, padx=5)

        # --- Zone de statut ---
        status_frame = ttk.LabelFrame(main_frame, text="Statut", padding="5")
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Statut JS8Call
        self.js8_status_label = ttk.Label(
                status_frame,
                text="JS8Call: Pending...",
                foreground="#669900"
        )
        self.js8_status_label.grid(row=0, column=0, sticky=tk.W)

        # Info fréquence
        self.freq_status_label = ttk.Label(
                status_frame,
                text="Frequency: ...",
                foreground="#669900"
        )
        self.freq_status_label.grid(row=1, column=0, sticky=tk.W)

        self.status_label = ttk.Label(status_frame, text="Inactive", foreground="#FFFFFF")
        self.status_label.grid(row=2, column=0, sticky=tk.W)

        self.next_emission_label = ttk.Label(status_frame, text="Next broadcast: ---", foreground="#669900")
        self.next_emission_label.grid(row=3, column=0, sticky=tk.W)

        self.last_emission_label = ttk.Label(status_frame, text="Last broadcast: ---", foreground="#669900")
        self.last_emission_label.grid(row=4, column=0, sticky=tk.W)

        # --- Log d'activité ---
        log_frame = ttk.LabelFrame(main_frame, text="Activity log", padding="5")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.log_area = scrolledtext.ScrolledText(
                log_frame,
                width=70,
                height=5,
                wrap=tk.WORD,
                font=("Courier", 9),
                state=tk.DISABLED
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # --- Grids ---
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=2)
        main_frame.rowconfigure(5, weight=1)




    
    def update_duration_estimate(self):
        """Met à jour l'estimation de durée de transmission"""
        segments = (self.max_chars // 13) + 1
        duration_seconds = segments * 15
        
        if duration_seconds < 60:
            duration_text = f"~{duration_seconds}s"
        else:
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            if seconds > 0:
                duration_text = f"~{minutes}min {seconds}s"
            else:
                duration_text = f"~{minutes}min"
        
        self.duration_label.config(text=f"Maximum duration TX: {duration_text}")
    
    def on_length_changed(self, event=None):
        """Gère le changement de limite de longueur"""
        selected = self.length_var.get()
        
        if selected == "Custom":
            self.custom_length_frame.pack(side=tk.LEFT, padx=5)
            self.custom_length_entry.focus()
        else:
            self.custom_length_frame.pack_forget()
            new_max = self.max_chars_options[selected]
            self.apply_new_max_chars(new_max)
    
    def apply_custom_length(self):
        """Applique une longueur personnalisée"""
        try:
            custom_value = int(self.custom_length_var.get())
            
            if custom_value < 10:
                messagebox.showerror("Error", "The minimum length is 10 characters.")
                return
            
            if custom_value > 500:
                if not messagebox.askyesno(
                    "Warning",
                    f"{custom_value} characters = ~{custom_value // 13} segments = ~{(custom_value // 13) * 15 // 60} minutes of transmission.\n\nContinue?"
                ):
                    return
            
            self.apply_new_max_chars(custom_value)
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number.")
    
    def apply_new_max_chars(self, new_max):
        """Applique une nouvelle limite de caractères"""
        old_max = self.max_chars
        self.max_chars = new_max
        
        self.progress_bar['maximum'] = new_max
        self.update_duration_estimate()
        
        current_text = self.text_area.get("1.0", tk.END).strip()
        if len(current_text) > new_max:
            if messagebox.askyesno(
                "Message too long",
                f"The current message ({len(current_text)} car) exceeds the new limit ({new_max} car).\n\nTruncate at {new_max} characters?"
            ):
                truncated = current_text[:new_max]
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", truncated)
        
        text_length = len(self.text_area.get("1.0", tk.END).strip())
        self.update_char_display(text_length)
        
        self.log_message(f"Character limit changed: {old_max} → {new_max}")
    
    def on_text_modified(self, event=None):
        """Validation stricte du nombre de caractères avec feedback visuel"""
        if self.text_area.edit_modified():
            self.text_area.edit_modified(False)
            
            text = self.text_area.get("1.0", tk.END).strip()
            char_count = len(text)
            
            if char_count > self.max_chars:
                cursor_pos = self.text_area.index(tk.INSERT)
                truncated_text = text[:self.max_chars]
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", truncated_text)
                
                try:
                    row, col = cursor_pos.split('.')
                    new_pos = f"{row}.{min(int(col), self.max_chars)}"
                    self.text_area.mark_set(tk.INSERT, new_pos)
                except:
                    self.text_area.mark_set(tk.INSERT, tk.END)
                
                self.root.bell()
                char_count = self.max_chars
            
            self.update_char_display(char_count)
    
    def update_char_display(self, char_count):
        """Met à jour l'affichage du compteur et de la barre de progression"""
        self.progress_bar['value'] = char_count
        
        warning_threshold = max(self.max_chars - 30, int(self.max_chars * 0.85))
        critical_threshold = max(self.max_chars - 15, int(self.max_chars * 0.93))
        
        if char_count >= self.max_chars:
            color = "red"
            msg = "LIMIT REACHED"
        elif char_count >= critical_threshold:
            color = "orange"
            remaining = self.max_chars - char_count
            msg = f"Plus que {remaining} characters{'s' if remaining > 1 else ''}"
        elif char_count >= warning_threshold:
            color = "dark orange"
            msg = ""
        else:
            color = "black" if char_count > 0 else "gray"
            msg = ""
        
        label_text = f"{char_count} / {self.max_chars} characters"
        if msg:
            label_text += f" - {msg}"
        
        self.char_label.config(text=label_text, foreground=color)
    
    def test_connection(self):
        """Teste et affiche le statut de la connexion"""
        result = "=== JS8Call connection test ===\n\n"
        result += f"Test of {self.js8_host}:{self.js8_port}...\n"
        
        try:
            test_client = JS8CallClient(host=self.js8_host, port=self.js8_port)
            if test_client.connect():
                result += f"✓ Connection successful!\n"
                test_client.disconnect()
            else:
                result += f"✗ Connection failed\n"
        except Exception as e:
            result += f"✗ ERROR: {e}\n"
        
        result += f"\nCurrent status: {'✓ Connected' if self.js8_connected else '✗ Not connected'}"
        result += f"\nConfigured address: {self.js8_host}:{self.js8_port}"
        freq_display = f"{self.js8_frequency} Hz" if self.js8_frequency > 0 else "Auto"
        result += f"\nFrequency: {freq_display}"
        result += f"\nAutostart: {'Activated' if self.autostart_enabled else 'Disabled'}"
        
        messagebox.showinfo("Connection test", result)
        self.log_message("Connection test performed")
    
    def log_message(self, message, level="INFO"):
        """Ajoute un message au journal"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, log_entry)
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        
        print(log_entry.strip())
    
    def new_file(self):
        """Crée un nouveau fichier"""
        if self.emission_active:
            messagebox.showwarning(
                "Active broadcasts",
                "Stop the broadcasts first before creating a new file."
            )
            return
        
        if messagebox.askyesno("New file", "Create a new message? Unsaved changes will be lost."):
            self.text_area.delete("1.0", tk.END)
            self.interval_var.set("15")
            self.current_file = None
            self.file_label.config(text="Untitled")
            self.update_char_display(0)
            self.log_message("New file created")
    
    def open_file(self):
        """Ouvre un fichier de message"""
        if self.emission_active:
            messagebox.showwarning(
                "Active broadcasts",
                "Stop the broadcasts first before opening a file."
            )
            return
        
        filename = filedialog.askopenfilename(
            title="Ouvrir un message",
            filetypes=[
                ("JSON files", "*.json"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ],
            defaultextension=".json"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    if filename.endswith('.json'):
                        data = json.load(f)
                        message_text = data.get('message', '')
                        
                        saved_max_chars = data.get('max_chars')
                        if saved_max_chars and saved_max_chars != self.max_chars:
                            if messagebox.askyesno(
                                "Different limit",
                                f"This file was created with a limit of {saved_max_chars} characters.\n"
                                f"The current limit is {self.max_chars} characters.\n\n"
                                f"Adopt the file limit ({saved_max_chars})?"
                            ):
                                found = False
                                for option_name, option_value in self.max_chars_options.items():
                                    if option_value == saved_max_chars:
                                        self.length_var.set(option_name)
                                        self.apply_new_max_chars(saved_max_chars)
                                        found = True
                                        break
                                
                                if not found:
                                    self.length_var.set("Custom")
                                    self.custom_length_var.set(str(saved_max_chars))
                                    self.apply_custom_length()
                        
                        if len(message_text) > self.max_chars:
                            message_text = message_text[:self.max_chars]
                            messagebox.showwarning(
                                "Message truncated",
                                f"The message was truncated to {self.max_chars} characters."
                            )
                        
                        self.text_area.delete("1.0", tk.END)
                        self.text_area.insert("1.0", message_text)
                        self.interval_var.set(data.get('interval', '15'))
                    else:
                        content = f.read()
                        
                        if len(content) > self.max_chars:
                            content = content[:self.max_chars]
                            messagebox.showwarning(
                                "Message truncated",
                                f"The message was truncated to {self.max_chars} characters."
                            )
                        
                        self.text_area.delete("1.0", tk.END)
                        self.text_area.insert("1.0", content)
                
                self.current_file = filename
                self.file_label.config(text=os.path.basename(filename))
                self.log_message(f"Fichier ouvert: {os.path.basename(filename)}")
                
                text = self.text_area.get("1.0", tk.END).strip()
                self.update_char_display(len(text))
                
            except Exception as e:
                messagebox.showerror("Error", f"Unable to open the file:\n{e}")
                self.log_message(f"File opening error: {e}", "ERROR")
    
    def save_file(self):
        """Enregistre le fichier actuel"""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """Enregistre sous un nouveau nom"""
        filename = filedialog.asksaveasfilename(
            title="Save the message",
            filetypes=[
                ("JSON Files", "*.json"),
                ("Text Files", "*.txt"),
                ("All files", "*.*")
            ],
            defaultextension=".json"
        )
        
        if filename:
            self._save_to_file(filename)
    
    def _save_to_file(self, filename):
        """Enregistre dans un fichier"""
        try:
            text = self.text_area.get("1.0", tk.END).strip()
            
            if filename.endswith('.json'):
                data = {
                    'message': text,
                    'interval': self.interval_var.get(),
                    'max_chars': self.max_chars,
                    'char_count': len(text),
                    'js8_host': self.js8_host,
                    'js8_port': self.js8_port,
                    'js8_frequency': self.js8_frequency,
                    'saved_at': datetime.now().isoformat()
                }
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(text)
            
            self.current_file = filename
            self.file_label.config(text=os.path.basename(filename))
            self.log_message(f"File saved: {os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Unable to save the file:\n{e}")
            self.log_message(f"Backup error: {e}", "ERROR")
    
    def load_last_config(self):
        """Charge la dernière configuration au démarrage"""
        config_file = "js8_bulletin_last.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    message = data.get('message', '')
                    
                    # Charge les paramètres JS8Call
                    saved_host = data.get('js8_host')
                    if saved_host:
                        self.js8_host = saved_host
                    
                    saved_port = data.get('js8_port')
                    if saved_port:
                        self.js8_port = saved_port
                    
                    saved_freq = data.get('js8_frequency')
                    if saved_freq is not None:
                        self.js8_frequency = saved_freq
                    
                    # NOUVEAU: Charge le paramètre autostart
                    saved_autostart = data.get('autostart_enabled')
                    if saved_autostart is not None:
                        self.autostart_enabled = saved_autostart
                    
                    saved_max_chars = data.get('max_chars', 210)
                    if saved_max_chars != self.max_chars:
                        for option_name, option_value in self.max_chars_options.items():
                            if option_value == saved_max_chars:
                                self.length_var.set(option_name)
                                self.max_chars = saved_max_chars
                                break
                    
                    if len(message) > self.max_chars:
                        message = message[:self.max_chars]
                    
                    if hasattr(self, 'text_area'):
                        self.text_area.insert("1.0", message)
                        self.interval_var.set(data.get('interval', '15'))
                        self.update_char_display(len(message))
                        self.update_duration_estimate()
                    
                autostart_status = "activated" if self.autostart_enabled else "disabled"
                self.log_message(f"Loaded configuration: {self.js8_host}:{self.js8_port} (autostart: {autostart_status})")
            except Exception as e:
                print(f"Error loading configuration: {e}")
    
    def save_current_config(self):
        """Sauvegarde la configuration actuelle"""
        config_file = "js8_bulletin_last.json"
        try:
            text = self.text_area.get("1.0", tk.END).strip()
            data = {
                'message': text,
                'interval': self.interval_var.get(),
                'max_chars': self.max_chars,
                'js8_host': self.js8_host,
                'js8_port': self.js8_port,
                'js8_frequency': self.js8_frequency,
                'autostart_enabled': self.autostart_enabled,
                'saved_at': datetime.now().isoformat()
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Configuration backup error: {e}")
    
    def calculate_next_emission(self):
        """Calcule la prochaine heure d'émission"""
        now = datetime.now()
        interval = self.interval_var.get()
        
        if interval == "odd":
            next_hour = now.replace(minute=0, second=0, microsecond=0)
            while next_hour.hour % 2 != 1 or next_hour <= now:
                next_hour += timedelta(hours=1)
            return next_hour
        elif interval == "even":
            next_hour = now.replace(minute=0, second=0, microsecond=0)
            while next_hour.hour % 2 != 0 or next_hour <= now:
                next_hour += timedelta(hours=1)
            return next_hour
        else:
            minutes = int(interval)
            next_time = now.replace(second=0, microsecond=0)
            
            current_minute = next_time.minute
            next_minute = ((current_minute // minutes) + 1) * minutes
            
            if next_minute >= 60:
                next_time += timedelta(hours=next_minute // 60)
                next_minute = next_minute % 60
            
            next_time = next_time.replace(minute=next_minute)
            return next_time
    
    def update_schedule(self):
        """Met à jour l'affichage de la prochaine émission"""
        if self.emission_active:
            self.next_emission = self.calculate_next_emission()
            if self.next_emission:
                time_diff = self.next_emission - datetime.now()
                minutes = int(time_diff.total_seconds() // 60)
                self.next_emission_label.config(
                    text=f"Next broadcast: {self.next_emission.strftime('%H:%M:%S')} (in {minutes} min)"
                )
            else:
                self.next_emission_label.config(text="Next broadcast: Manual only")
    
    def start_emissions(self):
        """Démarre le cycle d'émissions automatiques"""
        text = self.text_area.get("1.0", tk.END).strip()
        if not text:
            messagebox.showerror("Error", "The message is empty!")
            return
        
        if len(text) > self.max_chars:
            messagebox.showerror("Error", f"Message too long! ({len(text)}/{self.max_chars} caractères)")
            return
        
        if not self.js8_connected:
            if not messagebox.askyesno(
                "JS8Call not connected",
                f"JS8Call n'est pas connecté sur {self.js8_host}:{self.js8_port}.\n\nLes messages seront simulés.\n\nVoulez-vous essayer de reconnecter d'abord?"
            ):
                pass
            else:
                self.reconnect_js8call()
                if not self.js8_connected:
                    return
        
        self.emission_active = True
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.text_area.config(state=tk.DISABLED)
        self.status_label.config(text="✓ Active broadcast", foreground="green")
        
        self.log_message("Automatic broadcast started")
        self.update_schedule()
        
        self.check_thread = threading.Thread(target=self.emission_loop, daemon=True)
        self.check_thread.start()
    
    def stop_emissions(self):
        """Arrête les émissions automatiques"""
        self.emission_active = False
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.text_area.config(state=tk.NORMAL)
        self.status_label.config(text="Inactive", foreground="black")
        self.next_emission_label.config(text="Next brodcast: ---")
        self.log_message("Automatic broadcast stopped")
    
    def emission_loop(self):
        """Boucle de vérification des émissions"""
        while self.running:
            if self.emission_active and self.next_emission:
                now = datetime.now()
                if now >= self.next_emission:
                    self.emit_message()
                    self.next_emission = self.calculate_next_emission()
                    self.root.after(0, self.update_schedule)
            
            time.sleep(1)
    
    def emit_message(self):
        """Émet le message via JS8Call"""
        text = self.text_area.get("1.0", tk.END).strip()
        
        try:
            if self.js8_connected and self.js8_client:
                # Change la fréquence si configurée
                if self.js8_frequency > 0:
                    self.js8_client.set_frequency(self.js8_frequency)
                
                success = self.js8_client.send_message(text, self.js8_frequency)
                if success:
                    preview = text[:50] + "..." if len(text) > 50 else text
                    freq_info = f" @ {self.js8_frequency} Hz" if self.js8_frequency > 0 else ""
                    self.root.after(0, lambda: self.log_message(f"Message sent ({len(text)} car{freq_info}): '{preview}'"))
                else:
                    self.root.after(0, lambda: self.log_message("Transmission failed - check JS8Call", "ERROR"))
                    self.root.after(0, self.reconnect_js8call)
            else:
                preview = text[:50] + "..." if len(text) > 50 else text
                freq_info = f" @ {self.js8_frequency} Hz" if self.js8_frequency > 0 else ""
                self.root.after(0, lambda: self.log_message(f"[SIMULATION] Message ({len(text)} car{freq_info}): '{preview}'", "WARNING"))
            
            self.root.after(0, lambda: self.last_emission_label.config(
                text=f"Dernière émission: {datetime.now().strftime('%H:%M:%S')}"
            ))
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Error transmission: {e}", "ERROR"))
    
    def send_now(self):
        """Envoie immédiatement le message"""
        text = self.text_area.get("1.0", tk.END).strip()
        if not text:
            messagebox.showerror("Error", "The message is empty!")
            return
        
        if len(text) > self.max_chars:
            messagebox.showerror("Error", f"Message too long! ({len(text)}/{self.max_chars} characters)")
            return
        
        if not self.js8_connected:
            if messagebox.askyesno(
                "JS8Call not connected",
                f"JS8Call is not connected sur {self.js8_host}:{self.js8_port}.\n\nTry to reconnect ?"
            ):
                self.reconnect_js8call()
                if not self.js8_connected:
                    return
            else:
                return
        
        self.emit_message()
    
    def quit_app(self):
        """Quitte l'application proprement"""
        if self.emission_active:
            if not messagebox.askyesno(
                "Active emissions",
                "Programs are currently airing. Leave anyway ?"
            ):
                return
            self.stop_emissions()
        
        self.save_current_config()
        
        if self.js8_client:
            try:
                self.js8_client.disconnect()
            except:
                pass
        
        self.root.destroy()

def main():
    root = tk.Tk()
    app = JS8BulletinBoard(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()

if __name__ == "__main__":
    main()
