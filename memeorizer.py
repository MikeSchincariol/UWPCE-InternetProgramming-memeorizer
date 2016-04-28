"""
For your homework this week, you'll be creating a new WSGI application.

The MEMEORIZER acquires a phrase from one of two sources, and applies it
to one of two meme images.

The two possible sources are:

  1. A fact from http://unkno.com
  2. One of the 'Top Stories' headlines from http://www.cnn.com

For the CNN headline you can use either the current FIRST headline, or
a random headline from the list. I suggest starting by serving the FIRST
headline and then modifying it later if you want to.

The two possible meme images are:

  1. The Buzz/Woody X, X Everywhere meme
  2. The Ancient Aliens meme (eg https://memegenerator.net/instance/11837275)

To begin, you will need to collect some information. Go to the Ancient
Aliens meme linked above. Open your browser's network inspector; in Chrome
this is Ctrl-Shift-J and then click on the network tab. Try typing in some
new 'Bottom Text' and observe the network requests being made, and note
the imageID for the Ancient Aliens meme.

TODO #1:
The imageID for the Ancient Aliens meme is: 627067

You will also need a way to identify headlines on the CNN page using
BeautifulSoup. On the 'Unnecessary Knowledge Page', our fact was
wrapped like so:

```
<div id="content">
  Penguins look like they're wearing tuxedos.
</div>
```

So our facts were identified by the tag having
* name: div
* attribute name: id
* attribute value: content.

We used the following BeautifulSoup call to isolate that element:

```
element = parsed.find('div', id='content')
```

Now we have to figure out how to isolate CNN headlines. Go to cnn.com and
'inspect' one of the 'Top Stories' headlines. In Chrome, you can right
click on a headline and click 'Inspect'. If an element has a rightward
pointing arrow, then you can click on it to see its contents.

TODO #2:
Each 'Top Stories' headline is wrapped in a tag that has:
* name: span
* attribute name: class
* attribute value: cd__headline-text

NOTE: We used the `find` method to find our fact element from unkno.com.
The `find` method WILL ALSO work for finding a headline element from cnn.com,
although it will return exactly one headline element. That's enough to
complete the assignment, but if you want to isolate more than one headline
element you can use the `find_all` method instead.


TODO #3:
You will need to support the following four requests:

```
  http://localhost:8080/fact/buzz
  http://localhost:8080/fact/aliens
  http://localhost:8080/news/buzz
  http://localhost:8080/news/aliens
```

You can accomplish this by modifying the memefacter.py that we created
in class.

There are multiple ways to architect this assignment! You will probably
have to either change existing functions to take more arguments or create
entirely new functions.

I have started the assignment off by passing `path` into `process` and
breaking it apart using `strip` and `split` on lines 136, 118, and 120.

To submit your homework:

  * Fork this repository (PyWeb-04).
  * Edit this file to meet the homework requirements.
  * Your script should be runnable using `$ python memeorizer.py`
  * When the script is running, I should be able to view your
    application in my browser.
  * Commit and push your changes to your fork.
  * Submit a link to your PyWeb-04 fork repository!

"""

from bs4 import BeautifulSoup
import requests
import random

class InvalidResourcePath(Exception):
    def __init__(self, invalid_path):
        self.invalid_path = invalid_path


def create_buzz_meme(phrase):
    # Submit a request to the website that will overlay
    # the 'phrase' on an image.
    url = 'http://cdn.meme.am/Instance/Preview'
    params = {
        'imageID': 2097248,
        'text1': phrase
    }
    response = requests.get(url, params)
    return response.content

def create_alien_meme(phrase):
    # Submit a request to the website that will overlay
    # the 'phrase' on an image.
    url = 'http://cdn.meme.am/Instance/Preview'
    params = {
        'imageID': 627067,
        'text1': phrase
    }
    response = requests.get(url, params)
    return response.content


def parse_fact(body):
    # Extract the 'fact' from the HTML body.
    parsed = BeautifulSoup(body, 'html5lib')
    fact = parsed.find('div', id='content')
    return fact.text.strip()


def get_fact():
    response = requests.get('http://unkno.com')
    return parse_fact(response.text)


def parse_news(body):
    # Extract the 'news' from the HTML body.
    parsed = BeautifulSoup(body, 'html5lib')
    headline = parsed.find_all('span', class_='cd__headline-text')

    # Ok, CNN bits the big one...the site was un-parseable, at least the version
    # served up to those coming in from Canada.
    # So, in exchange for not being able to parse it, serve up phrases
    # that redirect people to other, possibly funnier, endpoints.
    val = random.random()
    if val < 0.25:
        headline = "CNN isn't really news. Try http://localhost:8080/homor/buzz"
    elif (val >= 0.25 and val < 0.5):
        headline = "CNN isn't really news. Try http://localhost:8080/homor/aliens"
    elif (val >= 0.50 and val < 0.75):
        headline = "CNN isn't really news. Try http://localhost:8080/fact/buzz"
    else:
        headline = "CNN isn't really news. Try http://localhost:8080/fact/aliens"
    return headline


def get_news():
    response = requests.get('http://www.cnn.com')
    return parse_news(response.text)


def parse_humor(body):
    # Extract the 'humor' from the HTML body.
    parsed = BeautifulSoup(body, 'html5lib')
    phrases = parsed.find_all('a', title="view quote")

    # Randomly select one and return it
    idx = random.randint(0, len(phrases))
    phrase = phrases[idx]
    return phrase.text.strip()


def get_humor():
    response = requests.get('http://www.brainyquote.com/quotes/topics/topic_funny.html')
    return parse_humor(response.text)


def process(path):
    args = path.strip("/").split("/")

    # Determine where the phrase for the meme will come from
    if args[0].lower() == "fact":
        phrase = get_fact()
    elif args[0].lower() == "news":
        phrase = get_news()
    elif args[0].lower() == "humor":
        phrase = get_humor()
    else:
        raise InvalidResourcePath("/".join(args))

    # Apply the phrase to the requested image
    if args[1].lower() == "buzz":
        meme = create_buzz_meme(phrase)
    elif args[1].lower() == "aliens":
        meme = create_alien_meme(phrase)
    else:
        raise InvalidResourcePath("/".join(args))

    return meme


def application(environ, start_response):

    try:
        path = environ.get('PATH_INFO', None)
        if path is None:
            raise NameError

        body = process(path)
        status = "200 OK"
        # If we got this far, the body will be an image that
        headers = [('Content-type', 'image/jpeg')]
    except InvalidResourcePath as ex:
        status = "404 Not Found"
        body = "<h1>The path: {} is not a valid server endpoint</h1>".format(ex.invalid_path).encode('utf8')
        headers = [('Content-type', 'text')]
    except NameError as ex:
        status = "404 Not Found"
        body = "<h1>Not Found</h1>".encode('utf8')
        headers = [('Content-type', 'text')]
    except Exception as ex:
        print(ex)
        status = "500 Internal Server Error"
        body = "<h1> Internal Server Error</h1>".encode('utf8')
        headers = [('Content-type', 'text')]
    finally:
        headers.append(('Content-length', str(len(body))))
        start_response(status, headers)
        return [body]

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    srv = make_server('localhost', 8080, application)
    srv.serve_forever()
