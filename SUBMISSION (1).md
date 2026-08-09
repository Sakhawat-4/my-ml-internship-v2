# Checkpoint 1 — Build the Agent (Submission)

**Platform:** Claude (Connectors: GitHub Integration)
**Core job:** Pull FlyRank internship data from GitHub and draft a status update
**Repo:** https://github.com/Sakhawat-4/my-ml-internship-v2

---

## Deviation from FL-06 spec

FL-06 originally scoped a Gemini-based local Python script (`study_coach_agent.py`,
committed under "Design Your Personal Agent") that searches repo files by keyword
and answers questions using the Gemini API. For Checkpoint 1, I built with Claude's
built-in GitHub connector instead — no local script, no API key setup — to get a
working end-to-end run inside the time I had. This is a documented platform
deviation, not the original FL-06 plan.

---

## Tool connection

Connected Claude's **GitHub Integration** connector (Settings → Connectors →
GitHub Integration → Connect → authorized via GitHub OAuth). This is the live
tool/data connection for this checkpoint.

---

## The prompt (core job, narrowest version)

```
Look at outputs/model_report.md in my GitHub repo Sakhawat-4/my-ml-internship-v2.
Draft a status update: Task / What I did / Key result / Next step. Under 80 words.
```

## The real output

> **Task:** FlyRank Refresh Opportunity Model
> **What I did:** Trained and compared baseline rules, logistic regression, decision
> tree, and random forest on the 30k-row anonymized dataset with a client-holdout split.
> **Key result:** Random forest won — Precision@50 = 0.74 vs. 0.24 for the hand-written
> baseline rule (~3x lift), ROC AUC 0.75.
> **Next step:** Manually verify high-confidence queue rows before treating this as
> more than a reviewer aid.

(Pulled from the actual numbers in `outputs/model_report.md` — not invented.)

---

## Build log

**Attempt 1:** Connected the GitHub connector in Claude's Settings. Sent the prompt
above pointing at a specific real file (`outputs/model_report.md`) rather than
"find the most recent file" — narrowing to a known file avoided ambiguity about
which file to summarize. It read the real report and produced the draft above
correctly on the first real run, using the actual Precision@50 and ROC AUC numbers
from the file rather than invented figures.

**What I'd change next:** point the agent at multiple files (e.g. also
`work/notebooks/w07_action_playbook.ipynb`) and have it flag which weekly task the
update is for automatically, instead of me picking the file by hand.

**What I cut from the original FL-06 spec:** the local Gemini script and its
keyword-search-across-all-files approach — replaced with a single connector +
single targeted file for the MVP. Broader multi-file search is a reasonable next
iteration, not part of this checkpoint.

---

## Run capture
<video controls src="Screen Recording 2026-08-09 011344.mp4" title="Title"></video>

To get this: open Claude, same chat where GitHub shows Connected, screen-record
(Win+G), paste the exact prompt above, send it, stop recording once the draft
appears. Upload the video (YouTube unlisted / Drive / Loom) and paste the link
above this line.
