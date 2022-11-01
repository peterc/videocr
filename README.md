# videocr
## Extract unique text displayed in videos on macOS

If you record a screencast, you might accidentally include credentials in it like usernames, passwords, AWS access keys, and the like.

videocr.py goes through videos and uses macOS's built-in OCR system to find all of the text in the video and return it on stdout for your perusal.

Note: This is only a rough proof of concept for now.

### USAGE

`python videocr.py in.mp4`
