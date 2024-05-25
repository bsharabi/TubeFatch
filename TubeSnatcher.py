import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pytube import YouTube
import os
from googleapiclient.discovery import build
import webbrowser
import threading
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment variable
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
if not YOUTUBE_API_KEY:
    raise ValueError("YouTube API key not found in the .env file.")

def search_videos(query: str, page_token: str = None):
    """
    Searches for videos on YouTube based on the query.

    Args:
        query (str): The search query.
        page_token (str, optional): The token for the next page of results.

    Returns:
        tuple: A tuple containing the list of search results and the next page token.
    """
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        q=query,
        part='snippet',
        type='video',
        maxResults=10,
        pageToken=page_token
    )
    response = request.execute()
    return response['items'], response.get('nextPageToken')

def download_video(url: str, download_path: str = '.', file_format: str = 'mp4', resolution: str = 'highest', progress_callback=None):
    """
    Downloads a video from YouTube.

    Args:
        url (str): The YouTube video URL.
        download_path (str, optional): The path to save the downloaded video. Defaults to '.'.
        file_format (str, optional): The file format ('mp4' or 'mp3'). Defaults to 'mp4'.
        resolution (str, optional): The resolution ('highest', 'lowest', '1080p', '720p', '480p'). Defaults to 'highest'.
        progress_callback (function, optional): The callback function for updating the progress bar.
    """
    try:
        yt = YouTube(url, on_progress_callback=progress_callback)
        if file_format == 'mp4':
            if resolution == 'highest':
                stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            elif resolution == 'lowest':
                stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').asc().first()
            else:
                stream = yt.streams.filter(progressive=True, file_extension='mp4', res=resolution).first()
                
            if stream:
                stream.download(output_path=download_path)
                messagebox.showinfo("Success", "Download complete!")
            else:
                messagebox.showerror("Error", "No suitable stream found.")

        elif file_format == 'mp3':
            stream = yt.streams.filter(only_audio=True).first()
            if stream:
                downloaded_file = stream.download(output_path=download_path)
                base, ext = os.path.splitext(downloaded_file)
                new_file = base + '.mp3'
                os.rename(downloaded_file, new_file)
                messagebox.showinfo("Success", "Download complete!")
            else:
                messagebox.showerror("Error", "No suitable stream found.")

        else:
            messagebox.showerror("Error", "Unsupported file format. Please choose 'mp4' or 'mp3'.")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

class TubeFetchApp(tk.Tk):
    """
    The main application class for the TubeFetch GUI.
    """

    def __init__(self):
        """
        Initializes the TubeFetchApp.
        """
        super().__init__()

        self.title("TubeFetch")
        self.geometry("800x800")

        self.search_label = tk.Label(self, text="Search:")
        self.search_label.pack(pady=10)

        self.search_entry = tk.Entry(self, width=50)
        self.search_entry.pack(pady=10)

        self.search_button = tk.Button(self, text="Search", command=self.search)
        self.search_button.pack(pady=10)

        self.results_frame = tk.Frame(self)
        self.results_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        self.results_scrollbar = tk.Scrollbar(self.results_frame)
        self.results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_listbox = tk.Listbox(self.results_frame, width=100, height=10, yscrollcommand=self.results_scrollbar.set)
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.results_scrollbar.config(command=self.results_listbox.yview)

        self.more_button = tk.Button(self, text="More Results", command=self.more_results)
        self.more_button.pack(pady=5)

        self.preview_button = tk.Button(self, text="Preview", command=self.preview)
        self.preview_button.pack(pady=5)

        self.format_label = tk.Label(self, text="Format:")
        self.format_label.pack(pady=5)

        self.format_choice = ttk.Combobox(self, values=["mp4", "mp3"])
        self.format_choice.current(0)
        self.format_choice.pack(pady=5)

        self.resolution_label = tk.Label(self, text="Resolution:")
        self.resolution_label.pack(pady=5)

        self.resolution_choice = ttk.Combobox(self, values=["highest", "lowest", "1080p", "720p", "480p"])
        self.resolution_choice.current(0)
        self.resolution_choice.pack(pady=5)

        self.path_label = tk.Label(self, text="Download Path:")
        self.path_label.pack(pady=5)

        self.path_entry = tk.Entry(self, width=50)
        self.path_entry.pack(pady=5)

        self.browse_button = tk.Button(self, text="Browse", command=self.browse)
        self.browse_button.pack(pady=5)

        self.download_button = tk.Button(self, text="Download", command=self.download)
        self.download_button.pack(pady=10)

        self.progress = ttk.Progressbar(self, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

        self.results = []
        self.next_page_token = None

    def search(self):
        """
        Searches for videos based on the user's query.
        """
        query = self.search_entry.get()
        if query:
            self.results, self.next_page_token = search_videos(query)
            self.results_listbox.delete(0, tk.END)
            for idx, item in enumerate(self.results):
                title = item['snippet']['title']
                self.results_listbox.insert(tk.END, f"{idx + 1}. {title}")
        else:
            messagebox.showerror("Error", "Please enter a search query.")

    def more_results(self):
        """
        Fetches more search results.
        """
        query = self.search_entry.get()
        if query and self.next_page_token:
            more_results, self.next_page_token = search_videos(query, self.next_page_token)
            self.results.extend(more_results)
            for idx, item in enumerate(more_results):
                title = item['snippet']['title']
                self.results_listbox.insert(tk.END, f"{len(self.results) - len(more_results) + idx + 1}. {title}")
        else:
            messagebox.showerror("Error", "No more results available or no search query entered.")

    def preview(self):
        """
        Opens the selected video in a web browser.
        """
        selected_idx = self.results_listbox.curselection()
        if selected_idx:
            video = self.results[selected_idx[0]]
            video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
            webbrowser.open(video_url)
        else:
            messagebox.showerror("Error", "Please select a video from the search results.")

    def browse(self):
        """
        Opens a dialog for the user to select a download directory.
        """
        directory = filedialog.askdirectory()
        if directory:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, directory)

    def progress_function(self, stream, chunk, bytes_remaining):
        """
        Updates the progress bar during the download.

        Args:
            stream: The stream being downloaded.
            chunk: The current chunk of data being downloaded.
            bytes_remaining: The number of bytes remaining in the download.
        """
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = bytes_downloaded / total_size * 100
        self.progress['value'] = percentage_of_completion
        self.update_idletasks()

    def download(self):
        """
        Initiates the download of the selected video.
        """
        selected_idx = self.results_listbox.curselection()
        if selected_idx:
            video = self.results[selected_idx[0]]
            video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
            format_choice = self.format_choice.get()
            resolution_choice = self.resolution_choice.get()
            download_path = self.path_entry.get() or './downloads'
            os.makedirs(download_path, exist_ok=True)

            self.progress['value'] = 0
            threading.Thread(target=download_video, args=(video_url, download_path, format_choice, resolution_choice, self.progress_function)).start()
        else:
            messagebox.showerror("Error", "Please select a video from the search results.")

if __name__ == "__main__":
    app = TubeFetchApp()
    app.mainloop()
