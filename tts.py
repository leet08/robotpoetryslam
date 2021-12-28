# test tts
import pyttsx3
engine = pyttsx3.init()
#engine.say("I will speak this text")
engine.save_to_file("Hello World", 'test.mp3')
engine.save_to_file("lalallala", 'test2.mp3')
engine.runAndWait()

# overlay audio
# from pydub import AudioSegment
# sound1 = AudioSegment.from_file("test.mp3", format="mp3")
# sound2 = AudioSegment.from_file("test2.mp3", format="mp3")

# # sound1 6 dB louder
# louder = sound1 + 6

# # Overlay sound2 over sound1 at position 0  (use louder instead of sound1 to use the louder version)
# overlay = sound1.overlay(sound2, position=0)


# # simple export
# file_handle = overlay.export("output.mp3", format="mp3")

# audio plus video (also overlay)
# import moviepy.editor as mpe

# # my_clip = mpe.VideoFileClip('testvid.mp4')
# # audio_background = mpe.AudioFileClip('output.mp3')
# # final_audio = mpe.CompositeAudioClip([my_clip.audio, audio_background])
# # final_clip = my_clip.set_audio(final_audio)
# # final_clip.write_videofile("output2.mp4",codec= 'mpeg4' ,audio_codec='libvorbis')

# # Generate a text clip 
# txt_clip = mpe.TextClip("GeeksforGeeks", fontsize = 75, color = 'black') 
    
# # setting position of text in the center and duration will be 10 seconds 
# txt_clip = txt_clip.set_pos('center').set_duration(10) 
    
# # Overlay the text clip on the first video clip 
# video = CompositeVideoClip([final_clip, txt_clip]) 
# video.write_videofile("output3.mp4",codec= 'mpeg4' ,audio_codec='libvorbis')

# add text
import numpy as np
import cv2

# describe the type of font
	# to be used.
font = cv2.FONT_HERSHEY_SIMPLEX

cap = cv2.VideoCapture('output2.mp4')

# save file
out = cv2.VideoWriter('output3.mp4',cv2.VideoWriter_fourcc(*'mp4v'), 20, (1280,720))

while(True):
	
	# Capture frames in the video
	ret, frame = cap.read()

	# Use putText() method for
	# inserting text on video- np array, text, text position, font, size, color, stroke, error?
	cv2.putText(frame,
				'TEXT ON VIDEO',
				(1, 5),
				font, 1,
				(0, 255, 255),
				2,
				cv2.LINE_4)

	out.write(frame)

	# Display the resulting frame
	cv2.imshow('video', frame)

	# creating 'q' as the quit
	# button for the video
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

# release the cap object
cap.release()
out.release()
# close all windows
cv2.destroyAllWindows()



