# Genera las imágenes del vídeo con IA (RealVisXL V5.0 Lightning, SDXL fotorrealista).
#   python3 images.py              -> genera las que falten
#   python3 images.py hook_eyes    -> (re)genera solo esas
import os, sys, time, torch
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("SDXL_MODEL", "/tmp/claude-0/realvis")   # o "SG161222/RealVisXL_V5.0_Lightning"
OUT = os.path.join(HERE, "ai_images"); os.makedirs(OUT, exist_ok=True)
W, H = 768, 1344            # formato vertical nativo de SDXL (≈9:16)

STYLE = ("cinematic documentary still, National Geographic photography, shot on Sony A1, 85mm lens, "
         "shallow depth of field, natural film grain, moody cinematic color grading, ultra realistic, highly detailed")
NEG = ("cartoon, illustration, painting, anime, 3d render, cgi, text, watermark, logo, letters, signature, "
       "deformed, extra legs, extra paws, mutated, disfigured, bad anatomy, blurry, lowres, oversaturated, ugly")

DOG = "a golden retriever"
PROMPTS = {
 "hook_eyes": f"extreme close-up of {DOG} staring intensely and knowingly into the camera, piercing amber eyes, dark living room, single window light, mysterious atmosphere",
 "sad_woman_dog": f"a sad young woman sitting alone on a sofa in a dim living room at dusk, {DOG} sitting on the floor watching her attentively, rain on the window, blue hour light",
 "fake_smile": "close-up portrait of a young man forcing a fake smile while his eyes look sad and tired, dim warm indoor light, emotional",
 "dog_watching_man": f"{DOG} lying on the floor, head up, looking at its owner who sits at a kitchen table with his head in his hands, evening light, the dog in sharp focus",
 "dog_tilt": f"{DOG} tilting its head curiously, looking at the camera, soft side light, dark background",
 "eye_reflection": "extreme macro photograph of a dog's brown eye, the reflection of a human silhouette visible in the glossy iris, intricate details",
 "dog_face_human": f"{DOG} looking up at a smiling woman's face, close-up from the side, warm golden light, both faces visible",
 "angry_face_dog": f"an angry frowning man shouting, seen from behind the shoulder of {DOG} who looks at him, tense moody light",
 "human_eyes": "extreme close-up of a woman's sad eyes with a tear, cinematic lighting, dark background",
 "dog_eye_macro": f"macro shot of the eye of {DOG} looking slightly to the side, detailed fur and eyelashes, dramatic rim light",
 "dog_gaze_profile": f"profile view of {DOG} gazing at the face of a woman who is looking down sadly, soft window light, intimate moment",
 "dog_ears": "close-up of a beagle with its ears perked up, listening carefully, head turned towards a sound, soft backlight",
 "dog_mri": "a calm awake dog lying still inside an MRI scanner in a modern research laboratory, wearing protective ear muffs, clinical blue light, scientific photography",
 "mri_monitor": "computer monitor in a neuroscience lab showing a colorful brain scan of a dog brain with highlighted active regions, blurred scientist in background, blue light",
 "man_phone_night": f"a tired man talking on the phone in a dark kitchen at night, worried face, {DOG} looking up at him from the floor, cinematic light from the fridge",
 "nose_macro": "extreme macro photograph of a wet black dog nose, detailed nostrils and texture, water droplets, dark background, dramatic light",
 "nose_particles": f"close-up of {DOG} sniffing the air, nose up, tiny glowing particles floating in a sunbeam, dust motes, magical realistic light",
 "dog_sniff_hand": f"close-up of {DOG} gently sniffing a person's open hand, soft natural light, shallow depth of field",
 "lab_dog_sample": "a trained dog sniffing a metal sample station in a bright scientific research laboratory, a scientist in a white coat watching, professional photography",
 "lab_samples": "glass sample jars with cotton gauze pads on a laboratory bench, scientist gloved hand holding one jar, clean clinical light, macro",
 "stress_sweat": "close-up of a stressed woman's forehead with drops of sweat, anxious expression, dark moody light",
 "mirror_smile": "a woman looking at herself in a bathroom mirror forcing a smile, her eyes sad, dim light, reflection",
 "nose_side": f"side profile close-up of {DOG}'s nose and whiskers sniffing, dark background, rim light",
 "crying_dog_approach": f"a young woman crying on a sofa covering her face with her hands, {DOG} walking towards her concerned, living room, soft evening light",
 "dog_head_knee": f"{DOG} resting its chin on the knee of a sad person sitting on the floor, looking up at them with caring eyes, warm light",
 "stranger_crying": f"a man sitting on a park bench crying, a friendly dog he doesn't know approaching him and sniffing his hand, overcast light",
 "prehistoric_fire": "prehistoric humans sitting around a campfire at night with a wolf-like dog lying beside them, firelight, starry sky, realistic historical reconstruction",
 "mutual_gaze": f"close-up profile of a woman and {DOG} looking into each other's eyes, noses almost touching, golden hour backlight, emotional",
 "hug_dog": f"a man hugging his {DOG.split()[-2]} {DOG.split()[-1]} tightly with eyes closed, emotional, warm light, close-up",
 "dog_dark_portrait": f"portrait of {DOG} looking straight into the camera, black background, Rembrandt lighting, intense and wise expression",
 "rainy_stairs": f"a sad man sitting on the front steps of a house on a rainy evening, {DOG} leaning against him, wet street, cinematic streetlight",
 "dog_lap_close": f"close-up of {DOG} with its head resting on its owner's lap, the owner's hand gently stroking its head, soft warm lamp light",
 "bed_comfort": f"{DOG} lying next to a sad woman curled up in bed, the dog's head on her arm, morning light through curtains",
 "final_look": f"{DOG} looking directly into the camera with gentle loving eyes, warm soft light, cozy home background, emotional final shot",
}

def main():
    from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
    torch.set_num_threads(os.cpu_count())
    pipe = StableDiffusionXLPipeline.from_pretrained(MODEL, torch_dtype=torch.bfloat16, variant="fp16", use_safetensors=True)
    # ajustes recomendados por RealVisXL Lightning: DPM++ SDE Karras, 5-6 pasos, CFG 1-2
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, algorithm_type="sde-dpmsolver++", use_karras_sigmas=True)
    pipe.set_progress_bar_config(disable=True)
    names = sys.argv[1:] or [k for k in PROMPTS if not os.path.exists(os.path.join(OUT, k + ".png"))]
    for i, k in enumerate(names):
        t0 = time.time()
        g = torch.Generator().manual_seed(1000 + list(PROMPTS).index(k) + int(os.environ.get("SEED_OFFSET", 0)))
        img = pipe(prompt=PROMPTS[k] + ", " + STYLE, negative_prompt=NEG, width=W, height=H,
                   num_inference_steps=int(os.environ.get("STEPS", 6)), guidance_scale=1.5, generator=g).images[0]
        img.save(os.path.join(OUT, k + ".png"))
        print(f"{k} {time.time()-t0:.0f}s ({i+1}/{len(names)})", flush=True)

if __name__ == "__main__":
    main()
