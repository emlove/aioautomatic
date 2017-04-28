"""SocketIO helper functions.

From https://github.com/invisibleroads/socketIO-client/
"""

ATTR_SESSION_ID = 'sid'
ATTR_PING_TIMEOUT = 'pingTimeout'
ATTR_PING_INTERVAL = 'pingInterval'
ATTR_PING_TIMEOUT_HANDLE = 'pingTimeoutHandle'
ATTR_PING_INTERVAL_HANDLE = 'pingIntervalHandle'


# pylint: disable=invalid-name
def decode_engineIO_content(content):
    """Method from socketIO-client."""
    content_index = 0
    content_length = len(content)
    while content_index < content_length:
        try:
            content_index, packet_length = _read_packet_length(
                content, content_index)
        except IndexError:
            break
        content_index, packet_text = _read_packet_text(
            content, content_index, packet_length)
        engineIO_packet_type, engineIO_packet_data = parse_packet_text(
            packet_text)
        yield engineIO_packet_type, engineIO_packet_data


def parse_packet_text(packet_text):
    """Method from socketIO-client."""
    packet_type = int(get_character(packet_text, 0))
    packet_data = packet_text[1:]
    return packet_type, packet_data


def _read_packet_length(content, content_index):
    """Method from socketIO-client."""
    while get_byte(content, content_index) != 0:
        content_index += 1
    content_index += 1
    packet_length_string = ''
    byte = get_byte(content, content_index)
    while byte != 255:
        packet_length_string += str(byte)
        content_index += 1
        byte = get_byte(content, content_index)
    return content_index, int(packet_length_string)


def _read_packet_text(content, content_index, packet_length):
    """Method from socketIO-client."""
    while get_byte(content, content_index) == 255:
        content_index += 1
    packet_text = content[content_index:content_index + packet_length]
    return content_index + packet_length, packet_text


def get_byte(content, index):
    """Method from socketIO-client."""
    return content[index]


def get_character(content, index):
    """Method from socketIO-client."""
    return chr(get_byte(content, index))
