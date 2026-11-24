"""Built-in media. Edit these lists to change what appears under "Featured".

Videos are open-licensed Blender / Google sample MP4s, played natively inside Raven.
Music is royalty-free SoundHelix demo tracks, played natively inside Raven.
"""

FEATURED_VIDEOS = [
    {"title": "Big Buck Bunny (Short)", "subtitle": "W3Schools sample",
     "url": "https://www.w3schools.com/html/mov_bbb.mp4"},
    {"title": "Flower", "subtitle": "MDN sample (CC0)",
     "url": "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"},
    {"title": "Sintel Trailer", "subtitle": "Blender Foundation",
     "url": "https://media.w3.org/2010/05/sintel/trailer.mp4"},
    {"title": "Big Buck Bunny (10s)", "subtitle": "Test Videos",
     "url": "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4"},
]

FEATURED_TRACKS = [
    {"title": f"SoundHelix Song {n}", "subtitle": "T. Schürger (royalty-free)",
     "url": f"https://www.soundhelix.com/examples/mp3/SoundHelix-Song-{n}.mp3"}
    for n in range(1, 6)
]