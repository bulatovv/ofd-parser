import glob
import email
from email.message import Message
from typing import Generator
from dataclasses import dataclass


@dataclass
class HtmlContent:
    content: str

@dataclass
class PlaintextContent:
    content: str

@dataclass
class HtmlWithAltContent:
    content: HtmlContent
    alt_content: PlaintextContent


def parse_content_tree(message: Message) -> Generator[HtmlContent | PlaintextContent | HtmlWithAltContent, None, None]:
    match message.get_content_type():
        case 'multipart/mixed' | 'multipart/related':
            yield from (
                content
                for subpart in message.get_payload() if isinstance(subpart, Message)
                for content in parse_content_tree(subpart)
            )
        case 'multipart/alternative':
            first, second = message.get_payload()
            
            if first.get_content_type() == 'text/plain': # type: ignore
                first, second = second, first

            # extract first html node
            first = next(
                parse_content_tree(first) # type: ignore
            )

            yield HtmlWithAltContent(first, second) # type: ignore


        case 'text/plain':
            data = message.get_payload(decode=True)
            assert isinstance(data, bytes)
            yield PlaintextContent(data.decode(errors='ignore'))
        case 'text/html':
            data = message.get_payload(decode=True)
            assert isinstance(data, bytes)
            yield HtmlContent(data.decode(errors='ignore'))


        






# Get a list of all the .eml files in the directory
files = glob.glob('*.eml')


from email.iterators import _structure

# Loop over each .eml file
for file in files:

    # Open the .eml file
    with open(file, 'r') as f:
        message = email.message_from_file(f)
        
        _structure(message)
        
        print([type(x) for x in parse_content_tree(message)])
        
