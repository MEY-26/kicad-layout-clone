# Documentation screenshots

Use a real application-window capture or a user-provided screenshot. Do not use
`wx.ClientDC` / `MemoryDC.Blit`: they can omit native controls and backgrounds on
Windows while producing a valid but mostly transparent PNG. Adding an opaque
background later does not restore the missing content.

Keep the original opaque PNG and use a new versioned filename when replacing a
published screenshot. Update both repository README image references. An English
UI screenshot may be shared by both READMEs; label its language correctly.

Before export/publication:

1. Validate with `python tools/check_doc_images.py` in the public repository.
   The check rejects transparency, damaged PNGs, unreadably small images and
   overwhelmingly blank captures. CI runs the same check on every push.
2. Open both rendered GitHub READMEs and inspect the image against the page
   background. Check text, buttons and backgrounds; a successful image load alone
   does not prove the capture is correct.
3. Keep private board files, personal paths and credentials out of screenshots.

The current `layout-clone-0.3.4-footprint-edits-en.png` was supplied by the user on
16 October 2026. It is a 1306 x 953 fully opaque PNG, used without pixel edits.
