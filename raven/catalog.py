"""Built-in media. Edit these lists to change what appears under "Featured".

Videos are open-licensed Blender / Google sample MP4s, played natively inside Raven.
Music is royalty-free SoundHelix demo tracks, played natively inside Raven.
"""

FEATURED_VIDEOS = [
    {"title": "Big Buck Bunny", "subtitle": "Blender Foundation",
     "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"},
    {"title": "Elephants Dream", "subtitle": "Blender Foundation",
     "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4"},
    {"title": "Sintel", "subtitle": "Blender Foundation",
     "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4"},
    {"title": "Tears of Steel", "subtitle": "Blender Foundation",
     "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4"},
    {"title": "For Bigger Fun", "subtitle": "Google sample",
     "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4"},
]

FEATURED_TRACKS = [
    {"title": f"SoundHelix Song {n}", "subtitle": "T. Schürger (royalty-free)",
     "url": f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{n}.mp3"}
    for n in range(1, 6)
]