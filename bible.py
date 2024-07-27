import pandas as pd
import textwrap
import pyperclip
import sys
import curses
import os

def load_bible_data():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the path to the CSV file
    csv_path = os.path.join(script_dir, 'web.csv')
    
    try:
        return pd.read_csv(csv_path, quotechar='"', skipinitialspace=True)
    except FileNotFoundError:
        print(f"Error: Bible data file not found at {csv_path}")
        return None
    except Exception as e:
        print(f"Error loading CSV: {str(e)}")
        return None

def search_bible(df, query):
    if not query:
        return ""
    parts = query.split()
    if len(parts) < 1:
        return "Invalid query. Use 'help' for usage information."

    book = parts[0].title()

    if len(parts) == 1:  # Entire book
        return search_book(df, book)
    
    chapter_verse = parts[1].split(':')

    try:
        if len(chapter_verse) == 1:  # Entire chapter
            chapter = int(chapter_verse[0])
            return search_chapter(df, book, chapter)
        elif len(chapter_verse) == 2:
            chapter = int(chapter_verse[0])
            if '-' in chapter_verse[1]:  # Verse range
                start_verse, end_verse = map(int, chapter_verse[1].split('-'))
                return search_verse_range(df, book, chapter, start_verse, end_verse)
            else:  # Single verse
                verse = int(chapter_verse[1])
                return search_verse(df, book, chapter, verse)
        else:
            return "Invalid query. Use 'help' for usage information."
    except ValueError:
        return "Invalid input. Please enter valid numbers for chapter and verse."

def search_verse(df, book, chapter, verse):
    result = df[(df['Book Name'] == book) & (df['Chapter'] == chapter) & (df['Verse'] == verse)]
    if result.empty:
        return "Verse not found. Please check your input."
    else:
        return f"{book} {chapter}:{verse}\n\n{verse}: {result.iloc[0]['Text']}"

def search_verse_range(df, book, chapter, start_verse, end_verse):
    result = df[(df['Book Name'] == book) & 
                (df['Chapter'] == chapter) & 
                (df['Verse'] >= start_verse) & 
                (df['Verse'] <= end_verse)]
    if result.empty:
        return "No verses found in the specified range. Please check your input."
    else:
        verses = [f"{verse}: {text}" for verse, text in zip(result['Verse'], result['Text'])]
        return f"{book} {chapter}:{start_verse}-{end_verse}\n\n" + "\n\n".join(verses)

def search_chapter(df, book, chapter):
    result = df[(df['Book Name'] == book) & (df['Chapter'] == chapter)]
    if result.empty:
        return "Chapter not found. Please check your input."
    else:
        verses = [f"{verse}: {text}" for verse, text in zip(result['Verse'], result['Text'])]
        return f"{book} Chapter {chapter}\n\n" + "\n\n".join(verses)

def search_book(df, book):
    result = df[df['Book Name'] == book]
    if result.empty:
        return "Book not found. Please check your input."
    else:
        verses = [f"{chapter}:{verse}: {text}" for chapter, verse, text in zip(result['Chapter'], result['Verse'], result['Text'])]
        return f"{book}\n\n" + "\n\n".join(verses)

def draw_box(stdscr, h, w):
    stdscr.clear()
    if h > 2 and w > 10:  # Ensure minimum size for drawing
        stdscr.box()
        if w > 10:
            stdscr.addstr(0, 2, "tty-bible"[:w-4])
        if h > 3 and w > 45:
            stdscr.addstr(h-1, 2, "Enter: search | 'help': usage info | 'c': copy | 'q': quit"[:w-4])

def handle_resize(stdscr):
    curses.update_lines_cols()
    h, w = stdscr.getmaxyx()
    draw_box(stdscr, h, w)
    if h > 4 and w > 35:  # Only draw prompt if there's enough space
        stdscr.addstr(2, 2, "Enter search query or command:"[:w-4])
    stdscr.refresh()

def show_help():
    return """
tty-bible help:

Usage: [Book] [Chapter]:[Verse(s)]

Examples:
- Entire book: Genesis
- Single verse: Genesis 1:1
- Verse range: Exodus 20:1-17
- Entire chapter: Psalms 23

Navigation:
- Use Up and Down arrow keys to scroll through search results
- Press Enter to return to the search prompt
- Press 'c' to copy the displayed passage to clipboard
- Press 'q' to quit the current view

Commands:
- help: Show this help message
- quit: Exit the program
- color [0-6]: Change text color (0: White, 1: Red, 2: Green, 3: Yellow, 4: Blue, 5: Magenta, 6: Cyan)
- info: Display app information

Note: Type 'help' anytime for usage information
    """

def show_info():
    return """
tty-bible information:

Current version: 0.1.0
Bible translation: World English Bible

Read The Bible, without leaving your terminal!

Features:
* Works offline, and on any system
* Python-based
* Fast
* Free and open-source
    """

def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    
    # Try to initialize colors, but have a fallback if it fails
    try:
        curses.start_color()
        curses.use_default_colors()
        for i in range(0, 7):
            curses.init_pair(i, i, -1)
        has_colors = True
    except curses.error:
        has_colors = False
    
    df = load_bible_data()
    if df is None:
        stdscr.addstr(0, 0, "Error: Bible data file not found or couldn't be read.")
        stdscr.addstr(1, 0, "Press any key to exit...")
        stdscr.getch()
        return

    text_color = 0 # white

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        draw_box(stdscr, h, w)

        stdscr.addstr(2, 2, "Enter search query or command:")
        stdscr.refresh()
        curses.echo()
        query = stdscr.getstr(2, 35, 50).decode('utf-8').strip().lower()
        curses.noecho()

        if query == 'quit':
            break
        elif query == 'help':
            result = show_help()
        elif query == 'info':
            result = show_info()
        elif query.startswith('color '):
            if has_colors:
                try:
                    color = int(query.split()[1])
                    if 0 <= color <= 6:
                        text_color = color
                        result = f"Text color changed to {['White', 'Red', 'Green', 'Yellow', 'Blue', 'Magenta', 'Cyan'][color]}"
                    else:
                        result = "Invalid color. Choose a number between 0 and 6."
                except (IndexError, ValueError):
                    result = "Invalid color command. Use 'color [0-6]'."
            else:
                result = "Colors are not available on this terminal."
        else:
            result = search_bible(df, query)

        action = display_result(stdscr, result, text_color, has_colors)
        if action == 'quit':
            break

def display_result(stdscr, result, text_color, has_colors):
    h, w = stdscr.getmaxyx()
    wrapped_lines = []
    for line in result.split('\n'):
        wrapped_lines.extend(textwrap.wrap(line, w-4) or [''])

    pad = curses.newpad(len(wrapped_lines) + h, w)
    for i, line in enumerate(wrapped_lines):
        if has_colors:
            pad.addstr(i, 0, line, curses.color_pair(text_color if result != show_help() else 1))
        else:
            pad.addstr(i, 0, line)

    stdscr.clear()
    draw_box(stdscr, h, w)
    stdscr.refresh()

    top_line = 0
    while True:
        pad.refresh(top_line, 0, 2, 2, h-3, w-3)
        key = stdscr.getch()
        if key == ord('\n'):
            break
        elif key == ord('q'):
            return 'quit'
        elif key == ord('c'):
            pyperclip.copy(result)
            stdscr.addstr(h-1, w-20, "Copied to clipboard")
            stdscr.refresh()
        elif key == curses.KEY_DOWN:
            top_line = min(top_line + 1, len(wrapped_lines) - (h-4))
        elif key == curses.KEY_UP:
            top_line = max(top_line - 1, 0)
        elif key == curses.KEY_RESIZE:
            handle_resize(stdscr)
            h, w = stdscr.getmaxyx()
            stdscr.clear()
            draw_box(stdscr, h, w)
            stdscr.refresh()
    return None

if __name__ == "__main__":
    curses.wrapper(main)