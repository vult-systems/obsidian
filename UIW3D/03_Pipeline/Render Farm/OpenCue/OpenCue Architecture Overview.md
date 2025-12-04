![[../../../05_Utility/Attachments/Pasted image 20251203160443.png]]

```
**Flow:**
  1. Artist submits job from Maya → Cuebot
  2. Cuebot stores job in PostgreSQL, queues frames
  3. RQD on lab machines checks in: "I'm available"
  4. Cuebot dispatches frames: "Render frames 1-10"
  5. RQD runs Maya, reports progress back
  6. Artist monitors in CueGUI
```

  **NIMBY:** When a student uses the lab machine, RQD detects keyboard/mouse activity and stops accepting new frames.