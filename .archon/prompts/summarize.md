Emit a short receipt under 200 words, plain text, no code fences, no
leading or trailing prose. Match this structure exactly:

    Remotion video
    Mode:      <$fetch-source.output.mode>
    Subject:   <$fetch-source.output.title>
    URL:       <$fetch-source.output.url>
    Comp ID:   <composition_id from $derive-slug.output>
    Audio:     voiced=<$qa-review.output.modes.voiced> music=<..modes.music> sfx=<..modes.sfx> diagrams=<..modes.diagrams>
    Verdict:   <$qa-review.output.verdict>

    Archive:   ./videos/<archive_dirname from $derive-slug.output>/
    Source:    ./src/<composition_id>/
    Preview:   npx remotion studio
    Render:    npx remotion render <composition_id>

    QA summary:
    <one-paragraph: $qa-review.output.summary>

Context substituted:
- Source:       $fetch-source.output
- Slug JSON:    $derive-slug.output
- QA modes:     $qa-review.output.modes
- QA verdict:   $qa-review.output.verdict
- QA summary:   $qa-review.output.summary
- Archive stdout:
$archive-render.output
