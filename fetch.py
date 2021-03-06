# coding: utf8

import argparse

from playhouse.shortcuts import model_to_dict

from config import config


def prepare_crawler(args):
    from crawl.crawler import Crawler

    config.crawler = Crawler(args.email, args.password, Crawler.load_cookie())

    return config.crawler


def update_fetch_info(uid):
    from models import database, FetchedUser, User, Status, Gossip, Album, Photo, Blog

    with database:
        database.create_tables([FetchedUser])

        user = User.get_or_none(User.uid==uid)
        if not user:
            raise KeyError("no such user")

        fetched = model_to_dict(user)
        fetched.update(
            status = Status.select().where(Status.uid==uid).count(),
            gossip = Gossip.select().where(Gossip.uid==uid).count(),
            album = Album.select().where(Album.uid==uid).count(),
            photo = Photo.select().where(Photo.uid==uid).count(),
            blog = Blog.select().where(Blog.uid==uid).count(),
        )

        FetchedUser.insert(**fetched).on_conflict('replace').execute()

        print('update fetched info {fetched}'.format(fetched=fetched))

    return True


def fetch_user(uid, args):
    from models import database, User, Comment, Like

    fetched = False
    with database:
        database.create_tables([User, Comment, Like])

        if args.fetch_status:
            print('prepare to fetch status')
            from models import Status
            from crawl import status as crawl_status

            database.create_tables([Status])
            status_count = crawl_status.get_status(uid)
            print('fetched {status_count} status'.format(status_count=status_count))

            fetched = True

        if args.fetch_gossip:
            print('prepare to fetch gossip')
            from models import Gossip
            from crawl import gossip as crawl_gossip

            database.create_tables([Gossip])
            gossip_count = crawl_gossip.get_gossip(uid)
            print('fetched {gossip_count} gossips'.format(gossip_count=gossip_count))

            fetched = True

        if args.fetch_album:
            print('prepare to fetch albums')
            from models import Album, Photo
            from crawl import album as crawl_album

            database.create_tables([Album, Photo])
            album_count = crawl_album.get_albums(uid)
            print('fetched {album_count} albums'.format(album_count=album_count))

            fetched = True

        if args.fetch_blog:
            print('prepare to fetch blogs')
            from models import Blog
            from crawl import blog as crawl_blog

            database.create_tables([Blog])
            blog_count = crawl_blog.get_blogs(uid)
            print('fetched {blog_count} blogs'.format(blog_count=blog_count))

            fetched = True

    return fetched


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="fetch renren data to backup")
    parser.add_argument('email', help="your renren email for login")
    parser.add_argument('password', help="your renren password for login")
    parser.add_argument('-s', '--fetch-status', help="fetch status or not", action="store_true")
    parser.add_argument('-g', '--fetch-gossip', help="fetch gossip or not", action="store_true")
    parser.add_argument('-a', '--fetch-album', help="fetch album or not", action="store_true")
    parser.add_argument('-b', '--fetch-blog', help="fetch blog or not", action="store_true")
    parser.add_argument('-u', '--fetch-uid', help="user to fetch, or the login user by default", type=int)
    parser.add_argument('-r', '--refresh-count', help="refresh fetched user count", action="store_true")

    args = parser.parse_args()

    cralwer = prepare_crawler(args)

    fetch_uid = args.fetch_uid if args.fetch_uid else cralwer.uid

    fetched = fetch_user(fetch_uid, args)
    if not fetched:
        print('nothing need to fetch, just test login')

    if fetched or args.refresh_count:
        update_fetch_info(fetch_uid)
