import dotenv
import pytube
import whisper
import pandas as pd
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import logging
import os

class YT:
    """Download a youtube video from a given url"""
    def __init__(self, youtube_url:str = None):
        self.youtube_url = youtube_url
    
    def video_object(self) -> pytube.YouTube:
        """ Use pyTube API to return the video"""
        return pytube.YouTube(self.youtube_url)

    def download_audio_only(self):
        video = self.video_object()
        audio_stream = video.streams.get_audio_only()
        return audio_stream.download()


class Transcriber:
    """Transcribe audio to text"""
    def __init__(self, whisper_model:str = 'base', audio_file:str = None):
        self.whisper_model = whisper_model
        self.audio_file = audio_file
        self.model = self.use_whisper()

    def use_whisper(self) -> whisper.Whisper:
        """ Load the specified Whisper model. If no model is specified, the default one
        i.e. base, is loaded
        """
        return whisper.load_model(self.whisper_model)

    def transcribe_audio(self) -> str:
        """Transcribe the audio file to text"""
        return self.model.transcribe(self.audio_file)
    
    def text_to_df(self, text:str) -> pd.DataFrame:
        """Put the speach-to-text transcription in a Pandas Dataframe with timestamps"""
        return pd.DataFrame(text['segments'], columns=['start', 'end', 'text'])


class Traductor:
    """ Translate the english transcribed text from the Transcriber to other languages. 
    This uses HuggingFace to simplify the access to meta nllb model """

    def __init__(self, 
                 hf_token:str, 
                 tokenizer:str = "facebook/nllb-200-distilled-600M", 
                 model:str = "facebook/nllb-200-distilled-600M"):
        self.hf_token = hf_token
        self.tokenizer = tokenizer 
        self.model = model

    def translate(self, input:str, src_lang:str = 'eng_Latn', dest_lang:str = 'fra_Latn'):
        """Translate the input text from the source language to the destination language using the specified 
        tokenizer and model."""
        tokenizer = AutoTokenizer.from_pretrained(self.tokenizer, use_auth_token=self.hf_token, src_lang=src_lang)
        model = AutoModelForSeq2SeqLM.from_pretrained(self.model, use_auth_token=self.hf_token)

        if isinstance(input, pd.DataFrame):
            input[f'text_{dest_lang}'] = ''
            for i, t in enumerate(input.text):
                t= tokenizer(t, return_tensors="pt")
                translated_tokens = model.generate(**t, forced_bos_token_id=tokenizer.lang_code_to_id[dest_lang], max_length=300)
                result = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
                input.loc[i, f'text_{dest_lang}'] = result
        else:
            logging('only pandas dataframe format is supported for now')

        return input


if __name__ == '__main__':
    
    # Get audio of the specific video
    url = 'https://www.youtube.com/watch?v=8RJ1QGrF__c&t=57s'
    audio = YT(youtube_url=url).download_audio_only()
    
    # Transcribe
    transcriber = Transcriber(whisper_model='small' ,audio_file=audio)
    transcription = transcriber.transcribe_audio()
    df_transcription = transcriber.text_to_df(transcription)


    # Translate
    dotenv.load_dotenv()
    token = os.getenv('HF_TOKEN')
    traductor = Traductor(hf_token=token)
    traductor.translate(input = df_transcription)

    df_transcription.to_csv('df_transcription.csv')