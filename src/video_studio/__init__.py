"""The video-studio engine: the scripts the social-skills video skills drive.

The skills in this repository are prose — they teach Claude how to think about
a video. This package is the other half: the programs that fetch footage,
synthesise voice, measure the result and hand it to an editor.

Nothing here renders. The Remotion composer is a separate, externally licensed
program; ``video_studio.project.studio`` and ``video_studio.project.setup``
shell out to it and report clearly when it is absent.
"""

__version__ = "0.1.0"
