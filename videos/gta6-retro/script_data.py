# "GTA 6 on Retro Consoles (It Looks TERRIBLE)" — idea from the viral Spanish Short "El GTA VI en consola RETRO"
# (Sergio Encinas, 9.2M), remade in English with our own execution: official images converted to each console's real
# limits (resolution, palette, dithering, wobble, fog). Console years are release years (see README).
V = "af_bella"
def S(i, say, hl, con, pause=0.2): return dict(id=i, say=say, hl=set(hl), shots=[(con, None)], voice=V, speed=1.15, pause=pause)
SEGMENTS = [
    S("hook", "What if GTA six came out on retro consoles? Let's find out.", ["retro", "consoles?"], "intro"),
    S("atari", "Atari twenty-six hundred, nineteen seventy-seven. Is that Lucia, or a rectangle?", ["lucia,", "rectangle?"], "atari"),
    S("gb", "Game Boy, nineteen eighty-nine. Vice City in four shades of green.", ["four", "green."], "gameboy"),
    S("nes", "NES. Eight-bit Jason looks ready to rob a bank. With a pixel gun.", ["eight-bit", "pixel"], "nes"),
    S("ps1", "PlayStation one, nineteen ninety-four. Wobbly polygons, and the textures are melting.", ["wobbly", "melting."], "ps1"),
    S("n64", "Nintendo sixty-four. You can't see the city. There's fog everywhere.", ["fog", "everywhere."], "n64"),
    S("ps5", "And finally, PS5. Beautiful. Wait, it's still thirty frames per second?", ["beautiful.", "thirty"], "ps5"),
    S("outro", "Which retro version would you play? Comment below, and follow for more!", ["which", "comment", "follow"], "outro", pause=0.4),
]
DISPLAY = {}
TITLE = "GTA 6 on Retro Consoles (It Looks TERRIBLE) 😂 #gta6 #retro #shorts #gaming #gta"
