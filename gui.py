import traceback
import tkinter as tk
import calendar
import datetime
from tkinter import ttk, font, filedialog
from tkinter.scrolledtext import ScrolledText
from threading import Thread
import bgg_labeler
from types import SimpleNamespace
import boardgamegeek as bgg

class ProcessManager():
    current_stage = 'downloading_collection'
    current_item = 'Azul'
    step = 23
    total = 251

    def __init__(self, pbar, label=None):
        if type(pbar) == ttk.Progressbar:
            self.tk_pbar = pbar
        if label is not None:
            self.tk_label = label

    def reset(self, total):
        self.step = 0
        self.total = 0

    def set_current_item(self, item):
        self.current_item = item
        if self.tk_label:
            self.tk_label.configure(value=item)

    def update(self, step=None):
        delta = 1
        if step:
            delta = step - self.step
            self.step = step
        else:
            self.step += 1
        if self.tk_pbar:
            self.tk_pbar.step(delta)

class BGGui(ttk.Frame):
    def error(self, error_short, error=''):
        if isinstance(error_short, Exception) and not error:
            error = traceback.format_exc()
        self.w_progressbar.pack_forget()
        self.w_force_stop.pack_forget()
        self.w_error.config(text="Error: " + str(error_short))
        if error:
            self.w_error_label.pack()
            self.w_error_long.pack()
            self.w_error_long.insert(tk.INSERT, error)
        else:
            self.w_error_label.pack_forget()
            self.w_error_long.pack_forget()

        self.error_frame.pack()
        self.w_submit.pack()

    def do_compute(self):
        try:
            bgg_labeler.run(self.args_namespace)
            self.complete()
        except Exception as e :
            self.error(e)

    def complete(self):
        self.w_progressbar.pack_forget()
        self.w_force_stop.pack_forget()
        self.w_success_label.pack()
        

    def start(self):
        self.error_frame.pack_forget()
        self.w_progressbar.pack()
        self.w_progressbar.configure(length=self.w_progressbar.master.winfo_width())
        self.w_progressbar.start()
        self.w_submit.pack_forget()
        self.w_force_stop.pack()
        self.args_namespace.username = self.username.get()
        if not self.out_file.get():
            self.error("Need a valid output filename")
            return
        self.args_namespace.out_file = self.out_file.get()
        self.args_namespace.no_pdf = self.no_pdf.get()
        self.args_namespace.no_svg_pages = self.no_svg_pages.get()
        self.args_namespace.since = self.since.get()
        self.args_namespace.cols = int(self.cols.get())
        self.args_namespace.rows = int(self.rows.get())
        if self.date_year.get() or self.date_month.get() or self.date_day.get():
            months = [calendar.month_name[i] for i in range(1, 13)]
            try:
                month_n = months.index(self.date_month.get()) + 1
                date = datetime.date(int(self.date_year.get()), 
                                     month_n, 
                                     int(self.date_day.get()))
                self.args_namespace.date = date
            except:
                self.error("Invalid date specified")
                return
            self.args_namespace.no_cache = True
        self.t1 = Thread(target=self.do_compute)
        self.t1.start()

    def ask_save_name(self):
        self.out_file.set(filedialog.asksaveasfilename())

    def __init__(self, master, args_namespace):
        super().__init__(master, padding=10)
        self.grid()

        BOLD = font.Font(weight="bold")
        ITALIC = font.Font(slant="italic") 
        
        self.since = tk.StringVar(value="")
        self.out_file = tk.StringVar(value="labels.pdf")
        self.username = tk.StringVar(value="ColbyB")
        self.no_pdf = tk.BooleanVar(value="False")
        self.no_svg_pages = tk.BooleanVar(value="False")
        self.args_namespace = args_namespace
        self.cols = tk.IntVar(value="3")
        self.rows = tk.StringVar(value="6")
            
        # self.w_title = ttk.Label(self, text="Welcome!")
        # self.w_title.pack(side='top')
        # ttk.Separator(self, orient="horizontal").pack(side='top', fill='x')
        self.toggle_frame = ttk.Frame(self, padding=10)
        self.left_frame = ttk.Frame(self)

        self.left_frame.pack(side='left')
        self.toggle_frame.pack(side='right')

        user_frame = ttk.Frame(self.left_frame)
        user_frame.pack()
        self.w_user_label = ttk.Label(user_frame, text="BGG Username")
        self.w_user_entry = ttk.Entry(user_frame, textvariable=self.username)
        filesel_frame = ttk.Frame(self.left_frame)
        self.w_out_file_label = ttk.Label(filesel_frame, text="Saving to: ").pack(side='left')
        self.w_saveas_btn = ttk.Button(
            filesel_frame, textvariable=self.out_file, command=self.ask_save_name).pack(side='right')
        filesel_frame.pack()

        self.w_submit = ttk.Button(
            self.left_frame, text="Start", command=self.start)
        self.w_force_stop = ttk.Button(
            self.left_frame, text="Force Stop")

        self.error_frame = ttk.Frame(self.left_frame)
        self.w_error = ttk.Label(
            self.error_frame, text="Error", foreground='red')
        self.w_error_label = ttk.Label(
            self.error_frame, text="More Information:")
        self.w_error_long = ScrolledText(
            self.error_frame)
        self.w_error.pack()
        self.w_error_long.pack()
        self.w_error_label.pack()

        self.w_success_label = ttk.Label(
            self.left_frame, text="Success!", foreground='green')
        self.w_progressbar = ttk.Progressbar(self.left_frame, mode="indeterminate")

        self.w_user_label.pack(side='left')
        self.w_user_entry.pack(side='right')
        self.w_submit.pack()

        w_toggle_label = ttk.Label(self.toggle_frame, text="Options", font=BOLD)

        w_toggle_label.pack(side='top')
        cols_frame = ttk.Frame(self.toggle_frame)
        self.w_cols_label = ttk.Label(cols_frame, text="Columns in the final PDF:").pack(side='left')
        self.w_cols_entry = ttk.Entry(cols_frame, textvariable=self.cols).pack(side='right')
        rows_frame = ttk.Frame(self.toggle_frame)
        self.w_rows_label = ttk.Label(rows_frame, text="Rows in the final PDF:").pack(side='left')
        self.w_rows_entry = ttk.Entry(rows_frame, textvariable=self.rows).pack(side='right')
        cols_frame.pack()
        rows_frame.pack()

        date_label = ttk.Label(self.toggle_frame, text="(Optional) Only make labels for games added after: ", padding="10px").pack()
        date_frame = ttk.Frame(self.toggle_frame)
        months = [calendar.month_name[i] for i in range(1, 13)]
        years = list(range(2000, datetime.date.today().year + 1))
        days = list(range(1,31))

        self.date_day = tk.StringVar(value="")
        self.date_month = tk.StringVar(value="")
        self.date_year = tk.StringVar(value="")
        self.w_year_combo = ttk.Combobox(date_frame, state='readonly', values=years, textvariable=self.date_year)
        self.w_month_combo = ttk.Combobox(date_frame, state='readonly', values=months, textvariable=self.date_month)
        self.w_day_combo = ttk.Combobox(date_frame, state='readonly', values=days, textvariable=self.date_day)
        self.w_month_combo.pack(side='left')
        self.w_day_combo.pack(side='left')
        self.w_year_combo.pack(side='left')
        date_frame.pack()

        w_toggle_pdf = ttk.Checkbutton(
            self.toggle_frame, text="Do not output a final PDF", variable=self.no_pdf)
        w_toggle_svg_pages = ttk.Checkbutton(
            self.toggle_frame, text="Do not output individual SVG pages", variable=self.no_svg_pages)
        w_toggle_pdf.pack(side='top', anchor='w')
        w_toggle_svg_pages.pack(side='top', anchor='w')



def main(args_namespace):
    root = tk.Tk()
    app = BGGui(root, args_namespace)
    app.mainloop()

if __name__ == "__main__":
    main()
