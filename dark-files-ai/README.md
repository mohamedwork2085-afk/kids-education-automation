# DARK FILES AI

A free-first GitHub Actions prototype that creates one Arabic documentary-style long video (16:9), one separate vertical teaser (9:16), Egyptian Arabic narration, scene visuals searched from Wikimedia Commons with a credits file, and FFmpeg motion on still images.

## Setup
1. Add a repository Actions secret named GEMINI_API_KEY.
2. Optional: add repository variable GEMINI_MODEL. Default: gemini-2.5-flash.
3. Open Actions -> DARK FILES AI - Daily video factory -> Run workflow.
4. Download the generated artifact from the workflow run.

The workflow is scheduled daily at 18:00 UTC (usually 20:00 in Egypt; daylight-saving changes can shift this).

## Important limitations
- Gemini generates the script, not the photos. Photos are retrieved from Wikimedia Commons; if no suitable image is found, the renderer creates a simple fallback graphic.
- Downloaded Commons images are listed in output/credits.txt. Check each file's license and attribution requirements before publishing.
- Edge TTS is a free prototype voice route, not a guarantee of permanent availability or commercial-use rights. Review Microsoft's current terms before monetizing.
- This version does not upload to YouTube. YouTube OAuth/API credentials and a separate upload-and-review step are needed.
- Generated factual scripts can contain errors. Verify story claims and source links before publishing. AI-generated bulk/repetitive videos may not qualify for platform monetization.
- No income or view count is guaranteed.
