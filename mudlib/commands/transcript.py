from mudlib import DeveloperCommand

class Transcript(DeveloperCommand):
    __verbs__ = [ 'transcript' ]

    @staticmethod
    def Run(context):
        transcriptNames = sorrows.transcript.GetTranscriptNames()

        commandArgument = context.argString.strip().lower()
        if commandArgument == "":
            context.user.Tell("<list> | [transcript name]")
            return
        elif commandArgument == "list":
            context.user.Tell("Found %d transcripts:" % len(transcriptNames))
            for transcriptName in transcriptNames:
                context.user.Tell(transcriptName)
            return

        if commandArgument not in transcriptNames:
            context.user.Tell("Unrecognised transcript: "+ commandArgument)
            return

        sorrows.transcript.Load(commandArgument)
