import logging
import os
import tempfile
import subprocess
from typing import IO

logger = logging.getLogger(__name__)


def convert_mp3_ogg_opus(voice_bytes: bytes) -> IO:
    """
    Convert mp3 file to ogg with opus codec
    """
    with tempfile.NamedTemporaryFile(suffix='.mp3') as tmp_in:
        tmp_in.write(voice_bytes)
        tmp_in.seek(0)
        tmp_dir = tempfile.gettempdir()
        tmp_in_path = os.path.join(tmp_dir, tmp_in.name)
        tmp_out = tempfile.NamedTemporaryFile(suffix='.ogg')
        tmp_out_path = os.path.join(tmp_dir, tmp_out.name)
        logger.debug(f"created temp files: tmp_in_path='{tmp_in_path}', tmp_out_path='{tmp_out_path}'")
        p = subprocess.run(
            ['ffmpeg', '-hide_banner', '-loglevel', 'error',
             '-i', tmp_in_path, '-acodec', 'libopus', tmp_out_path, '-y'],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if p.returncode != 0:
            logger.error(f"Conversion failed:\n{p.stderr.decode('utf-8')}")
            raise RuntimeError('Conversion failed')
        tmp_out.seek(0)
        return tmp_out
