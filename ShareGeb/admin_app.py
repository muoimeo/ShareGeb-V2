import tkinter as tk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database setup (same as web app)
engine = create_engine('mysql://user:password@localhost/rideshare')
Session = sessionmaker(bind=engine)
session = Session()

# Tkinter window
root = tk.Tk()
root.title("Admin Dashboard")

# Function to show users (example)
def show_users():
    # Replace with actual User model query when you set up database
    users = ["User1", "User2"]  # Placeholder
    user_list = "\n".join(users)
    label.config(text=user_list)

# Button and label
button = tk.Button(root, text="Show Users", command=show_users)
button.pack()
label = tk.Label(root, text="Click to see users")
label.pack()

root.mainloop()