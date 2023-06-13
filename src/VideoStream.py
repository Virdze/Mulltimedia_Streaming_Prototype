from io import TextIOWrapper

class VideoStream:

    filename : str
    file : TextIOWrapper
    frame_num : int

    def __init__(self, filename : str, initial_frame_number : int = 0):

        self.filename = filename
        try:
            self.file = open(filename, 'rb')
        except:
            raise IOError
        self.frame_num = initial_frame_number

    def next_frame(self) -> bytes:
        """Get next frame."""
        data = self.file.read(5)  # Get the framelength from the first 5 bits
        if data:
            frame_length = int(data)

            # Read the current frame
            data = self.file.read(frame_length)
            self.frame_num += 1

        return data
