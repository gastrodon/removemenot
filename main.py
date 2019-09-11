import requests, praw, os, re, json, threading, time
import process

with open(f"{os.path.dirname(os.path.abspath(__file__))}/config.json") as c:
    config = json.load(c)

reddit = praw.Reddit(user_agent = config["agent"],
                     client_id = config["client_id"],
                     client_secret = config["client_secret"],
                     username = config["username"],
                     password = config["password"])

print(f"{reddit.user.me()} may not be removed")


def monitor_buffer():
    print("[monitoring] buffer")
    while True:
        while len(process.buffer):
            item = process.pop_buffer()
            threading.Thread(target = process.handle_comment,
                             args = [item]).start()


def monitor_inbox():
    print("[monitoring] inbox")
    while True:
        print(f"[inbox?]                         ", end = "\r")
        for item in praw.models.util.stream_generator(reddit.inbox.unread):
            if process.should_handle(item, "inbox"):
                threading.Thread(target = process.handle_comment,
                                 args = [item]).start()

        time.sleep(1)


def monitor_all():
    print("[monitoring] all")
    while True:
        print(f"[all?]                         ", end = "\r")
        for item in reddit.subreddit("all").stream.comments():
            if process.should_handle(item, "all"):
                threading.Thread(target = process.handle_comment,
                                 args = [item]).start()

        time.sleep(1)


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
