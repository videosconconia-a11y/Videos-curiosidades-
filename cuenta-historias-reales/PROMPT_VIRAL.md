# Prompt para crear cada vídeo nuevo (pégaselo a Claude)

> Crea un vídeo nuevo de la cuenta de historias de miedo reales sobre **[CASO]**. Sigue CLAUDE.md y este formato:
>
> 1. **Gancho (0–3 s):** la frase más inquietante del caso, sin saludos ni contexto. Patrones que funcionan:
>    "Durante X, [algo normal]… y nadie lo sabía", "Esta es la última imagen de…", "La policía encontró algo
>    que nadie ha sabido explicar".
> 2. **Contexto en 1 frase:** lugar + año + protagonista ("Japón, 2008. Un hombre de 57 años…").
> 3. **Escalada:** 3–5 detalles reales, cada uno más inquietante; frases cortas; pausa antes de la revelación.
> 4. **Revelación:** el giro, con golpe de sonido y silencio de medio segundo antes.
> 5. **Cierre:** consecuencia real (qué pasó después) + pregunta personal al espectador para comentar.
> 6. Narrador masculino, español de España, tono neutro y serio, ~2,5 palabras/segundo, 45–75 s.
> 7. Visual: guion **frase a frase** (como `videos/chico-en-las-paredes`): cada frase tiene su plano y el corte cae
>    justo cuando empieza esa frase, para que la imagen enseñe siempre lo que dice la voz; cambio de plano cada 1–4 s, estética CCTV/linterna/grano, subtítulos grandes con palabras clave en rojo,
>    sin etiquetas en pantalla (la etiqueta de IA se activa en TikTok al subir). Nunca caras reales de víctimas.
> 7b. Voz: `es-ES-AlvaroNeural` (ver `videos/el-vigilante/voice.py`), subtítulos karaoke palabra a palabra.
> 7c. Interacción: una pregunta tipo encuesta a mitad ("1 / 2 en comentarios") y cierre pidiendo teorías para la parte 2.
> 8. Verifica cada dato en 2 fuentes fiables (agencias, prensa, documentos); si un dato viral es falso, corrígelo.
> 9. Entrega `final_9x16.mp4`, `.srt`, README con fuentes y `PUBLICAR.md` (portada, descripción, hashtags,
>    comentario fijado).
