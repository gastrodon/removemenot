import requests, praw, os, re, json, threading, time

with open(f"{os.path.dirname(os.path.abspath(__file__))}/config.json") as c:
    config = json.load(c)

reddit = praw.Reddit(user_agent = config["agent"],
                     client_id = config["client_id"],
                     client_secret = config["client_secret"],
                     username = config["username"],
                     password = config["password"])

print(f"{reddit.user.me()} may not be removed")

push_api = "https://api.pushshift.io/reddit"
buffer = []
buffer_lock = threading.Lock()


def get_removed(comment):
    params = {"ids": comment.id, "size": 1}

    if comment.body != "[deleted]" and comment.body != "[removed]":
        return "I think that this isn't deleted yet"

    response = requests.get(f"{push_api}/search/comment", params = params)

    if response.status_code != 200 or not response.json().get("data", False):
        return "I couldn't get the comment. Try removeddit?"

    retrieved = response.json()["data"][0]["body"].replace("\n\n", "\n\n>")
    author = response.json()["data"][0]["author"]

    if retrieved == comment.body:
        return "The comment was removed too quickly"

    return f"`{about}`:\n\n>{retrieved}\n\n[source](https://github.com/basswaver/removemenot)"


def write_buffer(item):
    buffer_lock.acquire()
    buffer.append(item)
    buffer_lock.release()


def pop_buffer():
    buffer_lock.acquire()
    val = buffer.pop()
    buffer_lock.release()
    return val


def monitor_buffer():
    global buffer

    while True:
        time.sleep(100)
        while len(buffer):
            item = pop_buffer()
            retrieved = get_removed(item.parent().parent())

            try:
                item.reply(retrieved)
                print(f"[buffer] from {item.author}")

            except praw.exceptions.APIException:
                write_buffer(item)
                print(f"[buffer] from {item.author} - buffered")
                break


def monitor_inbox():
    while True:
        time.sleep(2)
        for item in praw.models.util.stream_generator(reddit.inbox.unread):
            if not isinstance(item, praw.models.Comment):
                item.mark_read()
                continue

            if item.author.name.lower() == "removemenot":
                continue

            if not isinstance(item.parent(), praw.models.Comment):
                continue

            if not isinstance(item.parent().parent(), praw.models.Comment):
                continue

            if item.parent().parent().body != "[deleted]" and item.parent(
            ).parent().body != "[removed]":
                continue

            retrieved = get_removed(item.parent().parent())

            try:
                item.reply(retrieved)
                print(f"[inbox] from {item.author}")

            except praw.exceptions.APIException:
                write_buffer(item)
                print(f"[inbox] from {item.author} - buffered")

            item.mark_read()


def monitor_all():
    regex = "(W|w)hat did (\w)+ say"
    while True:
        time.sleep(2)
        for item in reddit.subreddit("all").stream.comments():
            if not re.search(regex, item.body):
                continue

            if item.author.name.lower() == "removemenot":
                continue

            if not isinstance(item.parent(), praw.models.Comment):
                continue

            if not isinstance(item.parent().parent(), praw.models.Comment):
                continue

            if item.parent().parent().body != "[deleted]" and item.parent(
            ).parent().body != "[removed]":
                continue

            retrieved = get_removed(item.parent().parent())

            try:
                item.reply(retrieved)
                print(f"[all] from {item.author}")

            except praw.exceptions.APIException:
                write_buffer(item)
                print(f"[all] from {item.author} - buffered")


def main():
    threads = {
        "all": threading.Thread(target = monitor_all),
        "inbox": threading.Thread(target = monitor_inbox),
        "buffer": threading.Thread(target = monitor_buffer)
    }

    for thread in threads.values():
        thread.start()


if __name__ == "__main__":
    main()
