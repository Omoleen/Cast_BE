# import logging
# from io import BytesIO

# import numpy as np
# from moviepy.video.io.VideoFileClip import VideoFileClip
# from PIL import Image


# class ThumbnailGenerator:
#     def __init__(
#         self,
#     ):
#         self.thumbnail_width = 1280
#         self.thumbnail_height = 720

#     # file_path param is a input file path of an image or video.
#     def generate_thumbnail(self, file_path):
#         try:
#             video = VideoFileClip(file_path)
#             middle_frame = video.duration / 2
#             video_thumbnail = video.get_frame(middle_frame)
#             video_thumbnail_copy = np.copy(video_thumbnail)

#             image = Image.fromarray(video_thumbnail_copy)
#             thumbnail_width, thumbnail_height = (
#                 self.thumbnail_width,
#                 self.thumbnail_height,
#             )
#             thumbnail = image.resize((thumbnail_width, thumbnail_height))
#             thumbnail_buffer = BytesIO()
#             thumbnail.save(thumbnail_buffer, format="JPEG")
#             thumbnail_buffer.seek(0)
#             logging.info(f"Thumbnail generated for video file {file_path}")
#             video.close()
#             return thumbnail_buffer
#         except Exception as e:
#             print(f"error while generating thumbnails:{e}")
