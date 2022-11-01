# Scan a video for text
# MIT licensed – Copyright (c) 2022 Peter Cooper – @cooperx86

# Some of the code around the call to VNRecognizeTextRequest is based on
# https://github.com/RhetTbull/osxphotos/blob/master/osxphotos/text_detection.py
# itself MIT licensed and copyright (c) 2019-2021 Rhet Turnbull

import subprocess
import io
import sys
import objc
import Quartz
from Cocoa import NSURL
import Vision
from PIL import Image
import imagehash
from math import ceil, floor
import imageio.v3 as iio
from progress.bar import Bar

def get_frame_rate(filename):
    ffprobe_options = ("ffprobe","-v","0","-of", "csv=p=0", "-select_streams","v:0","-show_entries","stream=r_frame_rate", filename)
    match subprocess.check_output(ffprobe_options).strip().split(b'/'):
        case [a]:
            return float(a)
        case [a, b]:
            return float(a)/float(b)
        case _:
            raise Exception("Could not parse frame rate")

def get_video_length(filename):
    ffprobe_options = ("ffprobe","-v","0","-of", "csv=p=0", "-select_streams","v:0","-show_entries","format=duration", filename)
    out = subprocess.check_output(ffprobe_options)
    return ceil(float(out.strip()))

def detect_text_from_image_data(img_data):
    with objc.autorelease_pool():
        input_image = Quartz.CIImage.imageWithData_(img_data)
        vision_handler = Vision.VNImageRequestHandler.alloc().initWithCIImage_options_(input_image, None)
        results = []
        handler = make_request_handler(results)
        vision_request = Vision.VNRecognizeTextRequest.alloc().initWithCompletionHandler_(handler)
        vision_request.setRecognitionLevel_(0)
        error = vision_handler.performRequests_error_([vision_request], None)
        if error[1]:
            print(f"Error: {error}")
        vision_request.dealloc()
        vision_handler.dealloc()
      
    return ' '.join(results)

def make_request_handler(results):
    def handler(request, error):
        if error:
            print(f"Error: {error}")
        else:
            observations = request.results()
            for text_observation in observations:
                recognized_text = text_observation.topCandidates_(1)[0]
                results.append(recognized_text.string())
    return handler

fname = sys.argv[1]
total_frames = floor(get_frame_rate(fname) * get_video_length(fname))
words = set()
previous_hash = None

# Set up progress indication bar
bar = Bar('Processing', max=total_frames, file=sys.stderr)

i = 0
for frame in iio.imiter(fname, plugin="pyav"):
    i += 1
    bar.next()
    # Only process every 15th frame (for now)
    if i % 15 != 0:
        continue

    # Convert to PNG image  
    png_data = iio.imwrite("<bytes>", frame, extension=".png")

    # Determine image hash to prevent processing duplicate frames
    image_hash = imagehash.average_hash(Image.open(io.BytesIO(png_data)))
    if image_hash == previous_hash:
        continue
    previous_hash = image_hash

    # Detect text in image
    for word in detect_text_from_image_data(png_data).split():
        words.add(word)
  
bar.finish()

# Output the results
print(" ".join(sorted(words)))