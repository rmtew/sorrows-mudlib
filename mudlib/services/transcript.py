import os

from mudlib import Service, Transcript

TRANSCRIPT_SUFFIX = ".txt"

class TranscriptService(Service):
    __sorrows__ = 'transcript'

    def Run(self):
        # Locate and verify the files existence.
        transcriptPath = os.path.join(sorrows.services.gameScriptPath, "transcripts")
        if not os.path.exists(transcriptPath):
            raise RuntimeError("Failed to locate transcript path")
        self.transcriptPath = transcriptPath

    def Load(self, transcriptName):
        transcriptFilePath = os.path.join(self.transcriptPath, transcriptName + TRANSCRIPT_SUFFIX)
        if not os.path.exists(transcriptFilePath):
            raise RuntimeError("Failed to locate transcript '%s'" % fileName)

        transcript = Transcript()
        transcript.ReadFile(transcriptFilePath)

        return transcript

    def GetTranscriptNames(self):
        l = []
        for transcriptName in os.listdir(self.transcriptPath):
            if transcriptName.endswith(TRANSCRIPT_SUFFIX):
                l.append(transcriptName[:-len(TRANSCRIPT_SUFFIX)])
        return l
