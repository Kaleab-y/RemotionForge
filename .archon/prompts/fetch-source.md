Parse the workflow arguments, fetch the source material, and write
two artifacts the rest of the workflow consumes.

── Arguments ──────────────────────────────────────────────────────

Raw `$ARGUMENTS` passed by the user: "$ARGUMENTS"

Format: `<mode> [url-or-prompt-text]`
  mode = `hn` | `article` | `marketing` | `idea`   (default: `hn`)
  For `hn`         : optional URL (auto-pick HN top story if omitted).
  For `article`    : URL is required.
  For `marketing`  : URL is required.
  For `idea`       : everything after the `idea` token is treated as
                     a free-form plain-English prompt — NOT a URL.
                     No fetching. The prompt IS the brief.
  `article` is a synonym for `hn` when a URL is explicitly given —
  both yield an article-style explainer video.

Parsing rules:
- Empty or whitespace-only ARGUMENTS → `mode=hn`, no URL.
- If the first whitespace-separated token is `hn` / `article` /
  `marketing` / `idea`, that is the mode. Otherwise treat the first
  token as an error (print FATAL and exit).
- For `hn` / `article` / `marketing`: the second token, if present,
  is the URL. It MUST look like `http(s)://...`. Reject anything
  else with a FATAL message. `marketing` without a URL is FATAL.
  `article` without a URL is FATAL.
- For `idea`: the rest of the line (everything after the `idea`
  token, with leading whitespace trimmed) is the prompt. It must
  be non-empty (FATAL otherwise). The prompt may contain spaces,
  URLs, or any text — pass it through verbatim. Do NOT WebFetch
  anything in idea mode.

── Steps by mode ──────────────────────────────────────────────────

1. **hn (no URL)**: WebFetch
   `https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=1`.
   Extract the top hit's `title` and `url`. If it has a URL,
   WebFetch that URL for the article body. If no URL (Ask HN post),
   use `story_text` as the body. If both are absent, use the title
   alone and note that explicitly at the top of `article-body.md`.
   `source_type` = `hn_algolia`.

2. **hn (with URL) / article**: WebFetch the given URL. Extract the
   article's title and readable body. Strip navigation, ads, cookie
   banners, footer. `source_type` = `article_url`.

3. **marketing**: WebFetch the given URL. Extract a structured brief
   suitable for a product pitch, not a wall of copy. The brief should
   capture:
   - Product / brand name (as best you can infer from the page)
   - One-sentence positioning (what it is, who it's for)
   - Value proposition — 1–3 sentences
   - 3–8 key features or capabilities (if the page lists them)
   - Primary CTA or action (e.g. "Install with npx ...", "Try it free",
     "Book a demo"). If no explicit CTA, use the domain as the CTA.
   - Tone / vibe of the site (technical / playful / enterprise / etc.)
   `source_type` = `marketing_site`.

4. **idea**: NO WebFetch. The user's prompt is the brief. Do this:
   - Generate a punchy, neutral, ≤ 60-character `title` from the
     prompt. Title-case. No quotes, no trailing punctuation. Examples:
       prompt = "vector databases vs traditional databases for ML"
         → title = "Vector Databases vs Traditional Databases"
       prompt = "explain how oauth pkce works for backend engineers"
         → title = "How OAuth PKCE Works"
   - `url` = `""` (empty string).
   - `source_type` = `user_idea`.
   - `article-body.md` content: write the user's prompt verbatim
     as the first line, then a section `## What the user wants`
     with 2–4 bullets capturing your interpretation of the topic
     scope, implied audience, and depth (e.g. "Audience: backend
     engineers familiar with HTTP", "Depth: conceptual, not a
     tutorial"). Do NOT invent specific numbers, products, or
     claims that aren't in the prompt. If the prompt is vague,
     keep the bullets vague — let `plan-video` decide angles.

── Artifacts to write ─────────────────────────────────────────────

1. `$ARTIFACTS_DIR/article.json` — exact schema:

       {
         "mode": "hn" | "article" | "marketing" | "idea",
         "title": "<string>",
         "url": "<string or empty>",
         "source_type": "hn_algolia" | "article_url" | "marketing_site" | "user_idea"
       }

   Keep it exactly these four top-level fields. Downstream nodes
   (music script, summarize, archive) read `title` and `url`.
   For `idea` mode, `url` is `""`.

2. `$ARTIFACTS_DIR/article-body.md` — plain text or markdown.
   - For hn/article: the extracted article content, cleaned up.
   - For marketing: the structured brief described above, with
     clear section headers (Product, Positioning, Value, Features,
     CTA, Tone).
   - For idea: the verbatim user prompt + a short `## What the
     user wants` interpretation as described in step 4 above.

Then emit your final message as a JSON object matching the output
schema (mode, title, url, source_type). Downstream nodes read this
via `$fetch-source.output.mode` etc.
