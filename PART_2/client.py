import socket
import threading
import customtkinter as ctk
from tkinter import messagebox

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 1234
# Messenger-like Blue Color
THEME_COLOR = "#0084FF"

# Setting up the visual theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ModernChatClient(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Client-Server Chat")
        self.geometry("400x600")
        
        # Initialize Socket
        self.client_socket = None
        self.nickname = ""
        self.running = True

        # --- GUI Layout ---
        
        # 1. Chat Area (Scrollable Frame)
        self.chat_area = ctk.CTkScrollableFrame(self, width=380, height=500, corner_radius=15)
        self.chat_area.pack(pady=10, padx=10, fill="both", expand=True)

        # 2. Input Area (Bottom Frame)
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(pady=10, padx=10, fill="x")

        # Entry Box
        self.msg_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type your message...", height=40, corner_radius=20)
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.msg_entry.bind("<Return>", lambda event: self.send_action()) # Allow sending with Enter key

        # Send Button
        self.send_btn = ctk.CTkButton(self.input_frame, text="Send", width=80, height=40, corner_radius=20,
                                      fg_color=THEME_COLOR, hover_color="#006CD0",
                                      command=self.send_action)
        self.send_btn.pack(side="right")

        # --- Protocol Protocol ---
        # We start the connection process after the UI initializes
        self.after(100, self.start_connection)

    def add_message(self, message, is_sender=True):
        """
        Adds a message bubble to the chat area.
        is_sender: True (Right side/Blue), False (Left side/Grey)
        """
        if is_sender:
            bubble_color = THEME_COLOR
            text_color = "white"
            anchor = "e"  # East (Right)
        else:
            bubble_color = "#3A3B3C"  # Dark Grey
            text_color = "white"
            anchor = "w"  # West (Left)

        # Frame to hold the bubble and manage alignment
        msg_frame = ctk.CTkFrame(self.chat_area, fg_color="transparent")
        msg_frame.pack(fill="x", pady=5)

        # The message bubble itself
        label = ctk.CTkLabel(
            msg_frame, 
            text=message, 
            fg_color=bubble_color, 
            text_color=text_color,
            corner_radius=15,
            wraplength=250,
            padx=15, pady=10,
            font=("Arial", 14)
        )
        
        # Pack to Right or Left
        if is_sender:
            label.pack(side="right", padx=(50, 5)) 
        else:
            label.pack(side="left", padx=(5, 50))
            
        # Auto-scroll to the bottom
        self.chat_area._parent_canvas.yview_moveto(1.0)

    def start_connection(self):
        """Handles the initial connection and handshake"""
        # 1. Ask for Nickname via Dialog (Blocking Input but GUI safe)
        dialog = ctk.CTkInputDialog(text="Enter your Nickname:", title="Login")
        self.nickname = dialog.get_input()

        if not self.nickname:
            self.destroy() # Close if no name provided
            return

        # 2. Connect to Server
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((HOST, PORT))
            self.add_message(f"Connected to {HOST}:{PORT}", is_sender=False)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect: {e}")
            self.destroy()
            return

        # 3. Handle Server Handshake (in a separate thread to avoid freezing)
        # We start the receive loop immediately, handling the handshake inside it or just sending data.
        # Based on your previous code, the server sends a prompt first.
        threading.Thread(target=self.receive_loop, daemon=True).start()

    def receive_loop(self):
        """Background thread to listen for messages"""
        # Handshake Logic (Simplified for GUI)
        try:
            # Step A: Receive 'Request for name' from server
            server_prompt = self.client_socket.recv(1024).decode('utf-8')
            
            # Step B: Send the nickname
            self.client_socket.send(str.encode(self.nickname))
            
            # Step C: Receive confirmation
            response = self.client_socket.recv(1024).decode('utf-8')
            
            # Update GUI with server response (using .after to be thread-safe)
            self.after(0, lambda: self.add_message(response, is_sender=False))

            if "already taken" in response:
                self.client_socket.close()
                return

            # --- Main Message Loop ---
            while self.running:
                try:
                    message = self.client_socket.recv(2048).decode('utf-8')
                    if message:
                        # Schedule the GUI update on the main thread
                        self.after(0, lambda msg=message: self.add_message(msg, is_sender=False))
                    else:
                        self.client_socket.close()
                        break
                except Exception as e:
                    print(f"Error receiving: {e}")
                    break
        except Exception as e:
            print(f"Handshake/Connection Error: {e}")
            self.client_socket.close()

    def send_action(self):
        """Sends the message typed in the entry box"""
        text = self.msg_entry.get()
        if text:
            try:
                # 1. Show locally immediately
                self.add_message(f"Me: {text}", is_sender=True)
                
                # 2. Send over socket
                self.client_socket.send(str.encode(text))
                
                # 3. Clear input
                self.msg_entry.delete(0, "end")
                
                if text.lower() == 'exit':
                    self.running = False
                    self.client_socket.close()
                    self.destroy()
            except Exception as e:
                self.add_message(f"Error sending: {e}", is_sender=False)

    def on_closing(self):
        """Clean up when window is closed"""
        self.running = False
        if self.client_socket:
            self.client_socket.close()
        self.destroy()

if __name__ == "__main__":
    app = ModernChatClient()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()