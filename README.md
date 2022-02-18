# update 2021
Below still applied. Env is out of date.
Process is to query youtube videos from airtable `get_yt_links_from_airtable.py`, download them locally,process them (sound, and adding splashscreen), then reupload to youtube and 
add to the right playlist. Creates a `data.csv` file to summarized failed/success at each step. 

Defintely some progress to make in the code to get it more robust.

`pipeline.py` is still a work in progress. Was never really used yet. 
`get_yt_links_from_airtable` allow to query the video links from airtable database.
`dl_yt_video.py` download youtube videos locally to be processed.

Minor updates to others code files to make it compatible with updated flow. 


# nmc-videos

Pipeline to create videos with Neuromatch conference.

Create the right conda environment with `conda env create -f environment.yml`

`conda activate videos`

`python cut_videos.py` shows how to cut a video (with splash screen).

`python cut_airtable.py` shows how to cut a video based off of timings stored in
Airtable. 

`python update_description.py` shows how to update a video's description based 
off of airtable data.

Secret tokens should be stored in .env:

* `GOOGLE_CLIENT_ID`
* `GOOGLE_CLIENT_SECRET`
* `GOOGLE_API_KEY`
* `AT_APP_KEY_ORANGE`
* `AT_APP_KEY_GRAY`
* `AT_API_KEY`

AT are the airtable keys, Google the YouTube keys.

Only tested on Ubuntu.

