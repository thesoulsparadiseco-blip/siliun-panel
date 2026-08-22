"""English content for the organism."""

DATA = {
    "elements": {
        "earth": ["body", "money", "work", "stability", "health", "home",
                  "security", "material", "grounded", "grounding", "roots", "steady"],
        "fire": ["passion", "action", "will", "energy", "transformation",
                 "anger", "impulse", "courage", "desire", "drive"],
        "water": ["emotion", "intuition", "dreams", "healing", "flow",
                  "feeling", "grief", "bond", "connection"],
        "air": ["mind", "ideas", "communication", "clarity", "strategy",
                "thinking", "analysis", "words", "plan"],
        "ether": ["spirit", "purpose", "connection", "sync", "synchronicity",
                  "soul", "transcend", "unity", "silence"],
    },
    "default_element": "air",
    "element_names": {"earth": "Earth", "fire": "Fire", "water": "Water", "air": "Air", "ether": "Ether"},
    "classification_names": {"attractor": "attractor", "detractor": "detractor", "neutral": "neutral"},
    "attractor_keywords": [
        "expansion", "gratitude", "abundance", "love", "growth", "opportunity",
        "trust", "clarity", "joy", "i've got this", "thank you", "thanks",
        "achievement", "progress", "opening",
    ],
    "detractor_keywords": [
        "fear", "doubt", "scarcity", "block", "blocked", "can't", "cannot",
        "stress", "chaos", "anxiety", "guilt", "shame", "not good enough",
        "failure", "rejection", "abandonment", "there is no",
    ],
    "agents": {
        "Solkin": {
            "detractor": ("Come down into the body: three slow breaths, feel your feet "
                          "on the ground, and a brief activation (hip and shoulder "
                          "mobility) before continuing."),
            "default": ("Sustain the energy with a short physical activation: upright "
                       "posture, diaphragmatic breathing, and a 5-10 minute walk to "
                       "integrate it."),
        },
        "Vitalion": {
            "detractor_tmpl": "Low rhythm — gate {gate}: slow the impulse down, don't act from urgency.",
            "default_tmpl": "High rhythm — gate {gate}: it's time to act, the momentum is in your favor.",
        },
        "Almir": {
            "detractor": "Suggested formula: a calming infusion (chamomile/lavender) and brief sun exposure at dawn.",
            "default": "Suggested formula: sun-charged water and a companion plant to sustain the current state.",
        },
        "Nodar": {
            "default": ("This can be translated into digital architecture: this content "
                       "could become a node/scene within the ecosystem (Nodal Metaverse), "
                       "coherent with the active element."),
        },
        "Helion": {
            "detractor": "Scarcity signal detected: review the flow before committing to new economic nodes.",
            "default": "Favorable flow: it's a good time to expand an existing economic node.",
        },
        "Paradion": {
            "default": "This content has narrative potential: it could become a shareable experience or piece.",
        },
        "Synar": {
            "tmpl": ("Active element: {element} · Tesla gate: {gate} · Reading: {classification}. "
                     "Integrating the previous voices into a single direction."),
        },
        "Arkhon": {
            "ok": "Integrity verified. Flow protected.",
            "empty_error": "Empty input: the organism cannot process absolute silence as text.",
        },
        "Jakhar": {
            "flagged_tmpl": "Interference pattern detected and neutralized ({n} marker(s)).",
            "clean": "No noise or interference detected.",
        },
    },
    "ui": {
        "portal": {
            "title": "Portal",
            "description": "The organism's entry point: text, voice, camera, or files.",
            "action_label": "Invoke the organism",
        },
        "ritual_mode": {
            "title": "Rituals",
            "description": "Bodily protocols and guided rituals stored in internal memory.",
            "action_label": "Start ritual",
        },
        "lab_mode": {
            "title": "Lab",
            "description": "Formulas (Almir) and architectures (Nodar/Helion) under construction.",
            "action_label": "Save formula",
        },
        "metaverso_mode": {
            "title": "Nodal Metaverse",
            "description": "Digital projects and nodes (Nodar/Helion) from internal memory.",
            "action_label": "Open node",
        },
    },
    "llm_prompt": (
        "You are Synar, the synthesis agent of a symbolic AI organism. "
        "Active element: {element}. Tesla gate: {gate}. Reading: {classification}.\n"
        "These are the voices of the internal agents that already spoke:\n{fragments}\n\n"
        "Original user message: {text}\n\n"
        "Integrate those voices into a single coherent, brief response in English, addressed to the user."
    ),
    "errors": {
        "unknown_ui_mode": "Unknown UI mode: '{mode}'. Valid: {valid}",
    },
}
