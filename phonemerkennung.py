import torch
import os
import os.path
import librosa
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

# Achtung: transformers läuft nicht in allen Versionen! In der Version 4.42.2 hat's
# geklappt.

# Es mussten noch die Pakete phonemizer und protobuf installiert werden,
# phonemizer setzt voraus, das espeak oder espeak-ng installiert ist.
# In der Conda-Umgebung muss dafür eine Umgebungsvariable gesetzt werden:
os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = r'C:\Program Files\eSpeak NG\libespeak-ng.dll'

# Lade das Modell
processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-xlsr-53-espeak-cv-ft")
asr_model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-xlsr-53-espeak-cv-ft")

#processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-large-xlsr-53-german")
#asr_model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-large-xlsr-53-german")


# Bilde IPA Symbole auf entsprechende SAMPA-Symbole ab; Symbole, die sowohl in IPA als auch
# SAMPA sind, werden nicht abgebildet.
ipaSampaDict = {
    'ə': '@', 'ɪ': 'I', 'ɛ': 'E', 'ɔ': 'O', 'ɾ': 'r', 'ʃ': 'S', 'ʊ': 'U',  
    'ː': ':', 'ɜ': 'E', 'ç': 'C', 'ŋ': 'N', 'ø': '2', 'ɑ': 'a', 'œ': '9', 
    'ʁ': 'R', 'æ': 'E', 'ɹ': 'r', 'ʒ': 'Z', 'ɲ': 'n', 'ð': 'v', 'ʌ': 'Q', 
    'ɐ': '6', 'ɚ':'E', 'ɕ': 'C', 'ɡ': 'g', 'θ': 'f'
}

# Funktion zur Transkription
def transcribeAudio(audioArray, sampleRate = 16000):
    inputValues = processor(audioArray, return_tensors="pt", sampling_rate = sampleRate).input_values
    logits = asr_model(inputValues).logits
    predictedIds = torch.argmax(logits, dim=-1)
    return processor.decode(predictedIds[0])


# Funktion zur Umwandlung IPA → SAMPA
# Die Funktion gibt das Transcript als Folge von Symbolen aus der Abbildungstabelle zurück
def ipaToSampa(ipaTranscript, mappingDict):
    sampaTranscript = []
    for symbol in ipaTranscript:
        if symbol in mappingDict:
            sampaTranscript.append(mappingDict[symbol])
        else:
            sampaTranscript.append(symbol)  # Zeichen bleibt, falls nicht in Mapping
        
    return "".join(sampaTranscript)


def saveTranscriptAsText (transcript, audioFileName, code):
    directory, fileName = os.path.split(audioFileName)
    baseName, _ = os.path.splitext(fileName)
    txtExtension = '.txt'
    textFileName = f'{baseName}_{code}{txtExtension}'
    with open(os.path.join(directory, textFileName), 'wt', encoding = "UTF-8") as textFile:
        textFile.write(transcript)


def saveTranscriptAsBPF (transcript, audioFileName, code, tierName):
    directory, fileName = os.path.split(audioFileName)
    baseName, _ = os.path.splitext(fileName)
    txtExtension = '.par'
    bpfFileName = f'{baseName}{code}{txtExtension}'
    with open(os.path.join(directory, bpfFileName), 'wt', encoding = "UTF-8") as bpfFile:
        # write header
        bpfFile.write(f'LHD: Partitur 1.3.1\n')
        bpfFile.write(f'SAM: 16000\n')
        bpfFile.write(f'LBD:\n')

        labelList = transcript.split(" ")
        counter = 0
        for label in labelList:
            bpfFile.write(f'{tierName}: {counter} {label}\n')
            counter += 1


if __name__ == '__main__':
    # Wurzel des zu bearbeitenden Verzeichnisbaums hier eingeben
#    rootDir = 'audio'
    #rootDir = '/Users/draxler/Documents/Phonetik/Betreuungen/Projekte/PersischesLesebuch/persischePhoneme'
    rootDir = r'C:\Users\dkl31\Desktop\001 von SC2'

    sampleRate = 16000

    for root, _, files in os.walk(rootDir):
        for wavFileName in files:
            baseName, extension = os.path.splitext(wavFileName)
            if wavFileName.endswith('.wav'):
                txtFileName = f'{baseName}.txt'

                wavFilePath = os.path.join(root, wavFileName)
                txtFilePath = os.path.join(root, txtFileName)
                
                if not os.path.exists(txtFilePath):
                    # Audio laden und Samplerate anpassen
                    audioArray, _ = librosa.load(wavFilePath, sr = sampleRate)

                    # Transkription durchführen
                    ipaTranscript = transcribeAudio(audioArray)
                    sampaTranscript = ipaToSampa(ipaTranscript, ipaSampaDict)

                 
                    saveTranscriptAsText(sampaTranscript, wavFilePath, 'sampa')
                    print(f'{sampaTranscript}\n')
                    #saveTranscriptAsBPF(ipaTranscript, wavFilePath, 'ipa', 'KAN')
                    #saveTranscriptAsBPF(sampaTranscript, wavFilePath, 'sampa', 'KAN')