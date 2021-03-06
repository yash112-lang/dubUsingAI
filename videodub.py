# -*- coding: utf-8 -*-
"""videoDub

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1qRDNC2JIrvfqAUkgScARYcwANIHCQ_tK
"""

import io
import os
from google.cloud import speech
from google.cloud import translate
from google.cloud import texttospeech
from google.cloud import texttospeech_v1
from google.cloud.speech_v1 import types
from pydub import AudioSegment
from google.colab import drive
import json
# from datetime import datetime
import datetime

drive.mount('/content/drive')

def convert_speech_to_text(audio):
  
    print("Start dubbing please wait ...")
    # setting up the google cloud speech API authentication
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/content/drive/My Drive/GCP/speechToText-demonstration-2260bdd544a3.json"
    try:
      # initializing the speech client
      client = speech.SpeechClient()

      # reading the audio file in read binary mode(as it is in binary form)
      with io.open(audio, "rb") as audio_file:
          content = audio_file.read()
          audio = types.RecognitionAudio(content=content) # recognizing the audio/storing the audio in a variable


      # setting up the configuration for speech to text api
      config = types.RecognitionConfig(
          encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16,
          language_code = 'en-US',
          enable_word_time_offsets = True,
          enable_automatic_punctuation = True
      )

      # storing the response from speech to text api into a variable
      response = client.recognize(config = config, audio = audio)

      return response
    except:
      client = speech.SpeechClient()
      audio = types.RecognitionAudio(uri=audio)
      config = types.RecognitionConfig(
          encoding = speech.RecognitionConfig.AudioEncoding.FLAC,
          language_code = 'en-US',
          enable_word_time_offsets = True,
          enable_automatic_punctuation = True
      )
      operation = client.long_running_recognize(config=config, audio=audio)

      print("Waiting for operation to complete...")
      response = operation.result(timeout=90)
      return response

def create_sentences(audio):
  response = convert_speech_to_text(audio)
  data = {}
  data["transcript"] = ""
  data['words'] = []
  trans = ""
  start_times = []
  end_times = []
  store = True
  for result in response.results:
    for result in response.results:
      trans += result.alternatives[0].transcript
      alternative = result.alternatives[0]
      for word_info in alternative.words:
        data['words'].append({
            'word':word_info.word,
            'start_time':str(word_info.start_time),
            'end_time': str(word_info.end_time)
        })
        data["transcript"] = trans
    response = data
    sentence = ""
    sentences = []
    for i in range(len(response["words"]) - 1):
      if(store):
        start_times.append(str(response["words"][i]["start_time"]))
      start_time = response["words"][i+1]["start_time"].split(":")
      end_time = response["words"][i]["end_time"].split(":")
      store = False
      if(start_time[2] == end_time[2]):
        sentence += response["words"][i]["word"] + " "
      else:
        end_times.append(str(response["words"][i]["end_time"]))
        sentence += response["words"][i]["word"] + " "
        sentences.append(sentence)
        sentence = ""
        store = True
    sentences.append(sentence)
    end_times.append(str(response["words"][i+1]["end_time"]))
    return sentences, start_times, end_times



os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = '/content/drive/My Drive/GCP/translationAPI.json'
translate_client = translate.Client()
def _translate(word, language_code, start_time_list, end_time_list):
    #setting up the environment for transaltion api
    print("it's about to complete please wait some more time ...")
    output = translate_client.translate(word, language_code) # Translating the word from one language to another
    _translation = {}
    _translation["words"] = []
    for i in range(len(output)):
      _translation["words"].append({
          output[i]['detectedSourceLanguage']: output[i]["input"],
          "start_time": start_time_list[i],
          "end_time": end_time_list[i],
          language_code: output[i]['translatedText']
      })
    return _translation

textToSpeechClient = texttospeech_v1.TextToSpeechClient()
def _textToSpeech(text, rate, language):
  os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = '/content/drive/My Drive/GCP/text-to-speech-practice.json'
  synthesis_input = texttospeech_v1.SynthesisInput(text=text)
  voice1 = texttospeech_v1.VoiceSelectionParams(
    language_code=language,
    ssml_gender=texttospeech_v1.SsmlVoiceGender.MALE
  )
  audio_config = texttospeech_v1.AudioConfig(
      audio_encoding=texttospeech_v1.AudioEncoding.LINEAR16,
      speaking_rate=rate
  )
  response1 = textToSpeechClient.synthesize_speech(
    input=synthesis_input,
    voice=voice1,
    audio_config=audio_config
  )
  return response1

import math
def convert_translation(sentences_list, language_code, start_time_list, end_time_list):
  translation = _translate(sentences_list, language_code, start_time_list, end_time_list)
  response2 = []
  blank_time = []
  if(len(translation["words"]) > 1):
    for i in range(len(translation["words"]) - 1):
      _blankTime = round(float((translation["words"][i+1]["start_time"].split(":"))[2]), 4) - round(float((translation["words"][i]["end_time"].split(":"))[2]), 4)
      blank_time.append(_blankTime)
  for sentence in translation["words"]:
    start_time = sentence["start_time"].split(":")
    start_time = start_time[2]
    end_time = sentence["end_time"].split(":")
    end_time = end_time[2]
    time = float(end_time) - float(start_time)
    print(time)
    rate = 0
    if(time/(float(len(sentence[language_code]))) < 0.5):
      rate = 0.70
    elif(time/(float(len(sentence[language_code]))) > 0.5 and time/(float(len(sentence[language_code]))) < 1):
      rate = 0.80
    elif(time/(float(len(sentence[language_code]))) > 1 and time/(float(len(sentence[language_code]))) < 1.5):
      rate = 1.30
    elif(time/(float(len(sentence[language_code]))) < 1.5 and time/(float(len(sentence[language_code]))) < 2):
      rate = 1.78
    else:
      rate = 1
    response2.append(_textToSpeech(sentence[language_code], rate, language_code))
  return response2, blank_time

def function_calls(audio,language_code="hi"):
  sentences_list, start_time_list, end_time_list = create_sentences(audio)
  converted_audio, blank_time = convert_translation(sentences_list, language_code, start_time_list, end_time_list)
  print("converting to audios ...")
  return converted_audio, blank_time

# if __name__ == "__main__":
def dub(audio, language):
  converted_audio, blank_time = function_calls(audio, language)
  print("reached ...")
  path = "/content/drive/My Drive/GCP/testAudio/"
  for i in range(len(converted_audio)):
    with open(f"{path}_0{i}.wav", "ab") as output1:
      output1.write(converted_audio[i].audio_content) 
  import glob
  print("converting ...")
  filenames = glob.glob(path+'*.wav')
  # open(f"{path}finalAudio.wav", "wb").close()
  final = AudioSegment.empty()
  j= 0
  print("it;s about to done ...")
  for i in filenames:
    final += AudioSegment.from_wav(i)
    if(j < len(blank_time)):
      final += AudioSegment.silent(duration=blank_time[j]*1000)
      j+=1
  final.export(f"{path}/finalAudios/finalAudio.wav", format="wav")
  print("All done")

audio = "/content/drive/My Drive/GCP/fi_.wav"

dub(audio, "ja")