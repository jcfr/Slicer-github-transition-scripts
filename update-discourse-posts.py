#!/usr/bin/env python

import discourse
import os
import re
import subprocess
import time

from joblib import Parallel, delayed
from requests.exceptions import HTTPError

RETRY_COUNT = 3


def get_updated_post_raw(post):
    post_content = post.raw

    slicer_github_svn_dir = '/home/jcfr/Projects/SlicerGitSVNArchive'
    slicer_github_dir = '/home/jcfr/Projects/Slicer'

    RE_GITHUB_SLICER_URL = r"https://github\.com/Slicer/Slicer/commit/([\w\d]+)"
    RE_SLICER_GIT_SVN_ID = r"git-svn-id: http://svn\.slicer\.org/Slicer4/[\w\d-]+@\d+"

    matches = re.finditer(RE_GITHUB_SLICER_URL, post_content, re.MULTILINE)

    for match in matches:
        git_svn_sha = match.groups()[0]
        try:
            commit_message = subprocess.check_output(
                ['git', 'log', '--format=%B', '-n', '1', git_svn_sha],
                stderr=subprocess.STDOUT,
                cwd=slicer_github_svn_dir).decode()

            git_svn_id = re.findall(RE_SLICER_GIT_SVN_ID, commit_message)[0]

        except subprocess.CalledProcessError:
            print("%s> sha %s referenced in post %s / topic %s not found in SlicerGitSVNArchive" % (
                post.topic_id, git_svn_sha, post.id, post.topic_id))
            continue

        try:
            # Lookup sha in current Slicer source tree
            git_sha = subprocess.check_output(
                ['git', 'log', '--all', '--grep', git_svn_id, '--format=%H'],
                stderr=subprocess.STDOUT,
                cwd=slicer_github_dir).decode()
        except subprocess.CalledProcessError:
            print("%s> couldn't find git_svn_id [%s] in Slicer" % (post.topic_id, git_svn_id))
            continue

        post_content = post_content.replace(
            "https://github.com/Slicer/Slicer/commit/%s" % git_svn_sha,
            "https://github.com/Slicer/Slicer/commit/%s" % git_sha)

    if post.raw != post_content:
        return post_content
    else:
        return None


def retry_process_topics(topic_id, retry):
    seconds = pow(6, RETRY_COUNT + 1 - retry)
    print("%s> sleeping %ss" % (topic_id, seconds))
    time.sleep(seconds)
    process_topics(topic_id, retry - 1)


def process_topics(topic_id, retry=RETRY_COUNT):
    if retry == 0:
        print("%s> Skipping topic: No more retry" % (topic_id))
        return
    print("%s> Processing topic: attempt %s" % (topic_id, 3 - retry + 1))
    try:
        client = discourse.Client(
            host='https://discourse.slicer.org/',
            api_username='jcfr',
            api_key=os.environ.get('DISCOURSE_API_KEY')
        )
    except HTTPError as exc:
        if exc.response.status_code == 429:
            retry_process_topics(topic_id, retry)
            return
    try:
        topic = client.get_topic(topic_id)
    except HTTPError as exc:
        if exc.response.status_code == 429:
            retry_process_topics(topic_id, retry)
            return

        print("%s> Skipping topic: %s %s" % (topic_id, exc.response.status_code, exc.response.reason))
        return

    for topic_post in topic.post_stream['posts']:
        post_id = topic_post['id']
        try:
            post = client.get_post(post_id)
        except HTTPError as exc:
            if exc.response.status_code == 429:
                retry_process_topics(topic_id, retry)
                return
            print("%s> Skipping post %s: %s %s" % (topic_id, post_id, exc.response.status_code, exc.response.reason))
            return

        updated_raw = get_updated_post_raw(post)
        if updated_raw is not None:
            print("%s> Updating post %s: Found relevant https://github.com/Slicer/Slicer/commit/<sha> URLs" % (topic_id, post_id))
            post.update(raw=updated_raw, edit_reason="Updated SHA in https://github.com/Slicer/Slicer/commit/<sha> URLs following transition to GitHub")
        else:
            print("%s> Skipping post %s: No update" % (topic_id, post_id))


if __name__ == "__main__":

    r = Parallel(n_jobs=1, verbose=0)(
        delayed(process_topics)(topic_id) for topic_id in range(8587, 1, -1)
    )

