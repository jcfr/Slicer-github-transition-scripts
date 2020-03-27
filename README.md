# Slicer GitHub Transition Scripts

Instructions and scripts used to transition from (1) Slicer svn repository mirror onto github
into (2) a git repository only.

## Documents

* [STEPS.md](STEPS.md): Instructions for
  * removing large files from the history
  * updating commit messages (e.g consolidate git trailers, update pull-request links, set author name and email based on `From:`)
  * updating authorship
  * grafting release branches onto master
  * creating tags
  * publishing updated repository


## Scripts

* [update-discourse-posts.py](update-discourse-posts.py): Process all Slicer discourse posts updating GitHub URL of the form `https://github.com/Slicer/Slicer/<sha>` to ensure they reference a valid commit. 
