# Slicer GitHub Transition Scripts

## Steps


(1) create branches

```
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
  for REFERENCE_BRANCH in master master-410 master-411 master-42 master-43 master-431 master-46 master-48; do

    BRANCH=${REFERENCE_BRANCH}-no-data

    git checkout ${BRANCH}

    rm -f /tmp/objects /tmp/candidates

    git rev-list --objects --all       | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)'       | sed -n 's/^blob //p'       | sort --numeric-sort --key=2       | cut -c 1-12,41-       | $(command -v gnumfmt || echo numfmt) --field=2 --to=iec-i --suffix=B --padding=7 --round=nearest > /tmp/objects

    cat /tmp/objects | cut -c22- | ack -iv "\.(cxx|h|json|stl|xml|tcl|py|csv|icns|png|ui|txt|in|hxx|c|txx|uu|svg|cmake|md5|rst|am|qrc|i|ini|dox|ts|log|sh|s3ext|s4ext|mat|acsv|pl|cpp|ico|mrml|patch|mcsv|gitignore|svnignore|cvsignore|css|html|directory|dic|tfm|dis|gitattributes|m|cc|m4|pkc|diff|sln|old|java|orig|ac|vcproj|ctbl|out|gif|bat|yml|cu|swp|kit|h5|curv|MF|NoDartCoverage|levels|inc\.[a-z0-9]+|supp|awk|[0-9]|s4ext-disabled|md|crt|fcsv|clp|vtp|vsprops|xmi|ctest|cfg|pipe|stop|mrml_remote|tcl_orig|ncb|suo)$" | ack -vi "(\/README|Makefile|hints|authors|news|version|pre-commit|stamp-h1|bootstrap|copying|install|notes|spec|commit-msg|doxyfile|missing|depcomp|o2|out|tmpl|vpj|Program_description|jython|CommandLineApplicationNew|getkits|randomFail|loopy|wccpp.nt|mvcpp.nt|testScript|testDemonsScript|QCleanlooksStyle|cmd2Circles|LevelSetSegmenter|UML/Annotation)^" | sort | uniq > /tmp/candidates

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
  for REFERENCE_BRANCH in master-410 master-411 master-42 master-43 master-431 master-46 master-48; do

    # BRANCH=master

    BRANCH=${REFERENCE_BRANCH}-no-data

    git checkout ${BRANCH}

    mkdir -p /tmp/Slicer4Migration-extracted-data
    rm -rf /tmp/Slicer4Migration-extracted-data/*
    rm -rf /tmp/Slicer4Migration-extracted-data-${BRANCH}
    > /tmp/GIT_MIGRATION_DATA_REMOVED.txt
    cp /tmp/candidates-${REFERENCE_BRANCH} /tmp/candidates
    git filter-branch -f --tree-filter '/home/jcfr/Projects/Slicer4MigrationSB/tree-filter-remove-data.py'
    mv /tmp/Slicer4Migration-extracted-data /tmp/Slicer4Migration-extracted-data-${BRANCH}

  done
```

(4) Consolidate git trailers, set author name and email based on "From:", update author and commiter

```
  for REFERENCE_BRANCH in master master-410 master-411 master-42 master-43 master-431 master-46 master-48; do
    BRANCH=${REFERENCE_BRANCH}-no-data
    echo ""
    git checkout ${BRANCH}

    git branch -D ${BRANCH}-trailers-consolidated || true

    cp /home/jcfr/Projects/Slicer4MigrationSB/commit-filter-script-trailers-consolidated .
    git-rocket-filter --branch ${BRANCH}-trailers-consolidated  --commit-filter-script ./commit-filter-script-trailers-consolidated
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

  BRANCH_SUFFIX=-trailers-consolidated

  BRANCH=master-411
  BRANCH=${BRANCH}-no-data${BRANCH_SUFFIX}

  # Extract SVN revision associated with branching point
  BRANCHING_SVN_REVISION=$(git rev-list --format=%B --max-parents=0 ${BRANCH} | sed -rn 's/.+(at|of) r?([0-9]+)/\2/p')
  echo "BRANCHING_SVN_REVISION: ${BRANCHING_SVN_REVISION}"

  # Extract corresponding git sha from master
  BRANCHING_SHA=$(git log --grep="@${BRANCHING_SVN_REVISION}" --pretty="%H" master-no-data${BRANCH_SUFFIX})
  echo "BRANCHING_SHA: ${BRANCHING_SHA}"

  # If commit contains "Begin post-", get the previous
  #if [[ $(git log -n1 ${BRANCHING_SHA} --pretty="%s" | ack "Begin post-") != "" ]]; then
  #  echo "${BRANCHING_SHA} contains 'Begin post-' - getting previous commit"
  #  BRANCHING_SHA=$(git rev-parse ${BRANCHING_SHA}^)
  #fi
  #echo "BRANCHING_SHA: ${BRANCHING_SHA}"

  # Branch history to rebase
  START=$(git rev-list ${BRANCH} | tail -1)
  END=$(git rev-list ${BRANCH} -n1)
  echo "${BRANCH} history to rebase from ${START} to ${END}"
  
  git rebase --onto ${BRANCHING_SHA} ${START} ${END} --committer-date-is-author-date
  git checkout -b ${BRANCH}-complete-history
  

(6) Experiment by publishing on jcfr/Slicer-Git

  # for consistency create the "-complete-history" associated with "master"
  branch=master
  git checkout -b ${branch}-no-data${BRANCH_SUFFIX}-complete-history ${branch}-no-data${BRANCH_SUFFIX}

  REMOTE=slicer-git
  git remote add ${REMOTE} git@github.com:jcfr/Slicer-Git.git
  for branch in master master-410 master-411 master-42 master-43 master-431 master-46 master-48; do
    src_branch=${branch}-no-data${BRANCH_SUFFIX}-complete-history

    if [[ ${branch} == "master-410" ]]; then
      dst_branch="master-4.10"
    elif [[ ${branch} == "master-411" ]]; then
      dst_branch="master-4.1.1"
    elif [[ ${branch} == "master-42" ]]; then
      dst_branch="master-4.2"
    elif [[ ${branch} == "master-43" ]]; then
      dst_branch="master-4.3"
    elif [[ ${branch} == "master-431" ]]; then
      dst_branch="master-4.3.1"
    elif [[ ${branch} == "master-46" ]]; then
      dst_branch="master-4.6"
    elif [[ ${branch} == "master-48" ]]; then
      dst_branch="master-4.8"
    else
      dst_branch=${branch}
    fi

    # echo "git push ${REMOTE} ${src_branch}:${dst_branch}"
    git push ${REMOTE} ${src_branch}:${dst_branch}
  done
```
