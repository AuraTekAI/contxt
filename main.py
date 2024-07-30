## main.py ##

import logging
import schedule
import time
import tkinter as tk
import threading
from tkinter import messagebox
from datetime import datetime, timedelta
from accept_invite import *
from pull_email import *
from db_ops import *
from send_sms import *
from variables import *
from push_email import *
from login import *

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_email_callback():
    """
    Sets up the email callback for db_ops.
    This function initializes the email callback by calling set_email_callback with process_emails as the argument.
    It's expected to be called at the start of the program to ensure email processing is properly configured.
    """
    set_email_callback(process_emails)

def setup_interactive_window():
    """
    Sets up the interactive window for test mode actions.
    This function creates a tkinter window with various buttons for different actions like email retrieval, SMS sending, and invitation processing.
    It's used in test mode to allow manual triggering of different functionalities for debugging and testing purposes.
    """
    window = tk.Tk()
    window.title("Debug Mode")

    # Get the screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Calculate the window dimensions and position
    window_width = 250
    window_height = 230
    window_x = (screen_width // 2) - (window_width // 2)
    window_y = (screen_height // 2) - (window_height // 2)

    # Set the window geometry and position
    window.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")

    # Add padding (border) around the window content
    window.configure(padx=10, pady=10)

    def handle_email_retrieval():
        """
        Handles the email retrieval process.
        This function is called when the "Retrieve Emails" button is clicked in the interactive window.
        It initializes the environment and executes the process_unread_emails function to fetch and process new emails.
        """
        initialize_and_execute(process_unread_emails)

    def send_email_responses_threaded():
        """
        Sends email responses in a separate thread.
        This function creates a new thread to run the process_emails function, which handles sending email responses.
        It's designed to prevent the GUI from freezing during the email sending process and provides feedback via message boxes.
        """
        def thread_function():
            try:
                process_emails()  # This is the function from push_email_gui.py
                messagebox.showinfo("Success", "Email process completed.")
            except Exception as e:
                logging.error(f"An error occurred: {str(e)}")
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        threading.Thread(target=thread_function).start()

    def parse_contact_emails_threaded():
        """
        Parses contact emails in a separate thread.
        This function creates a new thread to run the parse_contact_emails function, which processes emails to extract contact information.
        It's designed to prevent the GUI from freezing during the parsing process.
        """
        threading.Thread(target=lambda: initialize_and_execute(parse_contact_emails)).start()

    def accept_invite():
        """
        Handles the invitation acceptance process.
        This function fetches an invite code and user name from an email, then processes the invitation using this information.
        It runs in a separate thread and provides feedback via message boxes about the success or failure of the invitation acceptance.
        """
        def thread_function():
            # Fetch invite code from email
            invite_code, email_id, full_name = fetch_invite_code_and_name()
        
            if invite_code and full_name:
                print(f"Invite Code: {invite_code}")
                print(f"User Name: {full_name}")
                # Process invitation using the invite code and email ID
                result = process_invitation()
                if result:
                    messagebox.showinfo("Invitation Accepted", f"Successfully accepted invitation for {full_name}")
                else:
                    messagebox.showerror("Invitation Failed", f"Failed to accept invitation for {full_name}")
            else:
                messagebox.showinfo("No Invite", "No invite code found.")
    
        threading.Thread(target=thread_function).start()

    def run_push_email():
        """
        Runs the data logger push email process in a separate thread.
        This function executes the run_push_email function in a new thread and displays the result in a message box.
        It's used for logging and pushing email data, likely for debugging or monitoring purposes.
        """
        def thread_function():
            result = run_push_email()
            messagebox.showinfo("Data Logger Result", result)
        threading.Thread(target=thread_function).start()

    # Define button actions
    tk.Button(window, text="Retrieve Emails", command=handle_email_retrieval).pack(fill=tk.X)
    tk.Button(window, text="Send SMS", command=send_sms_threaded).pack(fill=tk.X)
    tk.Button(window, text="Reply to Emails", command=send_email_responses_threaded).pack(fill=tk.X)
    tk.Button(window, text="Parse Contact Emails", command=parse_contact_emails_threaded).pack(fill=tk.X)
    tk.Button(window, text="Accept Invite", command=accept_invite).pack(fill=tk.X)
    tk.Button(window, text="Data Logger", command=run_push_email).pack(fill=tk.X)
    tk.Button(window, text="Reply to CorrLinks P2P", command=lambda: messagebox.showinfo("Placeholder", "P2P functionality")).pack(fill=tk.X)
    tk.Button(window, text="Answer ChatGPT Questions", command=lambda: messagebox.showinfo("Placeholder", "ChatGPT functionality")).pack(fill=tk.X)

    window.mainloop()

def initialize_and_execute(task_function):
    """
    Initializes the environment and executes a given task function.
    Parameters:
    - task_function (function): The function to be executed after initialization.

    This function logs into Corrlinks, establishes a database connection, executes the provided task function, and ensures proper cleanup of resources afterwards.
    It's a general-purpose function used to set up the necessary environment for various operations.
    """
    session = login_to_corrlinks()
    if not session:
        logging.error("Failed to initialize the session.")
        return
    db_connection, cursor = get_database_connection()

    try:
        if db_connection and cursor:
            task_function(session, db_connection, cursor)  # Pass the session to the task function
        else:
            logging.error("Failed to establish database connection.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        if session:
            session.close()  # Ensure session is closed only after all task functions are done
        if db_connection and cursor:
            close_database_resources(db_connection, cursor)
        
def main():
    """
    The main entry point of the program.
    This function sets up the email callback and either launches the interactive window (in test mode) or sets up scheduled tasks (in normal mode).
    It controls the overall flow of the program based on the TEST_MODE flag.
    """
    # Set up the email callback
    setup_email_callback()

    if TEST_MODE:
        setup_interactive_window()
    else:
        # Schedule tasks to run periodically outside of TEST_MODE
        schedule.every(10).minutes.do(initialize_and_execute, process_unread_emails)
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Scheduler stopped manually.")

if __name__ == "__main__":
    main()