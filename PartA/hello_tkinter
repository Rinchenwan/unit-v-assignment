import tkinter as tk

root = tk.Tk()
root.title("Hello - Tkinter")
root.geometry("300x150")

label = tk.Label(root, text="Hello, World!", font=("Arial", 14))
label.pack(pady=15)


def on_click():
    label.config(text="Button clicked!")


tk.Button(root, text="Click me", command=on_click).pack()
root.mainloop()
