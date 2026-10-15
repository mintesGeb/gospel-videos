# Daily posting runbook — "Trust Jesus and Be Saved"

Run once per day (morning, US Eastern). Goal: keep TikTok, the Facebook Page Story and the
Instagram Story queues in Buffer topped up from `schedule.json`, and make new videos when
the plan runs low.

## Accounts (Buffer via Zapier, action `buffer_add_to_queue`, selected_api `BufferCLIAPI`)
- organizationId: `6acd442c7a96a70f48c4a848`
- TikTok (rastesolympiad): channelId `6acd4459778b240e2fec5896`
  - attachment `video`, method `schedule`, text = `caption`,
    dynamic_properties `{video, scheduling_type: "direct", scheduled_at}`
- Facebook Page (Trust Jesus and Be Saved): channelId `6ace5ea2778b240e2ff9a4a0`
  - attachment `video`, method `schedule`, text = `story_text`,
    dynamic_properties `{fb_post_type: "facebook_story", video, scheduled_at}`
- Instagram (gosple_daily): channelId `6ace5e5c778b240e2ff9a224`
  - attachment `video`, method `schedule`, text = `story_text`,
    dynamic_properties `{ig_post_type: "story", video, scheduling_type: "direct", scheduled_at}`
- Facebook Page REEL (same channel `6ace5ea2778b240e2ff9a4a0`): text = `reel_caption`,
    dynamic_properties `{fb_post_type: "facebook_reel", video, scheduled_at}`
- Instagram REEL (same channel `6ace5e5c778b240e2ff9a224`): text = `reel_caption`,
    dynamic_properties `{ig_post_type: "reels", ig_share_to_feed: "true", video, scheduling_type: "direct", scheduled_at}`
- Posting pattern (Zapier budget, MG Oct 14): TikTok at all 4 slots; Facebook + Instagram REELS at all
  4 slots (8am, 12pm, 4pm, 8pm); Facebook + Instagram STORY only at 8pm (the 8pm post goes out as both a reel and a story). In `schedule.json` a flag is false (to do),
  true (done) or null (skip this channel for this post).
- `video` = `https://raw.githubusercontent.com/mintesGeb/gospel-videos/main/<file>` (repo must be public).

Buffer free plan: max 10 scheduled posts per channel. Only schedule posts whose `time` is
in the future and within the next ~48 hours. If Buffer answers "10 scheduled post limit",
stop for that channel and carry on — the next run will catch up.

## Zapier budget
Each successful Zapier action costs 2 tasks from a shared allowance. Retry a failed Zapier call at
most once. Never make test calls. If Zapier reports the task limit is reached, stop and report it at
the top instead of retrying.

## Steps
1. In `schedule.json`, for each post with a future `time` within 48h, schedule every channel
   whose flag (`tiktok`, `facebook_story`, `instagram_story`, `facebook_reel`, `instagram_reel`) is false; set the flag true on
   success. Never schedule a post twice. Skip posts whose `time` has passed (leave flag false).
2. NEVER delete video files from `videos/` (MG Oct 15: keep every video for future reuse).
   Commit and push `schedule.json`.
3. If fewer than 8 future posts remain in `schedule.json`, make a new week (28 videos):
   - Bible translation: NIV while `niv_verses_used.json` lists fewer than 470 verses
     (NIV allows up to 500 verses without written permission; each quote is labeled "(NIV)" —
     set `version: "NIV"` in each spec and the renderer adds the label). Add every new verse to
     `niv_verses_used.json` (shared with the "Trust Jesus Page Posts" task, so `git pull --rebase`
     before editing and pushing it). When the list reaches 470, switch to the Berean Standard Bible
     (public domain, `version: "BSB"`) and tell the user in the report.
   - Pick 28 new verses on salvation/God's love, not used in any `used_verses_*.json`.
     Quote the text EXACTLY: verify each verse with WebFetch on biblehub.com (e.g.
     https://biblehub.com/niv/john/3.htm) by asking "does verse X read exactly: ...? YES/NO".
     For display only: drop a trailing comma/semicolon/dash (end with a period), capitalize the
     first letter, and balance any unmatched quotation mark. Write each spec as in
     `used_verses_week1.json` (file, ref, verse, close, sub, palette, hook). `hook` is a short
     scroll-stopping line (max ~6 words) shown on the first frame, e.g. "Tired? Read this." and save as
     `used_verses_weekN.json`.
   - Render silent videos: `python3 tools/render_videos.py <specs.json> <out_dir>` (needs
     ffmpeg, numpy, Pillow, DejaVu fonts). Check one frame of the longest verse visually.
   - Music: tracks live in the PRIVATE repo `mintesGeb/gospel-assets` under `music/` (attach it
     with add_repo owner "mintesGeb", repo "gospel-assets", access "read", then clone it).
     Do not copy the mp3s into this public repo. `sh tools/add_music.sh <silent> <final> <music_dir>`.
     If that repo is unavailable, stop and tell the user instead of posting silent videos.
   - Copy finals to `videos/`, append posts to `schedule.json` (with `reel_caption` = caption plus a line "Send this to someone who needs it." before the hashtags, no #fyp; reel flags false at all 4 slots; story flags false at 8pm and null at 8am/12pm/4pm) continuing the 8am/12pm/4pm/8pm
     Eastern slots after the last existing post, flags false. Commit and push.
4. Report briefly: what was scheduled per channel, any errors, how many posts remain.

Note: times are US Eastern. Use offset -04:00 until Nov 1 2026, then -05:00 (standard time) until DST resumes in March.
