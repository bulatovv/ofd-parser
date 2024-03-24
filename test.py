import glob
import email
from email.message import Message
from typing import Generator, Callable, Iterable
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

Content = HtmlContent | PlaintextContent | HtmlWithAltContent

def parse_content_tree(message: Message) -> Generator[Content, None, None]:
    match message.get_content_type():
        case 'multipart/mixed' | 'multipart/related':
            yield from (
                content
                for subpart in message.get_payload() if isinstance(subpart, Message)
                for content in parse_content_tree(subpart)
            )
        case 'multipart/alternative':
            payload: list[Message] = message.get_payload() # type: ignore
            assert 0 < len(payload) <= 2, f"Unsupported multipart/alternative payload length: {len(payload)}"

            if len(payload) == 1:
                yield from parse_content_tree(payload[0])
            else:
                first = find_by(
                    parse_content_tree(payload[0]), lambda c: isinstance(c, HtmlContent | PlaintextContent)
                )

                if isinstance(first, HtmlContent):
                    html = first
                    plaintext = find_by(
                        parse_content_tree(payload[1]), lambda c: isinstance(c, PlaintextContent)
                    )
                else:
                    plaintext = first
                    html = find_by(
                        parse_content_tree(payload[1]), lambda c: isinstance(c, HtmlContent)
                    )

                if html and plaintext:
                    yield HtmlWithAltContent(html, plaintext)
                elif html:
                    yield html
                elif plaintext:
                    yield plaintext
        case 'text/plain':
            data = message.get_payload(decode=True)
            assert isinstance(data, bytes)
            yield PlaintextContent(data.decode(errors='ignore'))
        case 'text/html':
            data = message.get_payload(decode=True)
            assert isinstance(data, bytes)
            yield HtmlContent(data.decode(errors='ignore'))


def find_by[T](seq: Iterable[T], pred: Callable[[T], bool]) -> T | None:
    return next((item for item in seq if pred(item)), None)


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
        
