# Slicer GitHub Transition Scripts

## Steps


(0) Prerequisites

```
git clone git@github.com:jcfr/Slicer-github-transition-scripts.git

TRANSITION_SCRIPTS_DIR=$(pwd)/Slicer-github-transition-scripts

# TRANSITION_SCRIPTS_DIR=/home/jcfr/Projects/Slicer-github-transition-scripts

git clone https://github.com/Slicer/Slicer Slicer4Migration

SOURCE_DIR=$(pwd)/Slicer4Migration

# SOURCE_DIR=/home/jcfr/Projects/Slicer4Migration
```

(1) create branches

```
cd ${SOURCE_DIR}

git checkout -b master-no-data origin/master
git checkout -b master-410-no-data origin/master-410
git checkout -b master-411-no-data origin/master-411
git checkout -b master-42-no-data origin/master-42
git checkout -b master-43-no-data origin/master-43
git checkout -b master-431-no-data origin/master-431
git checkout -b master-46-no-data origin/master-46
git checkout -b master-48-no-data origin/master-48
```

(2) for each "master*-no-data" branches, list files to remove

```
  cd ${SOURCE_DIR}

  for REFERENCE_BRANCH in master master-410 master-411 master-42 master-43 master-431 master-46 master-48; do

    BRANCH=${REFERENCE_BRANCH}-no-data

    git checkout ${BRANCH}

    rm -f /tmp/objects /tmp/candidates

    git rev-list --objects --all       | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)'       | sed -n 's/^blob //p'       | sort --numeric-sort --key=2       | cut -c 1-12,41-       | $(command -v gnumfmt || echo numfmt) --field=2 --to=iec-i --suffix=B --padding=7 --round=nearest > /tmp/objects

    cat /tmp/objects | cut -c22- | ack -iv "\.(cxx|h|json|stl|xml|tcl|py|csv|icns|png|ui|txt|in|hxx|c|txx|uu|svg|cmake|md5|rst|am|qrc|i|ini|dox|ts|log|sh|s3ext|s4ext|mat|acsv|pl|cpp|ico|mrml|patch|mcsv|gitignore|svnignore|cvsignore|css|html|directory|dic|tfm|dis|gitattributes|m|cc|m4|pkc|diff|sln|old|java|orig|ac|vcproj|ctbl|out|gif|bat|yml|cu|swp|kit|h5|curv|MF|NoDartCoverage|levels|inc\.[a-z0-9]+|supp|awk|[0-9]|s4ext-disabled|md|crt|fcsv|clp|vtp|vsprops|xmi|ctest|cfg|pipe|stop|mrml_remote|tcl_orig|ncb|suo)$" | ack -vi "(\/README|Makefile|hints|authors|news|version|pre-commit|stamp-h1|bootstrap|copying|install|notes|spec|commit-msg|doxyfile|missing|depcomp|o2|out|tmpl|vpj|Program_description|jython|CommandLineApplicationNew|getkits|randomFail|loopy|wccpp.nt|mvcpp.nt|testScript|testDemonsScript|QCleanlooksStyle|cmd2Circles|LevelSetSegmenter|UML/Annotation)^" | sort | uniq > /tmp/candidates

    # Consider handpicked files
    cat ${TRANSITION_SCRIPTS_DIR}/candidates-handpicked >> /tmp/candidates

    # Then exclude file currently in master HEAD
    # This is done only for master because the remaining files are considered small enough and it was not worth
    # setting up a mechanism to download them using ExternalData or similar approach.
    git checkout master
    for line in $(cat  /tmp/candidates); do if [[ ! -f $line ]]; then echo $line; fi; done > /tmp/candidates-updated
    mv  /tmp/candidates  /tmp/candidates-orig-${REFERENCE_BRANCH}
    mv  /tmp/candidates-updated  /tmp/candidates-${REFERENCE_BRANCH}

    git checkout ${BRANCH}

  done
```

# (3) Remove files

```
  cd ${SOURCE_DIR}

  for REFERENCE_BRANCH in master-410 master-411 master-42 master-43 master-431 master-46 master-48; do

    #REFERENCE_BRANCH=master

    BRANCH=${REFERENCE_BRANCH}-no-data

    git checkout ${BRANCH}

    mkdir -p /tmp/Slicer4Migration-extracted-data
    rm -rf /tmp/Slicer4Migration-extracted-data/*
    rm -rf /tmp/Slicer4Migration-extracted-data-${BRANCH}
    > /tmp/GIT_MIGRATION_DATA_REMOVED.txt
    cp /tmp/candidates-${REFERENCE_BRANCH} /tmp/candidates
    git filter-branch -f --tree-filter "${TRANSITION_SCRIPTS_DIR}/tree-filter-remove-data.py"
    mv /tmp/Slicer4Migration-extracted-data /tmp/Slicer4Migration-extracted-data-${BRANCH}

  done
```

(4a) Consolidate git trailers, set author name and email based on "From:"

```
  cd ${SOURCE_DIR}

  for REFERENCE_BRANCH in master master-410 master-411 master-42 master-43 master-431 master-46 master-48; do
    BRANCH=${REFERENCE_BRANCH}-no-data
    echo ""
    git checkout ${BRANCH}

    git branch -D ${BRANCH}-trailers-consolidated > /dev/null 2>&1 || true

    cp ${TRANSITION_SCRIPTS_DIR}/commit-filter-script-trailers-consolidated .
    git-rocket-filter --branch ${BRANCH}-trailers-consolidated  --commit-filter-script ./commit-filter-script-trailers-consolidated
  done
```

(4b) Update authorship

```
  cd ${SOURCE_DIR}

  for REFERENCE_BRANCH in master master-410 master-411 master-42 master-43 master-431 master-46 master-48; do
    BRANCH=${REFERENCE_BRANCH}-no-data-trailers-consolidated
    echo ""
    git checkout ${BRANCH}

    git branch -D ${BRANCH}-fix-authorship > /dev/null 2>&1 || true

    cp ${TRANSITION_SCRIPTS_DIR}/commit-filter-script-fix-authorship .
    git-rocket-filter --branch ${BRANCH}-fix-authorship  --commit-filter-script ./commit-filter-script-fix-authorship
  done
```



(5) graft release branches onto master

```
  # Branching point: This is the commit from which the SVN release branch was created.

  # master # NA
  # master-410 #
  # master-411 #
  # master-42 #
  # master-43 #
  # master-431 # manually created from "master-43-no-data${BRANCH_SUFFIX}-complete-history" by resetting to SHA corresponding to 22601
  # master-46 #
  # master-48 #

  cd ${SOURCE_DIR}

  BRANCH=master-42

  BRANCH_SUFFIX=-trailers-consolidated-fix-authorship
  BRANCH=${BRANCH}-no-data${BRANCH_SUFFIX}

  # Extract SVN revision associated with branching point
  BRANCHING_SVN_REVISION=$(git rev-list --format=%B --max-parents=0 ${BRANCH} | sed -rn 's/.+(at|of) r?([0-9]+)/\2/p')
  echo "BRANCHING_SVN_REVISION: ${BRANCHING_SVN_REVISION}"

  # Extract corresponding git sha from master
  BRANCHING_SHA=$(git log --grep="@${BRANCHING_SVN_REVISION}" --pretty="%H" master-no-data${BRANCH_SUFFIX})
  echo "BRANCHING_SHA: ${BRANCHING_SHA}"

  # Branch history to rebase
  START=$(git rev-list ${BRANCH} | tail -1)
  END=$(git rev-list ${BRANCH} -n1)
  echo "${BRANCH} history to rebase from ${START} to ${END}"
  
  git rebase --onto ${BRANCHING_SHA} ${START} ${END} --committer-date-is-author-date
  git checkout -b ${BRANCH}-complete-history


(6) for consistency create the "-complete-history" associated with "master"

  cd ${SOURCE_DIR}
  BRANCH=master
  git checkout -b ${BRANCH}-no-data${BRANCH_SUFFIX}-complete-history ${BRANCH}-no-data${BRANCH_SUFFIX}


(7) Fix commmitter email/name following rebase

  #BRANCH=test
  #cp ${TRANSITION_SCRIPTS_DIR}/commit-filter-script-fix-authorship-after-rebase .
  #git-rocket-filter c1850fd482..0255dacd5d --branch ${BRANCH}-committer-fixed  --commit-filter-script ./commit-filter-script-fix-authorship-after-rebase

  MASTER_BRANCH=master-no-data-trailers-consolidated-fix-authorship-complete-history

  REFERENCE_BRANCH=master-48
  BRANCH=${REFERENCE_BRANCH}-no-data-trailers-consolidated-fix-authorship-complete-history
  BEGIN=$(git merge-base ${MASTER_BRANCH} ${BRANCH})
  END=${BRANCH}
  cp ${TRANSITION_SCRIPTS_DIR}/commit-filter-script-fix-authorship-after-rebase .
  git-rocket-filter ${BEGIN}..${END} --branch ${BRANCH}-committer-fixed  --commit-filter-script ./commit-filter-script-fix-authorship-after-rebase

  git checkout ${BRANCH}-committer-fixed
  git branch -D ${BRANCH}
  git branch -M ${BRANCH}


  REFERENCE_BRANCH=master-410
  BRANCH=${REFERENCE_BRANCH}-no-data-trailers-consolidated-fix-authorship-complete-history
  BEGIN=$(git merge-base ${MASTER_BRANCH} ${BRANCH})
  END=${BRANCH}
  cp ${TRANSITION_SCRIPTS_DIR}/commit-filter-script-fix-authorship-after-rebase .
  git-rocket-filter ${BEGIN}..${END} --branch ${BRANCH}-committer-fixed  --commit-filter-script ./commit-filter-script-fix-authorship-after-rebase

  git checkout ${BRANCH}-committer-fixed
  git branch -D ${BRANCH}
  git branch -M ${BRANCH}

(8) Publish

  cd ${SOURCE_DIR}

  # master-431

  REMOTE=slicer-git
  git remote add ${REMOTE} git@github.com:jcfr/Slicer-Git.git
  for BRANCH in master master-410 master-411 master-42 master-43 master-46 master-48; do
    src_branch=${BRANCH}-no-data${BRANCH_SUFFIX}-complete-history

    if [[ ${BRANCH} == "master-410" ]]; then
      dst_branch="master-4.10"
    elif [[ ${BRANCH} == "master-411" ]]; then
      dst_branch="master-4.1.1"
    elif [[ ${BRANCH} == "master-42" ]]; then
      dst_branch="master-4.2"
    elif [[ ${BRANCH} == "master-43" ]]; then
      dst_branch="master-4.3"
    elif [[ ${BRANCH} == "master-431" ]]; then
      dst_branch="master-4.3.1"
    elif [[ ${BRANCH} == "master-46" ]]; then
      dst_branch="master-4.6"
    elif [[ ${BRANCH} == "master-48" ]]; then
      dst_branch="master-4.8"
    else
      dst_branch=${BRANCH}
    fi

    # echo "git push ${REMOTE} ${src_branch}:${dst_branch}"
    git push ${REMOTE} ${src_branch}:${dst_branch}
  done
```

(9) Create tags

# (a) Run this in original Slicer checkout
for tag in \
  v4.0.0 \
  v4.0.1 \
  v4.1.0 \
  v4.1.1 \
  v4.10.0 \
  v4.10.1 \
  v4.10.2 \
  v4.2.0 \
  v4.2.1 \
  v4.2.2 \
  v4.3.0 \
  v4.3.1 \
  v4.4.0 \
  v4.5.0-1 \
  v4.6.0 \
  v4.6.2 \
  v4.8.0 \
  v4.8.1; do
  svn_revision=$(git show ${tag} | ack git-svn-id | sed -r "s/.+@([0-9]+).+/\1/")
  echo "${tag}:${svn_revision}"
done > /tmp/slicer-tag-and-svn-revision

# (b) Manually edit /tmp/slicer-tag-and-svn-revision to re-order tags
#     v4.10.x should be listed after v4.8.x
#
#     Manually add v4.2.2-1:21513

# (c) Run this in updated Slicer checkout (e.g jcfr/Slicer-Git)

for tag_and_svn_revision in $(cat /tmp/slicer-tag-and-svn-revision); do
  tag=$(echo ${tag_and_svn_revision} | cut -d: -f1)
  version=$(echo ${tag} | sed -r "s/^v//")
  svn_revision=$(echo ${tag_and_svn_revision} | cut -d: -f2)
  tag_hash=$(git log --all --grep="@${svn_revision} " --format=format:%H)
  echo "${version}:${tag_hash}"
  git tag -s -m "ENH: Slicer ${version}" v${version} ${tag_hash}
  git push origin v${version}
done


# (maintenance only) Only useful to delete existing tags
for tag_and_svn_revision in $(cat /tmp/slicer-tag-and-svn-revision); do
  tag=$(echo ${tag_and_svn_revision} | cut -d: -f1)
  #git push origin :${tag}
  git  tag --delete ${tag}
done


(10) Grab latest changes from master and graft them onto converted master branch (master-no-data-trailers-consolidated-fix-authorship-complete-history)

BRANCH=master-no-data-trailers-consolidated-fix-authorship-complete-history

# backup
git checkout ${BRANCH}
git checkout -b ${BRANCH}-orig

# cleanup
git branch -D ${BRANCH}-1 ${BRANCH}-2

# origin corresponds to git@github.com:Slicer/Slicer.git
git fetch origin

#
git rebase --onto ${BRANCH} e68a1a22ed 85e4859909 --committer-date-is-author-date
git branch -D ${BRANCH} && git checkout -b ${BRANCH}

# apply filtering
git-rocket-filter --branch ${BRANCH}-1  --commit-filter-script ./commit-filter-script-trailers-consolidated

git checkout ${BRANCH}-1
git-rocket-filter --branch ${BRANCH}-2  --commit-filter-script ./commit-filter-script-fix-authorship

git checkout ${BRANCH}
git reset --hard ${BRANCH}-orig

# identify first and last commit
git lg $BRANCH-2

# rebase updated commits onto current "master" branch
git rebase --onto ${BRANCH} fbb980481a c2a42c1bcd --committer-date-is-author-date
git branch -D ${BRANCH} && git checkout -b ${BRANCH}

REMOTE=slicer-git
src_branch=${BRANCH}
dst_branch=master
git push ${REMOTE} ${src_branch}:${dst_branch}

