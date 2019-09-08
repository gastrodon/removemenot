import requests, praw, os, re, json, threading

with open(f"{os.path.dirname(os.path.abspath(__file__))}/config.json") as c:
    config = json.load(c)

reddit = praw.Reddit(user_agent = config["agent"],
                     client_id = config["client_id"],
                     client_secret = config["client_secret"],
                     username = config["username"],
                     password = config["password"])

print(f"{reddit.user.me()} may not be removed")

push_api = "https://api.pushshift.io/reddit"


def get_removed(comment):
    params = {"ids": comment.id, "size": 1}

    if comment.body != "[deleted]" and comment.body != "[removed]":
        return "I think that this isn't deleted yet"

    response = requests.get(f"{push_api}/search/comment", params = params)

    if response.status_code != 200 or not response.json().get("data", False):
        return "I couldn't get the comment. Try removeddit?"

    retrieved = response.json()["data"][0]["body"]
    author = response.json()["data"][0]["author"]

    if retrieved == comment.body:
        return "The comment was removed too quickly"

    return f"`{author}`:\n\n>{retrieved}"


def monitor_inbox():
    while True:
        for item in praw.models.util.stream_generator(reddit.inbox.unread):
            if not isinstance(item, praw.models.Comment):
                item.mark_read()
                continue

            if not isinstance(item.parent(), praw.models.Comment):
                continue

            if not isinstance(item.parent().parent(), praw.models.Comment):
                continue

            retrieved = get_removed(item.parent().parent())

            item.reply(retrieved)
            print(f"[inbox] from {item.body}")

            item.mark_read()


def monitor_all():
    regex = "(W|w)hat did (\w)+ say"
    while True:
        for item in reddit.subreddit("all").stream.comments():
            if not re.search(regex, item.body):
                continue

            if not isinstance(item.parent(), praw.models.Comment):
                continue

            if not isinstance(item.parent().parent(), praw.models.Comment):
                continue

            retrieved = get_removed(item.parent().parent())

            item.reply(retrieved)
            print(f"[all] from {item.body}")


def main():
    threads = {
        "all": threading.Thread(target = monitor_all),
        "inbox": threading.Thread(target = monitor_inbox)
    }

    for thread in threads.values():
        thread.start()


if __name__ == "__main__":
    main()
