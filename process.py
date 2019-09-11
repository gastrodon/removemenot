import requests, praw, threading, re

buffer = []
buffer_lock = threading.Lock()


def write_buffer(item):
    buffer_lock.acquire()
    buffer.append(item)
    buffer_lock.release()


def pop_buffer():
    buffer_lock.acquire()
    val = buffer.pop()
    buffer_lock.release()
    return val


def should_handle(request, source):
    if request.author.name.lower() == "removemenot":
        return False

    if not isinstance(request.parent(), praw.models.Comment):
        return False

    if not isinstance(request.parent().parent(), praw.models.Comment):
        return False

    if not any({
            request.parent().parent().body == "[deleted]",
            request.parent().parent().body == "[removed]"
    }):
        return False

    if source == "inbox":
        request.mark_read()
        return isinstance(request, praw.models.Comment)

    if source == "all":
        regex = "(W|w)hat did (\w)+ say"
        return re.search(regex, request.body)


def handle_comment(request):
    """
    determine how to reply to a ping, in order of precedence
    """
    removed = request.parent().parent()

    if not isinstance(request.parent(), praw.models.Comment):
        return

    if not isinstance(removed, praw.models.Comment):
        return

    if any(({removed.body == "[deleted]", removed.body == "[removed]"})):
        print(f"[handled] from {request.author}                         ",
              end = "\r")
        return handle_reply(request)


def get_removed(comment):
    id = comment.id
    params = {"ids": id, "size": 1}
    push_api = "https://api.pushshift.io/reddit"
    response = requests.get(f"{push_api}/search/comment", params = params)

    if response.status_code != 200 or not response.json().get("data", False):
        return "I couldn't get the comment. Try removeddit?"

    retrieved = response.json()["data"][0]["body"].replace("\n\n", "\n\n>")
    author = response.json()["data"][0]["author"]

    if retrieved == comment.body:
        return "The comment was removed too quickly"

    return f"`{author}`:\n\n>{retrieved}\n\n[about](https://github.com/basswaver/removemenot)"


def handle_reply(request):
    try:
        removed = request.parent().parent()

        if removed.body == "[removed]":
            request.reply("The mods asked me not to tell you")
            # return handle_message(request) # TODO: this will be added, probably

        retrieved = get_removed(removed)

        return request.reply(retrieved)

    except praw.exceptions.APIException:
        write_buffer(request)
        return print(
            f"[buffered] from {request.author}                         ",
            end = "\r")

    except praw.exceptions.Forbidden:
        return print(
            f"[forbidden] from {request.author}                         ",
            end = "\r")
