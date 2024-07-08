## RS3Helper
A small helper utility for RuneScape 3 on Linux machines.  

This was mainly built for my own personal use, and is custom tailored to my use case, as Alt1 doesn't work on Linux.  

As such, there is no handling if the dependencies are missing, and this isn't meant to be downloaded and used as is. I may come back to it in the future, and make it a bit more expansive, and usable for the public.
### Preview
![RS3Helper Tkinter UI](https://cdn.discordapp.com/attachments/748033117562077187/1259247096528113735/RS3Helper.png?ex=668afcbf&is=6689ab3f&hm=e3747ae98d65383ed5f356602e3505e8627e7c6b7827c16a00ac8abf5627314b& "RS3Helper Tkinter UI")
### Current Features
- AFK Notification (Based on active window title / mouse position)
- Invention Item Level Notification
### Dependencies
#### Python
- python-vlc
- tkinter
#### Linux
- xdotool
- slop
- maim
- tesseract
- Assumes you have a tmpfs /run/user/USERID/ directory to save images in for OCR.
### How It Works
#### AFK Detection
- "xdotool" is queried to identify the currently focused window.  
- If the focused window name is not "RuneScape", then a timer variable is incremented.
- Otherwise, "xdotool" is queried to identify the current mouse position.
- If the window is focused, and the mouse hasn't moved, then the timer variable in incremented.
- Any changes will reset the timer. 
- If the timer reaches 840 (14 minutes), the alert is played.
#### Invention Item Level Detection
- A region is selected using "slop", covering the chat box (preferably with no opacity).  
- Every 10 seconds, the region is captured with "maim", and saved to the tmpfs folder "/run/user/UID/" to avoid excessive disk writes.
- This .bmp image is then fed into "tesseract-ocr", the resulting output is then fed into the python script. 
- In my case, I'm training invention with an "Augmented crystal pickaxe", so the script look for the first instance of that phrase in the tesseract output, scanning from the bottom.
- The next 70 characters are isolated, and split into a list by whitespace.
- The last list element should contain the item level, with a period, so this period is removed. 
- If the item level reaches level 12, the alert is played.