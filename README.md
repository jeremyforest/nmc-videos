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

