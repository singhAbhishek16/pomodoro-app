import tkinter
from tkinter import messagebox
from tkinter import PhotoImage
import datetime

# ---------------------------- CONSTANTS ------------------------------- #
PINK = "#e2979c"
RED = "#e7305b"
GREEN = "#9bdeac"
YELLOW = "#f7f5dd"
FONT_NAME = "Courier"
WORK_MIN = 1
SHORT_BREAK_MIN = 1
LONG_BREAK_MIN = 1
reps = 0
timer = None

# ---------------------------- TIMER RESET ------------------------------- # 
def reset():
    window.after_cancel(timer)
    info_text.config(text="Timer")
    canvas.itemconfig(timer_text, text="00:00")
    check_marks.config(text="")
    global reps
    reps = 0

# ---------------------------- TIMER MECHANISM ------------------------------- # 
def start_timer():
    global reps
    reps += 1

    work_sec = WORK_MIN*60
    work_short_break_sec = SHORT_BREAK_MIN*60
    work_long_break_sec = LONG_BREAK_MIN*60

    if reps==1 or reps==3 or reps==5 or reps==7:
        countdown(work_sec)
        info_text.config(text="Work")
    elif reps==8:
        countdown(work_long_break_sec)
        info_text.config(text="Break", fg=RED)
    elif reps==2 or reps==4 or reps==6:
        countdown(work_short_break_sec)
        info_text.config(text="Break", fg=PINK)

# ---------------------------- COUNTDOWN MECHANISM ------------------------------- #

def countdown(count):
    minutes, seconds = divmod(count, 60)
    if minutes < 10:
        minutes = f'0{minutes}'
    if seconds < 10:
        seconds = f'0{seconds}'
    if count > 0:
        global timer
        canvas.itemconfig(timer_text, text=f'{minutes}:{seconds}')
        timer = window.after(1000, countdown, count-1)
    elif count == 0:
        start_timer()
        marks = ""

        current_datetime = datetime.datetime.now()
        formatted_date = current_datetime.strftime("%Y-%m-%d")
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
        if reps%2 == 0:
            number_of_checkmarks = reps // 2
            for mark in range(number_of_checkmarks):
                marks += "✔"
            check_marks.config(text=marks)
            with open(f"/Users/abhishek/personal/pomodoro-tracker/tracker-{formatted_date}.txt", mode="a") as file:
                file.write(f'\n {formatted_datetime} {marks}')
        if marks == "✔✔✔✔":
            messagebox.showinfo("pomodoro pop-up", "awesome! one session completed")
            with open(f"/Users/abhishek/personal/pomodoro-tracker/tracker-{formatted_date}.txt", mode="a") as file:
                file.write(f'\n {formatted_datetime} {marks}')

# ---------------------------- UI SETUP ------------------------------- #
window = tkinter.Tk()
window.title("personal-forest")
window.config(padx=200, pady=100, bg=YELLOW)

info_text=tkinter.Label(text="Timer", fg=GREEN, bg=YELLOW, font=(FONT_NAME, 50))
info_text.grid(row=0, column=2)


canvas = tkinter.Canvas(width=200, height=224, bg=YELLOW, highlightthickness=0)
tomato_img = PhotoImage(file="tomato.png")
canvas.create_image(100, 112, image=tomato_img)
timer_text = canvas.create_text(100, 130, text="00:00", fill="white", font=(FONT_NAME, 30, "bold"))
canvas.grid(row=2, column=2)


button_start=tkinter.Button(text="Start", highlightthickness=0, command=start_timer)
button_start.grid(row=3, column=1)

button_reset=tkinter.Button(text="Reset", highlightthickness=0, command=reset)
button_reset.grid(row=3, column=3)

check_marks = tkinter.Label(fg=GREEN, bg=YELLOW)
check_marks.grid(row=4, column=2)

window.mainloop()